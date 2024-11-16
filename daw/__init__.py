"""
The simple DAW

Author: 
    Leonard Franz
"""

# Fill the namespace
from .base import *
from .oscillators import *
from .instruments import *
from .notes import *

import __main__

def load(name : str = "save.daw", 
         where : dict = __main__.__dict__):
    """
    Executes a DAW script in the importing namespace

    Args:
        name (str):   file name of the script to execute
        where (dict): __dict__ of namespace to execute 
                      the script in
    """
    with open(name, "r") as f:
        file = f.read()
    exec(file, where, dict())

# Load the save.daw script on import
try:
    load(where=globals())
except Exception as e:
    if type(e) != FileNotFoundError:
        raise e
