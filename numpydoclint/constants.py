# numpydoclint: ignore=ES01
"""Numpydoclint constants."""
import importlib.metadata

PROJECT_NAME = "numpydoclint"
IGNORE_DIRECTIVE = r"numpydoclint:\s*ignore[\s=]*(\w+(?:,\w+)*)?"
R_IGNORE_DIRECTIVE = r"numpydoclint:\s*ignore-all[\s=]*(\w+(?:,\w+)*)?"
DEFAULT_FILENAME_PATTERN = "^.+\\.py$"
__version__ = importlib.metadata.version("numpydoc-linter")
