import numpy as np
import sounddevice as sd
import __main__

BLOCK_SIZE = 1024
SAMPLERATE = 48000

class daw_object:
    def __init__(self):
        pass

    def save(self, name="save.daw"):
        with open(name, "w") as f:
            f.write(repr(self))

def load(name="save.daw", where=__main__.__dict__):
    with open(name, "r") as f:
        file = f.read()
    exec(file, where)

class funk(daw_object):
    def __init__(self, f, repr=None):
        if callable(f):
            self.f = f
            self.repr = f.__repr__()
        elif type(f) == str:
            self.f = eval("lambda t: " + f)
            self.repr = f
        else:
            self.f = lambda t: f
            self.repr = str(f)
        if repr:
            self.repr = repr

    def __repr__(self):
        return self.repr

    def __call__(self, t):
        return self.f(t)
    
    def __add__(self, other):
        if isinstance(other, funk):
            return funk(lambda t: self.f(t) + other.f(t),
                        repr=f"{self.repr} + {other.repr}")
        return funk(lambda t: self.f(t) + other,
                    repr=f"{self.repr} + {other}")

    def __sub__(self, other):
        if isinstance(other, funk):
            return funk(lambda t: self.f(t) - other(t),
                        repr=f"{self.repr} - {other.repr}")
        return funk(lambda t: self.f(t) - other,
                    repr=f"{self.repr} - {other}")

    def __neg__(self):
        return funk(lambda t: -self.f(t),
                    repr=f"(-{self.repr})")

    def __mul__(self, other):
        if isinstance(other, funk):
            return funk(lambda t: self.f(t) * other.f(t),
                         repr=f"{self.repr} * {other.repr}")
        return funk(lambda t: self.f(t) * other,
                    repr=f"{self.repr} * {other}")
    
    def __rmul__(self, other):
        return funk(lambda t: other * self.f(t),
                    repr=f"{other} * {self.repr}")

    def __truediv__(self, other):
        if isinstance(other, funk):
            return funk(lambda t: self.f(t) / other.f(t),
                         repr=f"{self.repr}/{other.repr}")
        return funk(lambda t: self.f(t) / other,
                    repr=f"{self.repr}/{other}")

    def __pow__(self, other):
        if isinstance(other, funk):
            return funk(lambda t: self.f(t) ** other.f(t),
                         repr=f"{self.repr}**({other.repr})")
        return funk(lambda t: self.f(t) ** other,
                    repr=f"{self.repr}**{other}")

class player(funk):
    def __init__(self):
        self.inputs = []
        self.t = 0.0
        self.block = np.linspace(0, BLOCK_SIZE / SAMPLERATE, 
                                 BLOCK_SIZE)
        self.os = sd.OutputStream(samplerate=SAMPLERATE, 
                                  blocksize=BLOCK_SIZE,
                                  channels=1, 
                                  dtype='int16', 
                                  callback=self.tick)

    def __call__(self, t):
        return np.sum([f(t) for f in self.inputs], axis=0)

    def tick(self, outdata, frames, time, status):
        t_eval = self.t + self.block
        signal = np.sum([f(t_eval) for f in self.inputs], axis=0)
        signal = np.clip(signal, -1, 1)
        signal = np.int16(signal * 32767)
        outdata[:, 0] = signal
        self.t += BLOCK_SIZE / SAMPLERATE

    def plug(self, other):
        if isinstance(other, funk):
            self.inputs.append(other)
        elif hasattr(other, '__iter__'):
            for f in other:
                if isinstance(f, funk):
                    self.inputs.append(f)
                else:
                    print("⚡")
                    break
        else:
            print("⚡")
    
    def __lt__(self, other):
        self.plug(other)

    def __gt__(self, other):
        return self.unplug(other)

    def __repr__(self):
        name_of_global = {o: n for n, o in __main__.__dict__.items() 
                          if isinstance(o, daw_object)}
        name_of_self = name_of_global.pop(self)
        representations = [f"{name_of_global[f]}"
                           if f in name_of_global
                           else f.__repr__()
                           for f in self.inputs]
        nl = "\n"
        repr = f"{name_of_self} = player()\n"
        repr += f"{name_of_self} < (\n"
        for f in self.inputs:
            if f in name_of_global:
                repr = f"{name_of_global[f]} = {f.__repr__()}\n"\
                     + repr \
                     + indent_string(
                        name_of_global[f], 4
                       )
            else:
                repr += indent_string(f.__repr__(), 4)                    
            repr += ",\n"
        repr += ")"
        return repr

    def play(self):
        self.os.start()

    def stop(self):
        self.os.stop()

    def reset(self):
        self.t = 0.0

    def unplug(self, idx=None):
        if idx is not None:
            return self.inputs.pop(idx)
        removed = self.inputs
        self.inputs = []
        return removed

