import logging
import os
from pathlib import Path

TRACE = 5
DEBUG = logging.DEBUG
INFO = logging.INFO
WARNING = logging.WARNING
ERROR = logging.ERROR
FATAL = logging.FATAL
CRITICAL = logging.CRITICAL

TIME_FORMAT_WITH_DATE = "%Y-%m-%d %H:%M:%S.%.3f"
TIME_FORMAT_WITHOUT_DATE = "%H:%M:%S.%.3f"

LOG_FORMAT = (
    "[%(levelname)s] %(asctime)s - %(name)s - %(pathname)s:%(lineno)d - %(message)s"
)

BASE_DIR = Path(os.path.dirname(__file__))
