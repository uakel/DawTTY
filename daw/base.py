"""
Base classes
"""
from __future__ import annotations

import numpy as np
import sounddevice as sd
from concurrent.futures import ThreadPoolExecutor
from abc import ABC, abstractmethod
from typing import *

BLOCK_SIZE = 6_000
SAMPLERATE = 48_000

class daw_object(ABC):
    """
    Abstract base class for all objects in 
    the DAW
    """
    def save(
        self, 
        name : str ="save.daw"
    ):
        """
        Saves the python code that generates the 
        object
        """
        with open(name, "w") as f:
            f.write("#!python\n" + repr(self))

    @abstractmethod
    def __repr__(self) -> str:
        """
        Returns the python code that generates 
        the object
        """
        raise NotImplementedError

from .utils import _get_global_daw_objects

class funk(daw_object):
    """
    FUNKy function object
    """
    def __init__(
        self, 
        f : Union[Callable[[np.ndarray | float], 
                           np.ndarray | float], 
                  str, 
                  int, 
                  float] = 0,
        repr : str = ""
    ):
        """
        Generates a FUNKtion object by 
        either a callable, a string 
        representing the inside of a 
        lambda function depending on t,
        or a constant
        """
        # Initialize the function and repr
        self.f : Union[Callable[[Self, np.ndarray | float], 
                                 np.ndarray | float],
                       Callable[[np.ndarray | float], 
                                 np.ndarray | float]] = (
            lambda t: 0
        )
        self._repr : str = repr

        # Set the function and repr
        if callable(f):
            self.f = f
            self._repr = f.__repr__()
        elif type(f) == str:
            self.f = eval("lambda t: " + f)
            self._repr = f
        elif type(f) in {int, float}:
            self.f = lambda t: f
            self._repr = str(f)
        else:
            raise ValueError("f must be callable, "
                             "str, int or float")
        if repr:
            self._repr = repr

    @property
    def repr(self) -> str:
        """
        Property that wraps _repr
        """
        return self._repr

    def __repr__(self):
        """
        Returns the python code that Generates
        the object
        """
        name_of_globals = _get_global_daw_objects()
        if self in name_of_globals:
            return f"{name_of_globals[self]} = {self.repr}"
        return self.repr

    def __call__(
        self, 
        t: np.ndarray | float
    ) -> np.ndarray | float:
        """
        Evaluates the function at time t or times t
        in form of a numpy array
        """
        return self.f(t)
    
    def __add__(
        self, 
        other: Union[funk, int, float]
    ) -> funk:
        """
        Adds two functions or a function and a
        constant
        """ 
        if isinstance(other, funk):
            return funk(lambda t: self.f(t) + other.f(t),
                        repr=f"{self.repr} + {other.repr}")
        elif type(other) in {int, float}:
            return funk(lambda t: self.f(t) + other,
                    repr=f"{self.repr} + {other}")
        else:
            raise ValueError("In addition, both operands "
                             "must be funk, int or float")

    def __sub__(
        self, 
        other: Union[funk, int, float]
    ) -> funk:
        """
        Subtracts two functions or a function and a
        constant
        """
        if isinstance(other, funk):
            return funk(lambda t: self.f(t) - other(t),
                        repr=f"{self.repr} - {other.repr}")
        elif type(other) in {int, float}:
            return funk(lambda t: self.f(t) - other,
                        repr=f"{self.repr} - {other}")
        else:
            raise ValueError("In subtraction, both operands "
                             "must be funk, int or float")

    def __neg__(self) -> funk:
        """
        Negates the function
        """
        return funk(lambda t: -self.f(t),
                    repr=f"(-{self.repr})")

    def __mul__(
        self, 
        other : Union[funk, int, float]
    ) -> funk:
        """
        Multiplies two functions or a function and a
        constant
        """
        # Respect the order of operations of 
        # self
        if "+" in self.repr or "-" in self.repr:
            repr = f"({self.repr})"
        else:
            repr = self.repr
        if isinstance(other, funk):
            # Respect the order of operations of
            # other
            if "+" in other.repr or "-" in other.repr:
                other_repr = f"({other.repr})"
            else:
                other_repr = other._repr
            return funk(lambda t: self.f(t) * other.f(t),
                         repr=f"{repr} * {other_repr}")
        elif type(other) in {int, float}:
            return funk(lambda t: self.f(t) * other,
                        repr=f"{repr} * {other}")
        else:
            raise ValueError("In multiplication, both operands "
                             "must be funk, int or float")
    
    def __rmul__(
        self,
        other : Union[int, float]
    ) -> funk:
        """
        Multiplies two functions or a function and a
        constant
        """
        # Respect the order of operations of
        # self
        if "+" in self.repr or "-" in self.repr:
            repr = f"({self.repr})"
        else:
            repr = self.repr
        return funk(lambda t: other * self.f(t),
                    repr=f"{other} * {repr}")

    def __truediv__(
        self, 
        other : Union[funk, int, float]
    ) -> funk:
        """
        Divides two functions or a function and a
        constant
        """
        if isinstance(other, funk):
            return funk(lambda t: self.f(t) / other.f(t),
                         repr=f"{self.repr}/{other.repr}")
        elif type(other) in {int, float}:
            if other == 0:
                raise ZeroDivisionError("Division by zero")
            return funk(lambda t: self.f(t) / other,
                        repr=f"{self.repr}/{other}")
        else:
            raise TypeError(
                "Devision is only possible amongst funks, "
                "ints and floats"
            )

    def __pow__(
        self, 
        other : Union[funk, int, float]
    ) -> funk:
        """
        Raises the function to the power of another
        function or a constant
        """
        if isinstance(other, funk):
            return funk(lambda t: self.f(t) ** other.f(t),
                         repr=f"{self.repr}**({other.repr})")
        return funk(lambda t: self.f(t) ** other,
                    repr=f"{self.repr}**{other}")

