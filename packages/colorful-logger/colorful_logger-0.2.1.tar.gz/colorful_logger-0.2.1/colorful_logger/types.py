from logging import LogRecord
from pathlib import Path
from typing import Any

StrPath = str | Path


class Record(LogRecord):
    kwargs: dict[str, Any] = {}
