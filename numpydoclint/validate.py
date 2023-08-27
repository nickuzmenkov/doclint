"""Numpydoclint validate.

Numpydoclint is a linter for [Numpy style](https://numpydoc.readthedocs.io/en/latest/format.html) docstrings based on the
[numpydoc.validate](https://github.com/numpy/numpydoc/) module. Basic usage examples, as well as more advanced usage scenarios are covered
in detail in the [Official Documentation](https://nickuzmenkov.github.io/numpydoclint/).
"""
from pathlib import Path
from typing import Any, Dict, Iterable, Optional, Set, TypeVar, Union

import numpydoc.validate

from numpydoclint.introspection import Introspector

StrOrPath = TypeVar("StrOrPath", bound=Union[str, Path])


def validate(
    paths: Union[StrOrPath, Iterable[StrOrPath]],
    ignore_errors: Optional[Set[str]] = None,
    ignore_paths: Optional[Set[StrOrPath]] = None,
    ignore_hidden: bool = False,
    filename_pattern: Optional[str] = None,
) -> Dict[str, Dict[str, Any]]:
    """Recursively validate docstrings of functions, classes, and methods under given paths.

    Basic usage examples, as well as more advanced usage scenarios are covered in detail in the
    [Official Documentation](https://nickuzmenkov.github.io/numpydoclint/).

    Parameters
    ----------
    paths : str, Path, or iterable
        One or more paths to be validated. Paths can be directories or modules. If the path is a directory, all modules will be searched
        `filename_pattern`. All paths must be in your `sys.path`. You must have all dependencies installed, because `numpydoc.validate` used
        under the hood imports your module for validation.
    ignore_errors : set of str, optional
        Set of error codes to ignore (for example, `{"ES01", "GL08"}`). See the Numpydoc documentation for a complete reference.
    ignore_paths : set of str or Path, optional
        Set of paths to ignore. Can be directories or files. If the path is a directory, all files in that directory will be ignored.
        If you need to ignore specific patterns in filenames, consider using `filename_pattern` instead.
    ignore_hidden : bool, default False
        Whether to ignore hidden objects. Hidden objects are objects whose names begin with an underscore (`_`). Note that this includes all
        dunder methods of the classes, but not hidden modules. The default is False.
    filename_pattern : str, optional
        Filename pattern to include. Note that this is not a wildcard but a regex pattern, so for example `*.py` will not compile.
        The default is any file with a `.py` extension.

    Returns
    -------
    dict
        Validation report, where each key is the reference to the object being validated, and each value is the object's `numpydoc.validate`
        report.

    Notes
    -----
    The validation report has an additional `link` field that `numpydoc.validate` does not provide. This link is the file path plus the
    line number and becomes clickable in most IDEs when printed to the console.

    All paths must be in your `sys.path`. You must have all dependencies installed, because `numpydoc.validate` used under the hood imports
    your module for validation.
    """
    processed_paths = {Path(paths)} if isinstance(paths, (Path, str)) else {Path(x) for x in paths}  # type: ignore
    processed_ignore_paths = {Path(x) for x in ignore_paths or set()}

    introspector = Introspector(
        ignore_errors=ignore_errors,
        ignore_paths=processed_ignore_paths,
        ignore_hidden=ignore_hidden,
        filename_pattern=filename_pattern,
    )
    object_infos = introspector(paths=processed_paths)

    report = {}

    for object_info in object_infos:
        result = numpydoc.validate.validate(object_info.name)
        result["errors"] = [x for x in result["errors"] if x[0] not in object_info.ignore_errors]
        result["link"] = object_info.link
        report[object_info.name] = result

    return report
