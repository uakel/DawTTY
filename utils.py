def _indent_string(s, indent):
    return "\n".join([(" " * indent) + line 
                      for line in s.split("\n")])
