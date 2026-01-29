"""Public API for rust-ok."""

from importlib.metadata import version

__version__ = version("rust_ok")

from .err import Err
from .exceptions import IsNotError, RustOkError, UnwrapError
from .guards import is_err, is_ok
from .ok import Ok
from .result import Result
from .trace import format_exception_chain, iter_causes

__all__ = [
    "Err",
    "IsNotError",
    "Ok",
    "Result",
    "RustOkError",
    "UnwrapError",
    "format_exception_chain",
    "iter_causes",
    "is_err",
    "is_ok",
    "__version__",
]