class square(funk):
    def __init__(self, freq):
        self.freq = freq
        self.repr = f"square({self.freq})"

    def f(self, t):
        return np.sign(np.sin(2 * np.pi * self.freq * t))
    
class sine(funk):
    def __init__(self, freq):
        self.freq = freq
        self.repr = f"sine({self.freq})"

    def f(self, t):
        return np.sin(2 * np.pi * self.freq * t)

class saw(funk):
    def __init__(self, freq):
        self.freq = freq
        self.repr = f"saw({self.freq})"

    def f(self, t):
        return 2 * (t * self.freq - np.floor(t * self.freq)) - 1

class decay(funk):
    def __init__(self, amount):
        self.amount = amount
        self.repr = f"decay({self.amount})"

    def f(self, t):
        return np.exp(-self.amount * t)

class nnoise(funk):
    def __init__(self):
        self.repr = "nnoise()"

    def f(self, t):
        return np.random.randn(len(t)) / 3

class shotnoise(funk):
    def __init__(self, rate):
        self.rate = rate / SAMPLERATE
        self.repr = f"shotnoise({self.rate})"

    def f(self, t):
        return np.random.poisson(self.rate, len(t))

class crackle(funk):
    def __init__(self, rate):
        self.repr = f"crackle({rate})"
        self.shot = shotnoise(rate)
        self.noise = nnoise()

    def f(self, t):
        return self.shot(t) * self.noise(t)

class vinal(funk):
    def __init__(self, 
                 crackle_rate=8, 
                 crackle_level=1, 
                 noise_level=0.025,
                 noise_modulation_freq=1/8,
                 noise_modulation_amount=0.2):
        self.repr = f"""vinal(
    crackle_rate={crackle_rate},
    crackle_level={crackle_level},
    noise_level={noise_level},
    noise_modulation_freq={noise_modulation_freq},
    noise_modulation_amount={noise_modulation_amount},
)"""
        self.crackle_level = crackle_level
        self.crackle = crackle(crackle_rate)
        self.noise_level = noise_level
        self.noise = nnoise()
        self.noise_modulator = noise_modulation_amount\
                             * (sine(noise_modulation_freq)**2 - 1)\
                             + 1

    def f(self, t):
        return self.crackle_level * self.crackle(t)\
             + self.noise_level * self.noise(t)\
             * self.noise_modulator(t)

class epiano(funk):
    def __init__(self, 
                 freq=440, 
                 base_signal=sine,
                 harmonics_decay=0.5, 
                 harmonics=8):
        self.repr = f"epiano(\n"\
                  + f"    freq={freq},\n"\
                  + f"    base_signal={base_signal.__name__},\n"\
                  + f"    harmonics_decay={harmonics_decay},\n"\
                  + f"    harmonics={harmonics},\n)"
        self.harmonics = [harmonics_decay**i * base_signal(i * freq) for i 
                          in range(1, harmonics + 1)]

    def f(self, t):
        return np.sum([f(t) for f in self.harmonics], axis=0)

def indent_string(s, indent):
    return "\n".join([(" " * indent) + line 
                      for line in s.split("\n")])

try:
    load(where=globals())
except FileNotFoundError as e:
    print(e)
