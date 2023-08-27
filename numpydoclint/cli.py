"""Numpydoclint CLI.

Numpydoclint is a linter for [Numpy style](https://numpydoc.readthedocs.io/en/latest/format.html) docstrings based on the
[numpydoc.validate](https://github.com/numpy/numpydoc/) module. Basic usage examples, as well as more advanced usage scenarios are covered
in detail in the [Official Documentation](https://nickuzmenkov.github.io/numpydoclint/).
"""
from pathlib import Path
from typing import Any, Dict, Tuple

import click

import numpydoclint.validate
from numpydoclint.constants import __version__
from numpydoclint.utils import get_first, get_logger, parse_bool, parse_pyproject_toml, parse_set, parse_setup_cfg

logger = get_logger()


@click.command(
    context_settings={"help_option_names": ["-h", "--help"]},
    help="""Numpydoclint is a linter for Numpy style docstrings.

    Specify one or more paths to be validated. Paths can be directories or modules. If the path is a directory, all modules will be searched
    `filename_pattern`. All paths must be in your `sys.path`. You must have all dependencies installed, because `numpydoc.validate` used
    under the hood imports your module for validation.""",
)
@click.version_option(__version__)
@click.argument("paths", nargs=-1)
@click.option(
    "-e",
    "--ignore-errors",
    "ignore_errors_str",
    default="",
    show_default=False,
    help="""Comma-separated list of error codes to ignore (for example, 'ES01,GL08'). See the Numpydoc documentation for a complete
    reference.""",
)
@click.option(
    "-p",
    "--ignore-paths",
    "ignore_paths_str",
    default="",
    show_default=False,
    help="""Comma-separated list of paths to ignore. Can be directories or files. If the path is a directory, all files in that directory
    will be ignored. If you need to ignore specific patterns in filenames, consider using `filename_pattern` instead.""",
)
@click.option(
    "-h",
    "--ignore-hidden",
    "ignore_hidden",
    is_flag=True,
    default=False,
    show_default=False,
    help="""Whether to ignore hidden objects. Hidden objects are objects whose names begin with an underscore (`_`). Note that this includes
    all dunder methods of the classes, but not hidden modules. The default is False.""",
)
@click.option(
    "-f",
    "--filename-pattern",
    "filename_pattern",
    default="",
    show_default=False,
    help="""Filename pattern to include. Note that this is not a wildcard but a regex pattern, so for example `*.py` will not compile.
    The default is any file with a `.py` extension.""",
)
@click.option(
    "-v",
    "--verbose",
    "verbose",
    default=0,
    count=True,
    show_default=False,
    help="""Count argument representing the verbosity level of the linter output. Possible values are:

    - no flag (default): print only the number of errors found.

    - `-v`: show information about the objects and the corresponding error codes.

    - `-vv`: also add comments for each error.""",
)
def validate(  # numpydoclint: ignore
    paths: Tuple[str, ...],
    ignore_errors_str: str,
    ignore_paths_str: str,
    ignore_hidden: bool,
    filename_pattern: str,
    verbose: int,
) -> None:
    """Recursively validate docstrings of functions, classes, and methods under given paths.

    Basic usage examples, as well as more advanced usage scenarios are covered in detail in the
    [Official Documentation](https://nickuzmenkov.github.io/numpydoclint/).

    Parameters
    ----------
    paths : tuple of str
        One or more paths to be validated. Paths can be directories or modules. If the path is a directory, all modules will be searched
        `filename_pattern`. All paths must be in your `sys.path`. You must have all dependencies installed, because `numpydoc.validate` used
        under the hood imports your module for validation.
    ignore_errors_str : str
        Comma-separated list of error codes to ignore (for example, 'ES01,GL08'). See the Numpydoc documentation for a complete reference.
    ignore_paths_str : str
        Comma-separated list of paths to ignore. Can be directories or files. If the path is a directory, all files in that directory
        will be ignored. If you need to ignore specific patterns in filenames, consider using `filename_pattern` instead.
    filename_pattern : str
        Filename pattern to include. Note that this is not a wildcard but a regex pattern, so for example `*.py` will not compile.
        The default is any file with a `.py` extension.
    ignore_hidden : bool, default False
        Whether to ignore hidden objects. Hidden objects are objects whose names begin with an underscore (`_`). Note that this includes all
        dunder methods of the classes, but not hidden modules. The default is False.
    verbose : int
        Count argument representing the verbosity level of the linter output. Possible values are:

        - no flag (default): print only the number of errors found.
        - `-v`: show information about the objects and the corresponding error codes.
        - `-vv`: also add comments for each error.

    Notes
    -----
    All paths must be in your `sys.path`. You must have all dependencies installed, because `numpydoc.validate` used under the hood imports
    your module for validation.
    """
    if not paths:
        raise click.UsageError("You must provide at least one source to validate.")

    pyproject_toml_config = parse_pyproject_toml()
    setup_cfg_config = parse_setup_cfg()

    ignore_errors = parse_set(
        get_first((ignore_errors_str, pyproject_toml_config["ignore_errors"], setup_cfg_config["ignore_errors"]), default="")
    )
    ignore_paths = {
        Path(x)
        for x in parse_set(
            get_first((ignore_paths_str, pyproject_toml_config["ignore_paths"], setup_cfg_config["ignore_paths"]), default="")
        )
    }
    ignore_hidden = parse_bool(
        get_first((ignore_hidden, pyproject_toml_config["ignore_hidden"], setup_cfg_config["ignore_hidden"]), default="")
    )
    filename_pattern = get_first(
        (filename_pattern, pyproject_toml_config["filename_pattern"], setup_cfg_config["filename_pattern"]), default=None
    )

    report = numpydoclint.validate(  # type: ignore
        paths=paths,
        ignore_errors=ignore_errors,
        ignore_paths=ignore_paths,
        filename_pattern=filename_pattern,
        ignore_hidden=ignore_hidden,
    )

    if report and any(x["errors"] for x in report.values()):
        echo_errors(report=report, verbose=verbose)
        raise click.ClickException("numpydoclint validation failed.")

    echo_success(report=report)


def echo_errors(report: Dict[str, Dict[str, Any]], verbose: int) -> None:  # numpydoclint: ignore=ES01
    """Echo error report to stderr.

    Parameters
    ----------
    report : dict
        Validation report.
    verbose : int
        Verbose level.
    """
    for name, result in report.items():
        if not result["errors"] or verbose == 0:
            continue

        reference = f"{result['link']} in {result['type']} {click.style(name, fg='magenta')}: "
        if verbose >= 2:
            details = "\n" + "\n".join(click.style(f"        {x[0]} ", fg="red") + x[1] for x in result["errors"])
        else:
            details = ", ".join(click.style(x[0], fg="red") for x in result["errors"])

        message = reference + details
        click.echo(message, nl=True, err=True)
    errors = sum(1 for x in report.values() if x["errors"])
    click.echo(
        click.style(f"Errors found in {errors} out of {len(report)} objects checked.", fg="red"),
        err=True,
    )


def echo_success(report: Dict[str, Dict[str, Any]]) -> None:  # numpydoclint: ignore=ES01
    """Echo success message to stdout.

    Parameters
    ----------
    report : dict
        Validation report.
    """
    click.echo(click.style(f"Success: No errors found in {len(report)} objects checked.", fg="green"), err=False)
