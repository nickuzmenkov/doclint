"""Numpydoclint utilities.

Auxiliary functions for parsing and logging.
"""
import configparser
import logging
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Set, Union

import toml

from numpydoclint.constants import PROJECT_NAME


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """Get logger.

    Return configured logger object.

    Parameters
    ----------
    name : str, optional
        Name of the logger. If None, defaults to `__name__`.

    Returns
    -------
    Logger
        Configured logger.
    """
    return logging.getLogger(name=name or __name__)


def get_first(iterable: Iterable[Any], default: Any = None) -> Any:  # numpydoclint: ignore=ES01
    """The first item that evaluates to True, the default value, or None.

    Parameters
    ----------
    iterable : iterable
        Iterable of objects.
    default : any, optional
        Default value to return if all values are evaluated to False.
        Default is None.

    Returns
    -------
    any
        The first item that evaluates to True, the default value, or None.
    """
    return next((x for x in iterable if x), default)


def parse_set(str_or_list: Union[str, List[str]]) -> Set[str]:  # numpydoclint: ignore=ES01
    """Parse set from string with comma-separated values or list of strings.

    Parameters
    ----------
    str_or_list : str or list of str
        String with comma-separated values or set of strings to parse.
        Whitespace-only substrings and empty items of the list are dropped.

    Returns
    -------
    set of str
        Set of strings.
    """
    if isinstance(str_or_list, str):
        if not str_or_list:
            return set()
        str_or_list = str_or_list.split(",")
    return {x.strip() for x in str_or_list if x.strip()}


def parse_bool(str_or_bool: Union[str, bool]) -> bool:  # numpydoclint: ignore=ES01
    """Parse boolean value from string.

    Parameters
    ----------
    str_or_bool : str or bool
        String or bool to parse.

    Returns
    -------
    bool
        Parsed value.
    """
    if isinstance(str_or_bool, bool):
        return str_or_bool
    str_ = str_or_bool.lower().strip()
    return str_ == "true"


EMPTY_CONFIG = {
    "ignore_errors": "",
    "ignore_paths": "",
    "ignore_hidden": "",
    "filename_pattern": "",
}
logger = get_logger()


def parse_setup_cfg(config_dir: str = ".") -> Dict[str, str]:
    """Parse CLI configuration from `setup.py` file.

    The file is searched for in the current directory by default. The `config_dir` parameter is defined for testing purposes only.

    Parameters
    ----------
    config_dir : str, default "."
        Directory to search config within. Only for testing.
        Default is the current working directory.

    Returns
    -------
    dict of str
        Parsed configuration.
    """
    parsed_config = EMPTY_CONFIG.copy()
    config_file = Path(config_dir, "setup.cfg")

    if not config_file.exists():
        logger.debug("Config file 'setup.cfg' not found.")
        return parsed_config
    try:
        config = configparser.ConfigParser()
        config.read(config_file)

        if config.has_section(PROJECT_NAME):
            parsed_config["ignore_errors"] = config.get(PROJECT_NAME, "ignore_errors", fallback="")
            parsed_config["ignore_paths"] = config.get(PROJECT_NAME, "ignore_paths", fallback="")
            parsed_config["ignore_hidden"] = config.get(PROJECT_NAME, "ignore_hidden", fallback="")
            parsed_config["filename_pattern"] = config.get(PROJECT_NAME, "filename_pattern", fallback="")
        else:
            logger.debug("Config file 'setup.cfg' exists but has no '[%s]' section.", PROJECT_NAME)
    except Exception as exception:  # pylint: disable=broad-exception-caught
        logger.debug("Config file 'setup.cfg' was not parsed due to exception: %s.", exception)
    finally:
        return parsed_config  # pylint: disable=lost-exception


def parse_pyproject_toml(config_dir: str = ".") -> Dict[str, str]:
    """Parse CLI configuration from `pyproject.toml` file.

    The file is searched for in the current directory by default. The `config_dir` parameter is defined for testing purposes only.

    Parameters
    ----------
    config_dir : str, default '.'
        Directory to search config within. Only for testing.
        Default is the current working directory.

    Returns
    -------
    dict of str
        Parsed configuration.
    """
    parsed_config = EMPTY_CONFIG.copy()
    config_file = Path(config_dir, "pyproject.toml")

    if not config_file.exists():
        logger.debug("Config file 'pyproject.toml' not found.")
        return parsed_config
    try:
        config = toml.load(config_file).get("tool", {}).get(PROJECT_NAME)

        if config is not None:
            parsed_config["ignore_errors"] = config.get("ignore_errors", "")
            parsed_config["ignore_paths"] = config.get("ignore_paths", "")
            parsed_config["ignore_hidden"] = config.get("ignore_hidden", "")
            parsed_config["filename_pattern"] = config.get("filename_pattern", "")
        else:
            logger.debug("Config file 'pyproject.toml' exists but has no '[tool.%s]' section.", PROJECT_NAME)
    except Exception as exception:  # pylint: disable=broad-exception-caught
        logger.debug("Config file 'pyproject.toml' was not parsed due to exception: %s.", exception)
    finally:
        return parsed_config  # pylint: disable=lost-exception
