"""Exception types for qbepy."""

from __future__ import annotations


class QBEPyError(Exception):
    """Base exception for qbepy errors."""


class CompilationError(QBEPyError):
    """Error during QBE compilation.

    Attributes:
        message: Error message from QBE
        source: The IL source that caused the error (if available)
    """

    def __init__(self, message: str, source: str | None = None):
        self.source = source
        super().__init__(message)
