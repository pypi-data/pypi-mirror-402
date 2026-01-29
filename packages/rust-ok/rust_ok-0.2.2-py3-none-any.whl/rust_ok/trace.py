"""Helpers for formatting chained exceptions."""

from __future__ import annotations

from collections.abc import Iterator
from io import StringIO


def iter_causes(exc: BaseException) -> Iterator[BaseException]:
    """Yield an exception and its chained causes/contexts in order."""
    current: BaseException | None = exc
    while current is not None:
        yield current
        if current.__cause__ is not None:
            current = current.__cause__
        elif current.__context__ is not None and not current.__suppress_context__:
            current = current.__context__
        else:
            current = None


def format_exception_chain(exc: BaseException) -> str:
    """Return a readable string for an exception and its chain."""
    from traceback import format_exception  # lazy import keeps module light

    buffer = StringIO()
    first = True
    for cause in iter_causes(exc):
        if not first:
            buffer.write("\n\n")
        first = False
        chunk = "".join(
            format_exception(
                cause.__class__,
                cause,
                cause.__traceback__,
            )
        ).rstrip()
        buffer.write(chunk)
    return buffer.getvalue()
