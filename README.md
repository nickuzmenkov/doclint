# Numpydoclint

Numpydoclint is a linter for [Numpy style][numpy-style] docstrings.

```
$ numpydoclint -vv asgard midgard/thor.py
asgard/loki.py:12 in function asgard.loki.mischief:
    GL03 Double line break found
asgard/odin.py:10 in type asgard.odin.Allfather:
    SA04 Missing description for See Also 'Yggdrasil' reference
midgard/thor.py:20 in function thor.Thor.strike:
    PR01 Parameters {'mjolnir'} not documented
Errors found in 3 out of 9 objects checked.
```

Numpydoclint uses static file analysis to identify code objects and then uses the [`numpydoc.validate`][numpydoc-validate] module for validation, outputting corresponding [error codes][error-codes] along with explanatory comments.

## Installation

You can install Numpydoclint via the [PIP][pip] package manager:

```bash
$ pip install numpydoc-linter
```

Alternatively, if you wish to install from the source code, follow these steps. Clone the repository and use [Poetry][poetry] to manage the project dependencies specified in `pyproject.toml`:

```bash
$ git clone https://github.com/nickuzmenkov/numpydoclint.git
$ cd numpydoclint
$ poetry install
```

## Usage

Basic usage examples, as well as more advanced usage scenarios are covered in detail in the [Official Documentation][docs].

[numpy-style]: https://numpydoc.readthedocs.io/en/latest/format.html
[numpydoc-validate]: https://numpydoc.readthedocs.io/en/latest/validation.html
[error-codes]: https://numpydoc.readthedocs.io/en/latest/validation.html#built-in-validation-checks
[pip]: https://pip.pypa.io/en/stable/
[poetry]: https://python-poetry.org/
[docs]: https://nickuzmenkov.github.io/numpydoclint/
