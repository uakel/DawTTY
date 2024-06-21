import numpy as np
from .base import funk
from .utils import _get_global_daw_objects

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

def note_string(semitone):
    octave = semitone // 12 + 4
    note = semitone % 12
    for k, v in list(NOTE_SEMITONE_OFFSET.items()):
        if v == note:
            return k + str(octave)
        if v + 1 == note:
            return k + "#" + str(octave)
        if v - 1 == note:
            return k + "b" + str(octave)

def semitone(note_string):
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

def frequency(st):
    return 440 * 2 ** ((st - 9) / 12)

class Note:
    def __init__(self, 
                 note_string="C4",
                 start=0,
                 duration=1,
                 velocity=1,
                 ):

        self.note_string = note_string
        self.start = start
        self.duration = duration
        self.velocity = velocity

    @property
    def st(self):
        return semitone(self.note_string)

    @st.setter
    def st(self, st):
        self.note_string = note_string(st)

    @property
    def frequency(self):
        return frequency(self.st)

    def __add__(self, other):
        if not isinstance(other, int):
            print("⚡")
        else:
            st = self.st + other
            return Note(
                note_string=note_string(st),
                start=self.start,
                duration=self.duration,
                velocity=self.velocity,
            )


    def __sub__(self, other):
        if not isinstance(other, int):
            print("⚡")
        else:
            st = self.st - other
            return Note(
                note_string=note_string(st),
                start=self.start,
                duration=self.duration,
                velocity=self.velocity,
            )

    def __mul__(self, other):
        if not isinstance(other, int):
            print("⚡")
        else:
            return Note(
                note_string=self.note_string,
                start=self.start + other,
                duration=self.duration,
                velocity=self.velocity,
            )
    
    def __truediv__(self, other):
        if not isinstance(other, int):
            print("⚡")
        else:
            return Note(
                note_string=self.note_string,
                start=self.start - other,
                duration=self.duration,
                velocity=self.velocity,
            )


    def __lt__(self, other):
        return self.st < other.st
    
    def __le__(self, other):
        return self.st <= other.st

    def __eq__(self, other):
        return self.st == other.st

    def __ne__(self, other):
        return self.st != other.st

    def __repr__(self):
        return f"Note(\"{self.note_string}\", {self.start}, {self.duration}, {self.velocity})"

class nfunk(funk):
    def __call__(self):
        return self.f()

class NoteIndicator(funk):
    def __init__(self, note, attack=0.01, decay=0.1):
        self.note = note
        self.attack = attack
        self.decay = decay

    @property
    def repr(self):
        return f"NoteIndicator({self.note})"

    def f(self, t):
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

class Pitcher(funk):
    def __init__(self):
        self.note_signal = None
        self.signal = None

    @property
    def repr(self):
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

    def __lt__(self, other):
        if isinstance(other, nfunk):
            self.note_signal = other
        elif isinstance(other, funk):
            self.signal = other
        else:
            print("⚡You can only plug in a funk or nfunk object")

    def f(self, t):
        notes = self.note_signal()
        s = np.zeros_like(t)
        for note in notes:
            if note.start / BPM * 60 > t[-1]:
                continue
            if (note.start + note.duration) / BPM * 60 + 1 < t[0]:
                continue
            s += self.signal((t - note.start) * 
                             note.frequency / frequency(0)) \
              * note.velocity * NoteIndicator(note)(t)
        return s


class Sequencer(nfunk):
    def __init__(self, num_notes=16, note_length=1/8, repeats=4, sequence=None):
        self.repeats = repeats
        if sequence is None:
            self._num_notes = num_notes
            self._note_length = note_length
            self._sequence = [Note(start=note_length * i,
                                   duration=note_length)
                              for i in range(num_notes)]
        elif not all([isinstance(note, Note)
                    for note 
                    in sequence]):
            print("⚡non-Note object in sequence")
        elif not all([note.duration == note_.duration
                    for note in sequence 
                    for note_ in sequence]):
            print("⚡all notes in sequence must have the same duration")
        elif not all(
                [sequence[i].start + sequence[i].duration 
                 == sequence[i + 1].start for i 
                 in range(len(sequence) - 1)]
            ):
            print("⚡all notes in sequence must be contiguous")
        else:
            self._sequence = sequence
            self._num_notes = len(sequence)
            self._note_length = sequence[0].duration

    @property
    def repr(self):
        repr = f"Sequencer(repeats={self.repeats}, sequence=[\n"
        for note in self._sequence:
            repr += f"    {note},\n"
        repr += "])"
        return repr

    @property
    def num_notes(self):
        return self._num_notes

    @num_notes.setter
    def num_notes(self, num_notes):
        self._num_notes = num_notes
        self._sequence = [Note(start=self._note_length * i,
                               duration=self._note_length)
                          for i in range(num_notes)]

    @property
    def note_length(self):
        return self._note_length

    @note_length.setter
    def note_length(self, note_length):
        self._note_length = note_length
        for i, note in enumerate(self._sequence):
            note.start = note_length * i
            note.duration = note_length

    @property
    def sequence(self):
        return self._sequence

    @sequence.setter
    def sequence(self, sequence):
        self._sequence = sequence
    
    def f(self):
        return [n * int(i * self.num_notes * self.note_length) 
                for i in range(self.repeats) 
                for n in self.sequence]
    
    def __len__(self):
        return self._num_notes