from .utils import _indent_string

class player(funk):
    """
    A Player that evaluats funks 
    and plays them on the speakers
    """
    def __init__(self):
        """
        Sets up the output stream
        and initializes some variables
        """
        self.inputs : List[funk] = []
        self.t : float = 0.0
        self.block = np.linspace(0, BLOCK_SIZE / SAMPLERATE, 
                                 BLOCK_SIZE)
        self.os = sd.OutputStream(samplerate=SAMPLERATE, 
                                  blocksize=BLOCK_SIZE,
                                  channels=1, 
                                  dtype='int16', 
                                  callback=self.tick)
        self.executor = ThreadPoolExecutor()
        self.evaluation = np.zeros(BLOCK_SIZE, dtype=np.int16)
        self.all_outdata = []

    def __call__(
        self, t : np.ndarray | float
    ) -> np.ndarray | float:
        """
        A player is also a funk. This can be 
        used link players into the evaluation
        chain and listen to parts of the 
        signal
        """
        return np.sum(
            np.array([f(t) for f in self.inputs]),
            axis=0
        )

    def __getitem__(
            self,
            idx: int
    ) -> funk:
        """
        Returns the idx-th input
        to the player
        """
        return self.inputs[idx]

    def _evaluate(
        self, 
        t: float
    ):
        """
        Evaluates the inputs at the block
        starting at time t, brings the result
        into the right format for the output stream
        and stores it in a buffer variable
        """
        t_eval = t + self.block
        evaluation = np.sum(
            np.array([f(t_eval) for f in self.inputs]),
            axis=0
        )
        evaluation = np.clip(evaluation, -1, 1)
        evaluation = np.int16(evaluation * 32767)
        self.evaluation = evaluation

    def tick(self, 
             outdata: np.ndarray, 
             frames: int,
             time: "CData",
             status: sd.CallbackFlags):
        """
        The callback function for the output stream
        """
        outdata[:, 0] = self.evaluation
        self.all_outdata.append(outdata.copy())
        self.executor.submit(self._evaluate, self.t)
        self.t += BLOCK_SIZE / SAMPLERATE

    def plug(self, other: funk | Iterable[funk]):
        """
        Plugs a funk into the player
        """
        if isinstance(other, funk):
            self.inputs.append(other)
        elif hasattr(other, '__iter__'):
            for i, f in enumerate(other):
                if isinstance(f, funk):
                    self.inputs.append(f)
                else:
                    raise ValueError(f"Expected funk, got {type(f)}"
                                     f" at index {i}")
        else:
            raise ValueError(f"Expected funk or iterable of funks,"
                             f" got {type(other)}")
    
    def __lt__(self, other):
        """
        Makes a < b shorthand for plugging b into a
        """
        self.plug(other)

    def __gt__(self, other):
        """
        Makes a > b shorthand for unplug a from b
        """
        return self.unplug(other)

    @property
    def repr(self) -> str:
        """
        Builds code that generates the player together
        with its funk graph
        """
        name_of_global = _get_global_daw_objects()
        name_of_self = name_of_global.pop(self)
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
        """
        Lets the player play
        """
        self.os.start()

    def stop(self):
        """
        Stops the player
        """
        self.os.stop()

    def reset(self):
        """
        Resets the player to time 0
        """
        self.t = 0.0

    def unplug(self, idx: None | int = None) -> funk | List[funk]:
        """
        Unplugs a funk at a certain index or all funks
        if index is not given
        """
        if idx is not None:
            return self.inputs.pop(idx)
        removed = self.inputs
        self.inputs = []
        return removed
