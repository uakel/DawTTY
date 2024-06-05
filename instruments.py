from .base import funk
from .oscillators import *

class crackle(funk):
    def __init__(self, rate):
        self.repr = f"crackle({rate})"
        self.shot = shotnoise(rate)
        self.noise = nnoise()

    def f(self, t):
        return self.shot(t) * self.noise(t)

VINAL_CHRACKLE_RATE = 8
VINAL_CHRACKLE_LEVEL = 1
VINAL_NOISE_LEVEL = 0.025
VINAL_NOISE_MODULATION_FREQ = 1/8
VINAL_NOISE_MODULATION_AMOUNT = 0.2
class vinal(funk):
    def __init__(self, 
                 crackle_rate=VINAL_CHRACKLE_RATE, 
                 crackle_level=VINAL_CHRACKLE_LEVEL, 
                 noise_level=VINAL_NOISE_LEVEL,
                 noise_modulation_freq=VINAL_NOISE_MODULATION_FREQ,
                 noise_modulation_amount=VINAL_NOISE_MODULATION_AMOUNT):

        active_args = []
        if crackle_rate != VINAL_CHRACKLE_RATE:
            active_args.append(f"crackle_rate={crackle_rate}")
        if crackle_level != VINAL_CHRACKLE_LEVEL:
            active_args.append(f"crackle_level={crackle_level}")
        if noise_level != VINAL_NOISE_LEVEL:
            active_args.append(f"noise_level={noise_level}")
        if noise_modulation_freq != VINAL_NOISE_MODULATION_FREQ:
            active_args.append(f"noise_modulation_freq={noise_modulation_freq}")
        if noise_modulation_amount != VINAL_NOISE_MODULATION_AMOUNT:
            active_args.append(f"noise_modulation_amount={noise_modulation_amount}")
        self.repr = f"vinal({', '.join(active_args)})"


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

EPANO_FREQ = 440
EPANO_BASE_SIGNAL = sine
EPANO_HARMONICS_DECAY = 0.5
EPANO_HARMONICS = 8
class epiano(funk):
    def __init__(self, 
                 freq=EPANO_FREQ, 
                 base_signal=EPANO_BASE_SIGNAL,
                 harmonics_decay=EPANO_HARMONICS_DECAY, 
                 harmonics=EPANO_HARMONICS):

        active_args = []
        if freq != EPANO_FREQ:
            active_args.append(f"freq={freq}")
        if base_signal != EPANO_BASE_SIGNAL:
            active_args.append(f"base_signal={base_signal}")
        if harmonics_decay != EPANO_HARMONICS_DECAY:
            active_args.append(f"harmonics_decay={harmonics_decay}")
        if harmonics != EPANO_HARMONICS:
            active_args.append(f"harmonics={harmonics}")
        self.repr = f"epiano({', '.join(active_args)})"

        self.harmonics = [harmonics_decay**i * base_signal(i * freq) for i 
                          in range(1, harmonics + 1)]
        

    def f(self, t):
        return np.sum([f(t) for f in self.harmonics], axis=0)
