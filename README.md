# DawTTY: Your python based digital audio work station for the terminal
> You only make techno, if every line of code that makes your techno is written by yourself. Else, you are not making techno.
>
> -- <cite>totally reasonable techno artists</cite>

Warning: ***Work in Progress!***

DawTTY is nothing more than a library to compose functions into an into an audible signal that can be played over the speaker. Higher level functions then make it possible to generate a piece of music.

## Installation
Clone this repository and run
```
pip install -e .
```

## Usage
DawTTY is supposed to be used inside a repl, but can also be used inside a script. We recommend bpython for auto completion, but any repl should do.

The most important object of DawTTY is the player. The player accepts so-called "funks" (a wrapper for a float valued function), which can be plugged into the player for playback. A minimal working example that plays a sine signal, is shown bellow:
```python
>>> from daw import *
>>> p = player()
>>> p < sine(220) # freq: 220 Hz
>>> p.play()
```
The playback can then be stopped with `p.stop()`

In this example, one can see the most fundamental operator in DawTTY, which is the inequality sign: `<`. This operator "plugs" the sine function into the player. 

All the usual operations `+`,`-`,`*`,`/` are supported for funks, allowing one to generate more complex signals:
```python
>>> p.unplug() # Remove all input signals from the player
[sine(220)]
>>> p < sine(220) * sine(1/0.5)
>>> p.play()
```

Here is an even more complex example that generates a piece of (admittedly not very pleasant) music in C-minor:
```python
>>> from daw import *
>>> from random import choice
>>> p = player()
>>> pi = Pitcher()
>>> pi < epiano(frequency(semitone("C4")))
>>> s = Sequencer(note_length=1/4)
>>> minor = [0, 2, 3, 5, 7, 8, 10]
>>> for i in range(16):
        s.sequence[i] += choice(minor)
>>> pi < s
>>> p < pi
>>> p.play()
```

If one justs types `p`–the variable containing the player–into the console, then one gets the following output:
```python
p = player()
pi = Pitcher()
s = Sequencer(repeats=1024, sequence=[
    Note("D4", 0.0, 0.25, 1),
    Note("D4", 0.25, 0.25, 1),
    Note("D4", 0.5, 0.25, 1),
    Note("A#4", 0.75, 0.25, 1),
    Note("D4", 1.0, 0.25, 1),
    Note("D4", 1.25, 0.25, 1),
    Note("A#4", 1.5, 0.25, 1),
    Note("D#4", 1.75, 0.25, 1),
    Note("A#4", 2.0, 0.25, 1),
    Note("D4", 2.25, 0.25, 1),
    Note("G#4", 2.5, 0.25, 1),
    Note("E#4", 2.75, 0.25, 1),
    Note("D#4", 3.0, 0.25, 1),
    Note("G4", 3.25, 0.25, 1),
    Note("A#4", 3.5, 0.25, 1),
    Note("E#4", 3.75, 0.25, 1),
])
pi < s
pi < epiano(freq=261.6255653005986)
p < (
    pi,
)
```
This is a piece of python code that reconstructs the computation graph that is plugged into the player. By typing `p.save()`, this code is saved in a file called `save.daw`. When one imports DawTTY somewhere where the CWD contains a `save.daw` file, the contents of this file are automatically executed, thereby restoring the state of a previously saved computation graph.

By extending the compuation graph one should be able to create real pieces of music. To make this process easier additional features for DawTTY are planed:
- More high level functions for easy instrument creation (this includes a sampler and drum machine)
- TUI elements for faster manipulation of signal parameters
- Effects and filters
- Procedural creation of visuals that accompany the music
