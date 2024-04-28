# The simple DAW

from .base import *
from .oscillators import *
from .instruments import *

import __main__

def load(name="save.daw", where=__main__.__dict__):
    with open(name, "r") as f:
        file = f.read()
    exec(file, where)

try:
    load(where=globals())
except FileNotFoundError as e:
    print(e)
