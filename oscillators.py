import numpy as np
from .base import funk, SAMPLERATE

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
