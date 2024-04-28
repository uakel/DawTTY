from .base import funk
from .oscillators import *

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
