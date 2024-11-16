from .base import daw_object
import __main__
from typing import *

def _indent_string(s : str, indent : int) -> str:
    """
    Indents a string by 'indent' spaces
    """
    return "\n".join([(" " * indent) + line 
                      for line in s.split("\n")])

def _get_global_daw_objects() -> Dict[daw_object, str]:
    """
    Returns all daw objects insed the main namespace
    """
    return {o: n for n, o in __main__.__dict__.items() 
                          if isinstance(o, daw_object)}
