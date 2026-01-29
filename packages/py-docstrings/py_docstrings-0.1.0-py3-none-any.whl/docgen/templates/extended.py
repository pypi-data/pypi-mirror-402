DOCSTRING_FOR_FUNCTION = """Summarize the function in one line.

Several sentences providing an extended description. Refer to
variables using back-ticks, e.g. `var`. For functions (also method and module),
there should be no blank lines after closing the docstring.

Parameters
----------
var1 : array_like
    Array_like means all those objects -- lists, nested lists, etc. --
    that can be converted to an array.  We can also refer to
    variables like `var1`.

var2 : int
    The type above can either refer to an actual Python type
    (e.g. ``int``), or describe the type of the variable in more
    detail, e.g. ``(N,) ndarray`` or ``array_like``.

*args : iterable
    Other arguments.

Returns
-------
type
    Explanation of anonymous return value of type ``type``.

describe : type
    Explanation of return value named `describe`.

out : type
    Explanation of `out`.

type_without_description

Other Parameters
----------------
only_seldom_used_keyword : int, optional
    Infrequently used parameters can be described under this optional
    section to prevent cluttering the Parameters section.
**kwargs : dict
    Other infrequently used keyword arguments. Note that all keyword
    arguments appearing after the first parameter specified under the
    Other Parameters section, should also be described under this
    section.

Raises
------
BadException
    Because you shouldn't have done that.

See Also
--------
numpy.array : Relationship (optional).
numpy.ndarray : Relationship (optional), which could be fairly long, in
                which case the line wraps here.
numpy.dot, numpy.linalg.norm, numpy.eye

Notes
-----
Notes about the implementation algorithm (if needed).

This can have multiple paragraphs.

You may include some math:

.. math:: X(e^{j\\omega } ) = x(n)e^{ - j\\omega n}

And even use a Greek symbol like :math:`\\omega` inline.

References
----------
Cite the relevant literature, e.g. [1]_.  You may also cite these
references in the notes section above.

.. [1] https://numpydoc.readthedocs.io/en/latest/format.html

Examples
--------
These are written in doctest format, and should illustrate how to
use the function.

>>> a = [1, 2, 3]
>>> print([x + 3 for x in a])
[4, 5, 6]
"""

DOCSTRING_FOR_CLASS = """One line summary for the class and its purpose.

The __init__ method can be documented either here, or have its separate
docstring in the method itself. Stick with one of the two choices.
This paragraph (and others that may follow) are for explaining the
class in more detail.

After closing the class docstring, there should be one blank line to
separate following codes (PEP257).

Note
----
The `self` parameter is not listed as the first parameter of methods.

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

Examples
--------
Import an example class

>>> from foo import bar
>>> y = bar(3.14)

References
----------
[1] https://numpydoc.readthedocs.io/en/latest/
"""
