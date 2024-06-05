import numpy as np
import sounddevice as sd
import __main__

BLOCK_SIZE =  1_024
SAMPLERATE = 48_000

class daw_object:
    def __init__(self):
        pass

    def save(self, name="save.daw"):
        with open(name, "w") as f:
            f.write(repr(self))

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
        name_of_global = {o: n for n, o in __main__.__dict__.items() 
                          if isinstance(o, daw_object)}
        if self in name_of_global:
            return f"{name_of_global[self]} = {self.repr}"
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
        if "+" in self.repr or "-" in self.repr:
            repr = f"({self.repr})"
        else:
            repr = self.repr
        if isinstance(other, funk):
            if "+" in other.repr or "-" in other.repr:
                other_repr = f"({other.repr})"
            else:
                other_repr = other.repr
            return funk(lambda t: self.f(t) * other.f(t),
                         repr=f"{repr} * {other_repr}")
        return funk(lambda t: self.f(t) * other,
                    repr=f"{repr} * {other}")
    
    def __rmul__(self, other):
        if "+" in self.repr or "-" in self.repr:
            repr = f"({self.repr})"
        else:
            repr = self.repr
        return funk(lambda t: other * self.f(t),
                    repr=f"{other} * {repr}")

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

from .utils import _indent_string

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

    def __getitem__(self, idx):
        return self.inputs[idx]

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

    @property
    def repr(self):
        name_of_global = {o: n for n, o in __main__.__dict__.items() 
                          if isinstance(o, daw_object)}
        name_of_self = name_of_global.pop(self)
        representations = [f"{name_of_global[f]}"
                           if f in name_of_global
                           else f.__repr__()
                           for f in self.inputs]
        nl = "\n"
        repr = f"{name_of_self} < (\n"
        for f in self.inputs:
            if f in name_of_global:
                repr = f"{f.__repr__()}\n"\
                     + repr \
                     + _indent_string(
                        name_of_global[f], 4
                       )
            else:
                repr += _indent_string(f.__repr__(), 4)                    
            repr += ",\n"
        repr += ")"
        repr = f"player()\n" + repr
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
