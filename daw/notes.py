from __future__ import annotations
import numpy as np
from .base import funk, daw_object
from .utils import _get_global_daw_objects
import curses as c
from typing import *

BPM = 120
NOTE_SEMITONE_OFFSET = {
    'C': 0,
    'D': 2,
    'E': 4,
    'F': 5,
    'G': 7,
    'A': 9,
    'B': 11,
}

C_MAJOR = [0, 2, 4, 5, 7, 9, 11]
C_MINOR = [0, 2, 3, 5, 7, 8, 10]
C_DORIAN = [0, 2, 3, 5, 7, 9, 10]

def note_string(semitone : int) -> str:
    """
    Returns the note in string form of
    a given semi tone index

    Note: 0 returns C4
    """
    octave = semitone // 12 + 4
    note = semitone % 12
    for k, v in list(NOTE_SEMITONE_OFFSET.items()):
        if v == note:
            return k + str(octave)
        if v + 1 == note:
            return k + "#" + str(octave)
        if v - 1 == note:
            return k + "b" + str(octave)

def semitone(note_string : str) -> int:
    """
    Returns the semi tone index for a 
    given note in string form

    Note: C4 returns 0
    """
    note = note_string[0].upper()
    octave = int(note_string[-1])
    deminished = "b" in note_string 
    sharp = "#" in note_string
    return (
        NOTE_SEMITONE_OFFSET[note] 
        + (octave - 4) * 12 
        + sharp 
        - deminished
    )

def frequency(st : int) -> float:
    """
    Returns the frequency of a given
    simtone index

    Note: st = 0 is the note C4 (261,626 Hz)
    """
    return 440 * 2 ** ((st - 9) / 12)

class Note:
    """
    Class representing a note
    """
    def __init__(self, 
                 note_string : str ="C4",
                 start : float = 0,
                 duration : float = 1,
                 velocity : float = 1,
                 ):
        self.note_string : str = note_string
        self.start : float = start
        self.duration : float = duration
        self.velocity : float = velocity

    @property
    def st(self) -> int:
        return semitone(self.note_string)

    @st.setter
    def st(self, st : int):
        self.note_string = note_string(st)

    @property
    def frequency(self) -> float:
        return frequency(self.st)

    def __add__(self, other : int) -> Note:
        """
        Shift the note up by 'other' amount of
        semi tones
        """
        if not isinstance(other, int):
            raise TypeError(
                "One can only add semiton offset to notes"
            )
        else:
            st = self.st + other
            return Note(
                note_string=note_string(st),
                start=self.start,
                duration=self.duration,
                velocity=self.velocity,
            )


    def __sub__(self, other : int) -> Note:
        """
        Shift the note down by 'other' amount of
        semi tones
        """
        if not isinstance(other, int):
            raise TypeError(
                "One can only subtract semiton offset from notes"
            )
        else:
            st = self.st - other
            return Note(
                note_string=note_string(st),
                start=self.start,
                duration=self.duration,
                velocity=self.velocity,
            )

    def __mul__(self, other : float) -> Note:
        """
        Offsets the note start in positive direction 
        by 'other' amount of seconds
        """
        if not isinstance(other, float):
            raise TypeError(
                "Note starts can only be offset by float values"
            )
        else:
            return Note(
                note_string=self.note_string,
                start=self.start + other,
                duration=self.duration,
                velocity=self.velocity,
            )
    
    def __truediv__(self, other : float) -> Note:
        """
        Offsets the note start in negative direction 
        by 'other' amount of seconds
        """
        if not isinstance(other, float):
            raise TypeError(
                "Note starts can only be ofset by float values"
            )
        else:
            return Note(
                note_string=self.note_string,
                start=self.start - other,
                duration=self.duration,
                velocity=self.velocity,
            )


    def __lt__(self, other : Note) -> bool:
        """
        Checks if 'other' note is lower
        """
        return self.st < other.st
    
    def __le__(self, other : Note) -> bool:
        """
        Checks if 'other' note is lower or equal
        """
        return self.st <= other.st

    def __eq__(self, other : Note) -> bool:
        """
        Checks if 'other' note is equal
        """
        return self.st == other.st

    def __ne__(self, other : Note) -> bool:
        """
        Checks if 'other' note is not equal
        """
        return self.st != other.st

    def __repr__(self) -> str:
        return f"Note(\"{self.note_string}\", {self.start}, {self.duration}, {self.velocity})"


