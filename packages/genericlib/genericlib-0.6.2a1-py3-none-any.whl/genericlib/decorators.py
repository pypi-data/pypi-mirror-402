"""
genericlib.decorators
=====================

Utility decorators for text normalization, formatting, and output consistency.

This module provides reusable decorators that simplify common text‑processing
tasks across the codebase. They ensure that functions receive or return
normalized strings, making downstream parsing and testing more reliable.
"""

import functools
from textwrap import dedent
from typing import Callable, Any


def normalize_return_output_text(func: Callable) -> Callable:
    """
    Decorator to normalize the return value of a function.

    This decorator ensures that the output of the wrapped function is
    consistently formatted as a string:

    - Strings are unindented and stripped of leading/trailing whitespace.
    - Bytes are decoded as UTF-8, then unindented and stripped.
    - Lists or tuples are joined into a newline-separated string,
      then unindented and stripped.
    - Other types are converted to string, then unindented and stripped.

    Parameters
    ----------
    func : Callable
        The function to wrap.

    Returns
    -------
    Callable
        Wrapped function that returns a normalized string.
    """
    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> str:
        output = func(*args, **kwargs)

        if isinstance(output, str):
            return dedent(output).strip()
        if isinstance(output, bytes):
            return dedent(output.decode("utf-8")).strip()
        if isinstance(output, (list, tuple)):
            return dedent("\n".join(str(item) for item in output)).strip()
        return dedent(str(output)).strip()

    return wrapper


def try_and_catch(handler: Callable[[Exception], Any] = None) -> Callable:
    """Decorator to catch exceptions and optionally handle them.

    Parameters
    ----------
    handler : Callable[[Exception], Any], optional
        A function that takes the raised exception and returns a value.
        If not provided, the exception is re-raised.

    Returns
    -------
    Callable
        Wrapped function with exception handling.
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return func(*args, **kwargs)
            except Exception as exc:
                if handler:
                    return handler(exc)
                raise exc
        return wrapper
    return decorator
