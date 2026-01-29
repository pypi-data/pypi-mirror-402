"""MARC Linting library for Python."""

__version__ = "0.0.3"

from .linter import MarcLint, RecordResult
from .warning import MarcWarning

__all__ = ["MarcLint", "MarcWarning", "RecordResult"]