class NoteIndicator(funk):
    """
    Curve that describes attack and decay of a note
    """
    def __init__(self, 
                 note : Note, 
                 attack : float =0.01,
                 decay : float =0.1):
        self.note : Note = note
        self.attack : float = attack
        self.decay : float = decay

    @property
    def repr(self) -> str:
        return f"NoteIndicator({self.note})"

    def f(self, t : np.ndarray | float ) -> np.ndarray | float:
        t = np.atleast_1d(t)
        r = np.zeros_like(t)
        before = t < self.note.start / BPM * 60
        after = t > (self.note.start + self.note.duration) / BPM * 60
        inside = np.logical_not(before | after)

        r[inside] = 1 - np.exp(-((t[inside] - self.note.start / BPM * 60) / self.attack))
        r[after] = np.exp(
            -((t[after] - (self.note.start + self.note.duration) / BPM * 60) 
             / self.decay)
        )
        return r

class nfunk(daw_object):
    """
    FUNKy note function that returns a list of notes
    """
    def __init__( 
        self, 
        f : Union[
                Callable[[],List[Note]], 
                int
        ] = 0,
        repr : str = ""
    ):
        self._repr : str = repr

        if type(f) == int:
            self.f : Union[Callable[[], List[Note]],
                           Callable[[Self], List[Note]]] = lambda: [Note(note_string(f))]
        elif callable(f):
            self.f : Union[Callable[[], List[Note]],
                           Callable[[Self], List[Note]]] = f

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

    def __call__(self) -> List[Note]:
        return self.f()

class Pitcher(funk):
    """
    Pitches an input signal according to its note list
    """
    def __init__(self):
        self.note_signal : nfunk | None = None
        self.signal : funk | None = None

    @property
    def repr(self) -> str:
        repr = f"Pitcher()"
        names_of_globals = _get_global_daw_objects()
        name_of_self = names_of_globals.pop(self)
        if self.note_signal:
            if self.note_signal in names_of_globals:
                repr += f"\n{self.note_signal}"
                repr += f"\n{name_of_self} < {names_of_globals[self.note_signal]}"
            else:
                repr += f"\n{name_of_self} < {self.note_signal}"
        if self.signal:
            if self.signal in names_of_globals:
                repr += f"\n{self.signal}"
                repr += f"\n{name_of_self} < {names_of_globals[self.signal]}"
            else:
                repr += f"\n{name_of_self} < {self.signal}"
        return repr

    def __lt__(self, other : nfunk | funk):
        """
        Makes a < b short hand for plugging in
        a funk or nfunk
        """
        if isinstance(other, nfunk):
            self.note_signal = other
        elif isinstance(other, funk):
            self.signal = other
        else:
            raise TypeError("Pitchers can only receive funks or note funks")

    def f(self, t : np.ndarray | float) -> np.ndarray | float:
        if self.note_signal is not None:
            notes = self.note_signal()
        else:
            raise RuntimeError("Pitcher has no note signal")
        t = np.atleast_1d(t)
        s = np.zeros_like(t)
        for note in notes:
            if note.start / BPM * 60 > t[-1]:
                continue
            if (note.start + note.duration) / BPM * 60 + 0.5 < t[0]:
                continue
            if self.signal is not None:
                s += self.signal((t - note.start) * 
                                 note.frequency / frequency(0)) \
                  * note.velocity * NoteIndicator(note)(t)
            else:
                raise RuntimeError("Pitcher has no input signal")
        return s


