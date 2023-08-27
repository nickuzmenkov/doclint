# Quickstart

This section will give you a basic understanding of Numpydoclint's capabilities. If you encounter scenarios that go beyond this tutorial, you can find more information in the [Complete Reference](complete_reference.md).

## Basic Usage

Numpydoclint makes it easy to validate all objects in a package or a series of packages:

<!-- termynal -->

```bash
$ numpydoclint -vv asgard midgard
asgard/loki.py:12 in function asgard.loki.mischief:
    GL03 Double line break found
asgard/odin.py:10 in type asgard.odin.Allfather:
    SA04 Missing description for See Also 'Yggdrasil' reference
midgard/thor.py:20 in function thor.Thor.strike:
    PR01 Parameters {'mjolnir'} not documented
Errors found in 3 out of 9 objects checked.
```

!!! note "Imports ahead"

    For accurate validation, ensure that your `sys.path` contains all relevant paths, that all necessary dependencies are installed, and that resource-intensive code is confined within the `if __name__ == "__main__"` block.

You can also validate standalone modules:

<!-- termynal -->

```bash
$ numpydoclint -vv midgard/thor.py
midgard/thor.py:20 in function thor.Thor.strike:
    PR01 Parameters {'mjolnir'} not documented
Errors found in 1 out of 3 objects checked.
```

!!! tip

    Package and module paths can be mixed within a single run.

## Verbosity

By default, Numpydoclint only prints the number of errors found. You can also set the verbosity level to suit your needs: a single verbosity flag shows information about the object and the corresponding error codes, while a double verbosity flag also adds comments:

<!-- termynal -->

```bash
$ numpydoclint asgard
Errors found in 3 out of 6 objects checked.
$ numpydoclint asgard -v
asgard/loki.py:12 in function asgard.loki.mischief: GL03
asgard/odin.py:10 in type asgard.odin.Allfather: SA04
Errors found in 3 out of 6 objects checked.
$ numpydoclint asgard -vv
asgard/loki.py:12 in function asgard.loki.mischief:
    GL03 Double line break found
asgard/odin.py:10 in type asgard.odin.Allfather:
    SA04 Missing description for See Also 'Yggdrasil' reference
Errors found in 3 out of 6 objects checked.
```

## Filtering Options

Numpydoclint introduces flexible filtering options to tailor the validation process to your needs. These options include global settings such as ignoring certain errors or files, either via the command line or within your [configuration files](complete_reference.md#configuration-files). In addition, Numpydoclint supports special comments for more precise targeting.

### Global Options

These global options allow you to bypass certain [validation checks :octicons-link-external-16:][error-codes] and to exclude files by path or name using regular expressions. See the example below:

```bash
$ numpydoclint asgard \
    --ignore-errors ES01 \ # (1)
    --ignore-paths midgard/loki.py \ # (2)
    --filename-pattern '^(?!__).+.py$' # (3)
```

1. Suppress 'No extended summary found' (`ES01`) errors from the validation process.
2. Exclude the `loki.py` module from validation.
3. Exclude modules starting with a double underscore (`__`) using [regex :octicons-link-external-16:][regex] filename pattern.

!!! note "Filename Pattern"

    The pattern should match only the file name, not the full path. The default pattern matches any file with the `.py` extension.

To learn more about each argument and how to provide arguments through your configuration files, please refer to the appropriate section of our [Complete Reference](complete_reference.md#available-arguments) guide.

### Special Comments

For granular control, numpydoclint provides special comments to ignore certain objects or [error codes :octicons-link-external-16:][error-codes]. Use `numpydoclint: ignore` to omit an object's docstring, and `numpydoclint: ignore-all` to exclude both the object's docstring and all of its child objects.

In addition, errors specific to an object or its child objects can be ignored by appending the appropriate error codes to the directives. Consider the following example:

``` py title="thor.py" hl_lines="1 8"
# numpydoclint: ignore-all GL08,ES01 # (1)
"""Thor, the God of Thunder."""
from jotunheim import Jotun

class Mjolnir:
    """Mjolnir: Thor's fearsome and potent weapon."""

class Thor:  # numpydoclint: ignore # (2)
    """Thor: Norse God of Thunder."""
    
    def __init__(self) -> None: # (3)
        self.strength = float(inf)

    def strike(self, mjolnir: Mjolnir, jotun: Jotun):  # (4)
        """Thor strikes a jotun with Mjolnir.

        Parameters
        ----------
        jotun : Jotun
            A mighty giant.
        """
        print(f"Thor strikes {jotun.name} with Mjolnir!")
```

1. Suppress 'The object does not have a docstring' (`GL08`) and 'No extended summary found' (`ES01`) errors for all objects within this module.
2. Ignore the main docstring of the `Thor` class.
3. All class constructors are always ignored.
4. Note that the `strike` method will not be ignored. To ignore all methods too, use `numpydoclint: ignore-all`.

!!! note

    Place directives on the line of the object definition. For directives at module level, they should appear on the first line or before the first statement in the module.

For more information on special comments, please refer to the relevant section of our [Complete Reference](complete_reference.md#special-comments) guide.

[error-codes]: https://numpydoc.readthedocs.io/en/latest/validation.html#built-in-validation-checks
[regex]: https://docs.python.org/3/library/re.html
