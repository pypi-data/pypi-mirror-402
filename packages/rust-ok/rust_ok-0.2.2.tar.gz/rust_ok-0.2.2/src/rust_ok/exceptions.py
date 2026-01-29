"""Custom exceptions for rust-ok."""


class RustOkError(Exception):
    """Base exception for all rust-ok errors."""


class UnwrapError(RustOkError):
    """Raised when accessing an Ok/Err value in an invalid way."""


class IsNotError(RustOkError):
    """Raised when attempting to retrieve an error from an Ok result."""
