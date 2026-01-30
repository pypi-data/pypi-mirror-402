def copy_docstring(from_func):
    """Decorator function to assign a docstring from another function."""

    def wrapped(to_func):
        to_func.__doc__ = from_func.__doc__
        return to_func

    return wrapped
