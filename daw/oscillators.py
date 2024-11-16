import numpy as np
from numpy._core.multiarray import ndarray
from .base import funk, SAMPLERATE
from typing import *

class square(funk):
    """
    Square wave oscillator
    """
    def __init__(self, freq : float):
        self.freq = freq
        self._repr = f"square({self.freq})"

    def f(self, t : np.ndarray | float) -> np.ndarray | float:
        return np.sign(np.sin(2 * np.pi * self.freq * t))
    
class sine(funk):
    """
    Sine wave oscillator
    """
    def __init__(self, freq : float):
        self.freq = freq
        self._repr = f"sine({self.freq})"

    def f(self, t : np.ndarray | float) -> np.ndarray | float:
        return np.sin(2 * np.pi * self.freq * t)

class saw(funk):
    """
    Saw wave oscillator
    """
    def __init__(self, freq):
        self.freq = freq
        self._repr = f"saw({self.freq})"

    def f(self, t : np.ndarray | float) -> np.ndarray | float:
        return 2 * (t * self.freq - np.floor(t * self.freq)) - 1

class decay(funk):
    """
    Exponential decay
    """
    def __init__(self, amount):
        self.amount = amount
        self._repr = f"decay({self.amount})"

    def f(self, t : np.ndarray | float) -> np.ndarray | float:
        return np.exp(-self.amount * t)

class nnoise(funk):
    """
    Normal distributed noise
    """
    def __init__(self):
        self._repr = "nnoise()"

    def f(self, t : np.ndarray | float) -> np.ndarray | float:
        if type(t) == float:
            return np.random.randn(1) / 3
        elif type(t) == np.ndarray:
            return np.random.randn(t.shape[0]) / 3
        else:
            raise TypeError(
                "nnoise only accepts float or nd arrays as input"
            )

class shotnoise(funk):
    """
    Shot noise
    """
    def __init__(self, rate):
        self.rate = rate / SAMPLERATE
        self._repr = f"shotnoise({self.rate})"

    def f(self, t : np.ndarray | float) -> np.ndarray | float:
        if type(t) == float:
            return np.random.poisson(self.rate, 1)
        elif type(t) == np.ndarray:
            return np.random.poisson(self.rate, t.shape[0])
        else:
            raise TypeError(
                "nnoise only accepts float or nd arrays as input"
            )
