# Complete Reference

This guide provides detailed information about all configuration options available in Numpydoclint.

## Command Line  Arguments

This section lists all the arguments available from the command line.

### `PATHS`

Specify one or more paths to be validated. Paths can be directories or modules. If the path is a directory, all modules will be searched `filename_pattern`. All paths must be in your `sys.path`. You must have all dependencies installed, because [`numpydoc.validate` :octicons-link-external-16:][numpydoc-validate] used under the hood imports your module for validation.

### `-e`, `--ignore_errors`

Comma-separated set of error codes to ignore (for example, `ES01,GL08`). See the [Numpydoc documentation :octicons-link-external-16:][error-codes] for a complete  reference.

### `-p`, `--ignore_paths`

Comma-separated list of paths to ignore. Can be directories or files. If the path is a directory, all files in that directory will be ignored. If you need to ignore specific patterns in filenames, consider using `filename_pattern` instead.

??? example

    Suppose you have the following file structure:

    ```
    asgard/
    ├── __init__.py
    ├── bifrost.py
    ├── odin.py
    ├── loki.py
    ├── valhalla/
    │   ├── __init__.py
    │   ├── einherjar.py
    │   ├── valkyries.py
    │   └── feast.py
    ```

    The following command will only validate the `asgard/bifrost.py`, `asgard/odin.py`, as well as both `__init__.py` modules:

    ```bash
    $ numpydoclint asgard --ignore_paths=asgard/loki.py,asgard/valhalla
    ```

### `-f`, `--filename_pattern`

Filename pattern to include. Note that this is not a wildcard but a regex pattern, so for example `*.py` will not compile. The default is any file with a `.py` extension.

??? example
    
    Suppose you have the following file structure:

    ```
    asgard/
    ├── __init__.py
    ├── bifrost.py
    ├── odin.py
    ├── loki.py
    ├── valhalla/
    │   ├── __init__.py
    │   ├── einherjar.py
    │   ├── valkyries.py
    │   └── feast.py
    ```

    The following command will skip both `__init__.py` modules:

    ```bash
    $ numpydoclint asgard --filename_pattern='^(?!__).+.py$'
    ```

    While the following command will only match filenames ending in `st.py`, namely, `asgard/bifrost.py` and `asgard/valhalla/feast.py`:
    
    ```bash
    $ numpydoclint asgard --filename_pattern='^.*st.py$'
    ```

### `-v`, `--verbose`

Count argument representing the verbosity level of the linter output. Possible values are:

- no flag (default): print only the number of errors found.
- `-v`: show information about the objects and the corresponding error codes.
- `-vv`: also add comments for each error.

See the [Verbosity](quickstart.md#verbosity) section for an interactive example.

## Special Comments

This section outlines special comments that can be used to ignore certain objects or certain errors only for those objects. See the [Special Comments](quickstart.md#special-comments) section in the [Quickstart](quickstart.md) guide for a basic example.

There are basically two types of special comment: regular and recursive. The former applies only to an object itself (e.g. a class or a module), while the latter also applies to all child objects (i.e. all methods in a class, or all functions and classes in a module).

!!! note
    
    As functions do not have child objects, they can be ignored by both.

To ignore specific errors for these objects only, you can also add a list of codes to ignore to one of the comments to ignore errors for the object, or to ignore them for the object and all child objects. Let's look at some examples.

### `numpydoclint: ignore`

This tells Numpydoclint to ignore the object or, which is the same, to ignore all errors for the object. To ignore some specific errors for this object instead, you should add a comma-separated list of [error codes :octicons-link-external-16:][error-codes] after the directive, followed by a space or an equal sign.

!!! example
    
    Examples of valid comments are:

    - `numpydoclint: ignore` (ignore all errors)
    - `numpydoclint: ignore=RT01` (ignore 'No Returns section found' error)
    - `numpydoclint: ignore GL01,ES01` (you can use a space instead of an equal sign)
    - `numpydoclint: ignore = EX01, PR01, SS01` (you can add extra spaces)

### `numpydoclint: ignore-all`

This tells Numpydoclint to ignore the object and all its children: all methods if it's a class, and all classes and functions if it's a module. To ignore some specific errors for this object instead, you should also add a comma-separated list of [error codes :octicons-link-external-16:][error-codes] after the directive, followed by a space or an equal sign.

See the example [above](#numpydoclint-ignore) for a list of legal commands.

## Configuration Files

Numpydoclint allows flexible configuration via the command line and configuration files. These are processed in a certain order, from highest to lowest:

- Command line arguments: All arguments given directly on the command line have the highest priority. These arguments override any conflicting settings in the configuration files.
- `pyproject.toml`: If there is a `pyproject.toml` file in the current working directory, and it has a `[tool.numpydoclint]` section defined, Numpydoclint will use the settings from that section.
- `setup.cfg`: If there is a `setup.cfg` file in the current working directory, and it has a `[numpydoclint]` section defined in it, Numpydoclint will use the settings from that section.

??? example

    Suppose you have the following configuration files in your current project directory:

    ```toml title="pyproject.toml"
    [tool.numpydoclint]
    ignore_errors = ["ES01", "EX01"]
    ```

    ```ini title="setup.cfg"
    [numpydoclint]
    ignore_errors = RT01, GL08
    filename_pattern = '^(?!__).+.py$'
    ```
    
    Running `numpydoclint asgard/` will use the filename pattern specified in the `setup.cfg`, while the ignored errors from `setup.cfg` will be overridden by the values in the `pyproject.toml` file.

[numpydoc-validate]: https://numpydoc.readthedocs.io/en/latest/validation.html
[error-codes]: https://numpydoc.readthedocs.io/en/latest/validation.html#built-in-validation-checks
