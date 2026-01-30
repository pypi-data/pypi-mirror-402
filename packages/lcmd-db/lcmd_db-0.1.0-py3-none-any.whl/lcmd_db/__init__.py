"""LCMD-DB - Python client for the LCMD molecular database."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("lcmd-db")
except PackageNotFoundError:
    __version__ = "0.0.0"

from .client import clear_cache, load_dataset
from .exceptions import DatasetNotFoundError, DownloadError, LCMDError
from .types import DataFormat

__all__ = [
    "__version__",
    "load_dataset",
    "clear_cache",
    "DataFormat",
    "LCMDError",
    "DatasetNotFoundError",
    "DownloadError",
]