class Sequencer(nfunk):
    """
    Equidistant note sequencer
    """
    def __init__(self, 
                 num_notes : int = 16, 
                 note_length : float = 1/8, 
                 repeats : int = 1024,
                 sequence : List[Note] | None = None):
        """
        Note: First 2 parameters are overwritten if 
        sequence is given
        """
        self.repeats : int = repeats
        if sequence is None:
            self._num_notes : int = num_notes
            self._note_length : float = note_length
            self._sequence : List[Note] = [Note(start=note_length * i,
                                           duration=note_length)
                                           for i in range(num_notes)]
        else:
            self._check_sequence_validity(sequence)
            self._sequence : List[Note] = sequence
            self._num_notes : int = len(sequence)
            self._note_length : float = sequence[0].duration

    def _check_sequence_validity(self, sequence: List[Note]):
        if not all([isinstance(note, Note)
                    for note 
                    in sequence]):
            raise TypeError("All notes of the sequence "
                            "given to a equidistant sequencer "
                            "must be a note")
        elif not all([note.duration == note_.duration
                      for (note, note_) in zip(sequence[:-1],
                                               sequence[1:])]):
            raise TypeError("All notes of the sequence "
                            "given to a equidistant sequencer "
                            "must be a of the same length")
        elif not all(
                [sequence[i].start + sequence[i].duration 
                 == sequence[i + 1].start for i 
                 in range(len(sequence) - 1)]
            ):
            raise TypeError("All notes of the sequence given to a "
                            "equidistant sequencer must be contiguous")

    @property
    def repr(self) -> str:
        repr = f"Sequencer(repeats={self.repeats}, sequence=[\n"
        for note in self._sequence:
            repr += f"    {note},\n"
        repr += "])"
        return repr

    @property
    def num_notes(self) -> int:
        return self._num_notes

    @num_notes.setter
    def num_notes(self, num_notes):
        """
        Makes a new note sequence with specified number
        of note

        Note: Overrides existing note sequence
        """
        self._num_notes = num_notes
        self._sequence = [Note(start=self._note_length * i,
                               duration=self._note_length)
                          for i in range(num_notes)]

    @property
    def note_length(self) -> float:
        """
        Return the note length of 
        the notes in the equidistant sequencer
        """
        return self._note_length

    @note_length.setter
    def note_length(self, note_length : float):
        """
        Makes the notes in the equidistant 
        sequencer according to given note 
        length
        """
        self._note_length = note_length
        for i, note in enumerate(self._sequence):
            note.start = note_length * i
            note.duration = note_length

    @property
    def sequence(self):
        return self._sequence

    @sequence.setter
    def sequence(self, sequence):
        """
        Sets the sequence
        """
        self._check_sequence_validity(sequence)
        self._sequence = sequence
    
    def f(self) -> List[Note]:
        return [n * float(i * self.num_notes * self.note_length) 
                for i in range(self.repeats) 
                for n in self.sequence]
    
    def __len__(self):
        return self._num_notes

    class NoteEditor:
        def __init__(self, note_range, length, sequencer):
            self.note_range = note_range
            self.length = length
            self.sequence = sequencer.sequence
            self.cursor = (0, 0)
            self.sb = self.status_bar(self)

        def __str__(self):
            roll = ""
            for i in range(*self.note_range):
                line = ["█" if self.sequence[j] == i 
                        else " " for j in range(self.length)]
                roll += "".join(line) + "\n"
            return roll

        class status_bar:
            def __init__(self, editor):
                self.editor = editor

            def __str__(self):
                raise NotImplementedError

            def enter_command(self):
                raise NotImplementedError

        def increase_size(self):
            raise NotImplementedError

        def decrease_size(self):
            raise NotImplementedError

        def toggle_note(self, position):
            raise NotImplementedError

        def move_cursor(self, direction):
            raise NotImplementedError

        def write(self):
            raise NotImplementedError


    def configure(self):
        raise NotImplementedError
