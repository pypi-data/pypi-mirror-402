"""Base Result primitives and helpers."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, Generic, TypeVar

# Covariant type variables for Result base type
T_co = TypeVar("T_co", covariant=True)
E_co = TypeVar("E_co", covariant=True)
# TypeVars for transformation method return types
U = TypeVar("U")
F = TypeVar("F")


class Result(Generic[T_co, E_co]):
    """Base type for Ok/Err results."""

    __slots__ = ()

    def unwrap(self) -> T_co:
        """Return the contained value if successful, else raise in subclass."""
        raise NotImplementedError  # pragma: no cover

    def unwrap_err(self) -> E_co:
        """Return the contained error if Err, else raise in subclass."""
        raise NotImplementedError  # pragma: no cover

    def unwrap_or(self, default: T_co | Any) -> T_co:
        """Return the contained value if Ok, otherwise return the default."""
        raise NotImplementedError  # pragma: no cover

    def unwrap_or_else(self, func: Callable[[Any], T_co]) -> T_co:
        """Return the contained value if Ok, otherwise compute a default."""
        raise NotImplementedError  # pragma: no cover

    def expect(self, msg: str) -> T_co:
        """Return the contained value if Ok, otherwise raise with custom message."""
        raise NotImplementedError  # pragma: no cover

    def is_ok(self) -> bool:  # pragma: no cover
        """Return True if this is Ok."""
        from .ok import Ok

        return isinstance(self, Ok)

    def is_err(self) -> bool:  # pragma: no cover
        """Return True if this is Err."""
        from .err import Err

        return isinstance(self, Err)

    def map(self, func: Callable[[Any], U]) -> Result[U, E_co]:
        """Apply func to the contained value if Ok, returning a new Result."""
        raise NotImplementedError  # pragma: no cover

    def map_err(self, func: Callable[[Any], F]) -> Result[T_co, F]:
        """Apply func to the error if Err, returning a new Result."""
        raise NotImplementedError  # pragma: no cover

    def and_then(self, func: Callable[[Any], Result[U, E_co]]) -> Result[U, E_co]:
        """Chain another computation on the contained value if Ok."""
        raise NotImplementedError  # pragma: no cover

    def or_else(self, func: Callable[[Any], Result[T_co, F]]) -> Result[T_co, F]:
        """Handle the error by calling func if Err, returning a new Result."""
        raise NotImplementedError  # pragma: no cover

    def ok(self) -> T_co | None:
        """Return the success value if Ok, otherwise None."""
        raise NotImplementedError  # pragma: no cover

    def err(self) -> E_co:
        """Return the error value if Err, otherwise raise in subclass."""
        raise NotImplementedError  # pragma: no cover

    @property
    def error(self) -> E_co | None:
        """Return the error value if Err, otherwise None."""
        return self.err()

    def unwrap_or_raise(
        self,
        exc_type: type[BaseException] = Exception,
        context: str | None = None,
    ) -> T_co:
        """Return the Ok value or raise `exc_type`."""
        raise NotImplementedError  # pragma: no cover
