"""Numpydoclint.

Numpydoclint is a linter for [Numpy style](https://numpydoc.readthedocs.io/en/latest/format.html) docstrings based on the
[numpydoc.validate](https://github.com/numpy/numpydoc/) module. Basic usage examples, as well as more advanced usage scenarios are covered
in detail in the [Official Documentation](https://nickuzmenkov.github.io/numpydoclint/).
"""
from numpydoclint.constants import __version__
from numpydoclint.validate import validate

__all__ = [
    "validate",
    "__version__",
]
