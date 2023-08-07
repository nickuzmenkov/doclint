"""Utilities for testing modules."""
import random
import uuid
from logging import LogRecord
from typing import List, Optional

import pytest


def get_name(prefix: str = "", extension: str = "") -> str:
    """Return random name for a file or directory."""
    # cut UUID string before the first dash
    name = str(uuid.uuid4())[:8]
    return f"{prefix}{name}{extension}"


def get_number(low: Optional[int] = None, high: Optional[int] = None) -> int:
    """Return random number."""
    low = low or 1
    high = high or 10_000
    return random.randint(a=low, b=high)


def get_log_records(caplog: pytest.LogCaptureFixture, level: int, func_name: Optional[str] = None) -> List[LogRecord]:
    """Return log records filtered by level and function name."""
    if func_name is None:
        records = caplog.records
    else:
        records = [x for x in caplog.records if x.funcName == func_name]
    return [x for x in records if x.levelno == level]
