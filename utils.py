from .base import daw_object
import __main__

def _indent_string(s, indent):
    return "\n".join([(" " * indent) + line 
                      for line in s.split("\n")])

def _get_global_daw_objects():
    return {o: n for n, o in __main__.__dict__.items() 
                          if isinstance(o, daw_object)}
