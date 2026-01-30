"""SCANOSS SDK for Software Composition Analysis."""

from .client import Scanoss, ScanossError, ScanProgress, ProgressCallback
from .binary import get_binary_path

__version__ = "2.0.0"
__all__ = [
    "Scanoss",
    "ScanossError",
    "ScanProgress",
    "ProgressCallback",
    "get_binary_path",
    "__version__",
]
