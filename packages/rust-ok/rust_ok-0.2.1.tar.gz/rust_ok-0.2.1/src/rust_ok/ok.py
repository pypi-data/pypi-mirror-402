"""Implementation of the Ok variant."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, Literal, Never, TypeVar, cast, overload

from .exceptions import IsNotError, UnwrapError
from .result import Result

T_co = TypeVar("T_co", covariant=True)
E_co = TypeVar("E_co", covariant=True)
U = TypeVar("U")
F = TypeVar("F")


class Ok(Result[T_co, E_co]):
    """Success result containing a value."""

    __slots__ = ("value",)
    __match_args__ = ("value",)

    value: T_co

    @overload
    def __init__(self: Ok[T_co, Never], value: T_co) -> None: ...

    @overload
    def __init__(self: Ok[Any, Any]) -> None: ...

    @overload
    def __init__(self: Ok[None, Any], value: Literal[None]) -> None: ...

    def __init__(self, value: T_co | None = None) -> None:
        self.value = value  # type: ignore[assignment]

    def __repr__(self) -> str:
        return f"Ok({self.value!r})"

    def __str__(self) -> str:
        return f"Ok({self.value})"

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Ok):
            return bool(self.value == other.value)
        return False

    def __hash__(self) -> int:
        return hash(("Ok", self.value))

    def __bool__(self) -> bool:
        return True

    def unwrap(self) -> T_co:
        return self.value

    def unwrap_err(self) -> E_co:
        raise UnwrapError("Called unwrap_err on Ok")

    def unwrap_or(self, default: T_co | Any) -> T_co:
        return self.value

    def unwrap_or_else(self, func: Callable[[Any], T_co]) -> T_co:
        """Return value; func is never called in Ok."""
        return self.value

    def expect(self, msg: str) -> T_co:
        return self.value

    def is_ok(self) -> bool:
        return True

    def is_err(self) -> bool:
        return False

    def map(self, func: Callable[[Any], U]) -> Result[U, E_co]:
        return Ok(func(self.value))

    def map_err(self, func: Callable[[Any], F]) -> Result[T_co, F]:
        """Phantom type: func is never called in Ok."""
        return cast(Result[T_co, F], Ok(self.value))

    def and_then(self, func: Callable[[Any], Result[U, E_co]]) -> Result[U, E_co]:
        return func(self.value)

    def or_else(self, func: Callable[[Any], Result[T_co, F]]) -> Result[T_co, F]:
        """Phantom type: func is never called in Ok."""
        return cast(Result[T_co, F], Ok(self.value))

    def ok(self) -> T_co:
        return self.value

    def err(self) -> E_co:
        raise IsNotError

    def unwrap_or_raise(
        self,
        exc_type: type[BaseException] = Exception,
        context: str | None = None,
    ) -> T_co:
        return self.value
