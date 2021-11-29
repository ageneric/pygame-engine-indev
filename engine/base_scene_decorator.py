"""Call as a decorator.
"""

from functools import wraps

def init_scene_nodes(set_attributes_function):
    def init_then_set_attributes(init):
        @wraps(init)
        def wrapper(*args, **kwargs):
            init(*args, **kwargs)
            set_attributes_function(args[0])
        return wrapper
    return init_then_set_attributes
