"""Implementation of the Err variant."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, Never, TypeVar, cast, overload

from .exceptions import UnwrapError
from .result import Result

T_co = TypeVar("T_co", covariant=True)
E_co = TypeVar("E_co", covariant=True)
U = TypeVar("U")
F = TypeVar("F")


class Err(Result[T_co, E_co]):
    """Error result containing an error value."""

    __slots__ = ("_error_value",)
    __match_args__ = ("error",)

    @overload
    def __init__(self: Err[Never, E_co], error: E_co) -> None: ...

    @overload
    def __init__(self: Err[Any, Any], error: Any) -> None: ...

    def __init__(self, error: E_co | Any) -> None:
        self._error_value = error

    def __repr__(self) -> str:
        return f"Err({self._error_value!r})"

    def __str__(self) -> str:
        return f"Err({self._error_value})"

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Err):
            return bool(self._error_value == other._error_value)
        return False

    def __hash__(self) -> int:
        return hash(("Err", self._error_value))

    def __bool__(self) -> bool:
        return False

    def unwrap(self) -> T_co:
        raise UnwrapError(f"Called unwrap on Err: {self._error_value}")

    def unwrap_err(self) -> E_co:
        return self._error_value

    def unwrap_or(self, default: T_co | Any) -> T_co:
        return default

    def unwrap_or_else(self, func: Callable[[Any], T_co]) -> T_co:
        return func(self._error_value)

    def expect(self, msg: str) -> T_co:
        raise UnwrapError(f"{msg}: {self._error_value}")

    def is_ok(self) -> bool:
        return False

    def is_err(self) -> bool:
        return True

    def map(self, func: Callable[[Any], U]) -> Result[U, E_co]:
        """Return Err; func is never called."""
        return cast(Result[U, E_co], Err(self._error_value))

    def map_err(self, func: Callable[[Any], F]) -> Result[T_co, F]:
        return cast(Result[T_co, F], Err(func(self._error_value)))

    def and_then(self, func: Callable[[Any], Result[U, E_co]]) -> Result[U, E_co]:
        """Return Err; func is never called."""
        return cast(Result[U, E_co], Err(self._error_value))

    def or_else(self, func: Callable[[Any], Result[T_co, F]]) -> Result[T_co, F]:
        return func(self._error_value)

    def ok(self) -> T_co | None:
        return None

    def err(self) -> E_co:
        return self._error_value

    def unwrap_or_raise(
        self,
        exc_type: type[BaseException] = Exception,
        context: str | None = None,
    ) -> T_co:
        payload = self._error_value
        msg = context if context is not None else str(payload)

        if isinstance(payload, BaseException):
            raise exc_type(msg) from payload

        raise exc_type(f"{msg}: {payload!r}")
