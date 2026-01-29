DOCSTRING_FOR_FUNCTION_DEFAULT = """Summarize the function in one line.

Several sentences providing an extended description. Refer to
variables using back-ticks, e.g. `var`. For functions (also method and module),
there should be no blank lines after closing the docstring.

Parameters
----------
var1 : array_like
    Array_like means all those objects -- lists, nested lists, etc. --
    that can be converted to an array.

*args : iterable
    Other arguments.

Returns
-------
describe : type
    Explanation of return value named `describe`.

out : type
    Explanation of `out`.

Examples
--------
These are written in doctest format, and should illustrate how to
use the function.

>>> a = [1, 2, 3]
>>> print([x + 3 for x in a])
[4, 5, 6]
"""

DOCSTRING_FOR_CLASS_DEFAULT = """One line summary for the class and its purpose.

The __init__ method can be documented either here, or have its separate
docstring in the method itself. Stick with one of the two choices.
This paragraph (and others that may follow) are for explaining the
class in more detail.

After closing the class docstring, there should be one blank line to
separate following codes (PEP257).

Parameters
----------
num : float
    The number to be used for operations.

msg : str (default: "")
    Message to be displayed.

Attributes
----------
x : int
    Description of attribute `x`

References
----------
[1] https://numpydoc.readthedocs.io/en/latest/
"""
