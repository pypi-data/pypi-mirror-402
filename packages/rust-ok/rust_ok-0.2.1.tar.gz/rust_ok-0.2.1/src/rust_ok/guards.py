"""Type-guard helpers for Result values."""

from __future__ import annotations

from typing import TypeGuard, TypeVar

from .err import Err
from .ok import Ok
from .result import Result

T = TypeVar("T")
E = TypeVar("E")


def is_ok(result: Result[T, E]) -> TypeGuard[Ok[T, E]]:
    """Return True if the result is Ok."""
    return isinstance(result, Ok)


def is_err(result: Result[T, E]) -> TypeGuard[Err[T, E]]:
    """Return True if the result is Err."""
    return isinstance(result, Err)
