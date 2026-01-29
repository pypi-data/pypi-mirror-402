<h1 align="center">
<img src="https://raw.githubusercontent.com/Nimish-4/py-docstrings/main/logo.png" width="312" height="250"  border='0px'>
</h1>

A command-line tool for generating Python docstrings using Concrete Syntax Trees (CST).

`py-docstrings` analyzes Python source code with [**LibCST**](https://github.com/Instagram/LibCST) and inserts docstrings while preserving
original formatting, comments, and structure. `py-docstrings` uses Concrete Syntax Trees, which 
retain the exact structure of the original source code. The primary interface is the CLI, with a
few different options depending upon use.





## Installation

```bash
pip install py-docstrings
```

## Basic Usage

To generate docstrings directly in a file:

```bash
docgen main.py
```

To check for missing docstrings without modifying files:

```bash
docgen main.py --check
```

## Additional Options

* `--recursive`
  Recursively process Python files in a directory.

* `--verbose`
  Display information about processed files.

* `--full`
  Generate a more complete numpy-style docstring with more attributes.

---

## Example

### Before

```python
def add(a, b):
    return a + b
```

### After

```python
def add(a, b):
    """Summarize the function in one line.
    
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
    return a + b
```

---

## Supported Targets

* Top-level functions
* Classes
* Class methods

Existing docstrings are **not overwritten**.


## Upcoming features

Planned improvements include:

* Docstrings include actual function arguments
* Generate docstring for specific functions/classes in a module

---

## License

MIT License


