"""
genericlib.number
=================

Utility functions for identifying and safely converting objects into numeric
types (boolean, integer, float). This module provides consistent parsing logic
for strings, bytes, and native Python types, ensuring predictable behavior
across heterogeneous inputs.
"""

from copy import deepcopy
from typing import Any, Optional, Tuple, Type
import re


def is_boolean(obj: Any, allowed_str: bool = True) -> bool:
    """
    Check whether the given object represents a boolean value.

    Strings such as "true", "false", "0", "1", "+0", "-0", "0.0", "1.0"
    are considered valid boolean representations when `allowed_str` is True.

    Parameters
    ----------
    obj : Any
        The object to check.
    allowed_str : bool, default=True
        Whether to allow string/byte representations of booleans.

    Returns
    -------
    bool
        True if the object can be interpreted as a boolean, False otherwise.
    """
    data = deepcopy(obj)

    if allowed_str and isinstance(data, (str, bytes)):
        text = data if isinstance(data, str) else data.decode("utf-8")
        text = text.strip().lower()
        return bool(re.match(r"^(true|false|[+-]?0(\.0+)?|[+]?1(\.0+)?)$", text))

    if isinstance(data, (int, float, bool)):
        return data in (0, 1)

    return False


def is_integer(obj: Any, allowed_str: bool = True) -> bool:
    """
    Check whether the given object represents an integer value.

    Strings such as "42", "-7", "true", "false" are considered valid
    integer representations when `allowed_str` is True.

    Parameters
    ----------
    obj : Any
        The object to check.
    allowed_str : bool, default=True
        Whether to allow string/byte representations of integers.

    Returns
    -------
    bool
        True if the object can be interpreted as an integer, False otherwise.
    """
    data = deepcopy(obj)

    if allowed_str and isinstance(data, (str, bytes)):
        text = data if isinstance(data, str) else data.decode("utf-8")
        text = text.strip().lower()
        return bool(re.match(r"^(true|false|[+-]?\d+)$", text))

    return isinstance(data, (int, bool))


def is_float(obj: Any, allowed_str: bool = True) -> bool:
    """
    Check whether the given object represents a floating-point value.

    Strings such as "3.14", "-0.5", "42", "true", "false" are considered valid
    float representations when `allowed_str` is True.

    Parameters
    ----------
    obj : Any
        The object to check.
    allowed_str : bool, default=True
        Whether to allow string/byte representations of floats.

    Returns
    -------
    bool
        True if the object can be interpreted as a float, False otherwise.
    """
    data = deepcopy(obj)

    if allowed_str and isinstance(data, (str, bytes)):
        text = data if isinstance(data, str) else data.decode("utf-8")
        text = text.strip().lower()
        return bool(re.match(r"^(true|false|[+-]?((\d+\.?\d*)|(\d*\.?\d+)))$", text))

    return isinstance(data, (int, float, bool))


def is_number(obj: Any, allowed_str: bool = True) -> bool:
    """
    Check whether the given object represents any numeric type (boolean, integer, or float).

    Parameters
    ----------
    obj : Any
        The object to check.
    allowed_str : bool, default=True
        Whether to allow string/byte representations of numbers.

    Returns
    -------
    bool
        True if the object can be interpreted as a number, False otherwise.
    """
    return (
        is_boolean(obj, allowed_str=allowed_str)
        or is_integer(obj, allowed_str=allowed_str)
        or is_float(obj, allowed_str=allowed_str)
    )


def try_to_get_number(
    obj: Any, return_type: Optional[Type] = None, allowed_str: bool = True
) -> Tuple[bool, Any]:
    """
    Attempt to convert an object into a numeric or boolean value.

    Strings and bytes are parsed into int, float, or bool when possible.
    If conversion succeeds, the result is optionally cast to `return_type`.

    Parameters
    ----------
    obj : Any
        The object to attempt conversion on. Can be str, bytes, int, float, or bool.
    return_type : type, optional
        Desired return type (int, float, or bool). If None, the natural type is preserved.
    allowed_str : bool, default=True
        Whether to allow string/byte representations of numbers.

    Returns
    -------
    tuple of (bool, Any)
        - bool: True if conversion succeeded, False otherwise.
        - Any: Converted value if successful, otherwise the original object.
    """

    def cast_to_type(value: Any, target_type: Optional[Type]) -> Any:
        """Cast value to the requested type if valid, otherwise return unchanged."""
        if target_type in (int, float, bool):
            return target_type(value)
        return value

    data = deepcopy(obj)

    if allowed_str and isinstance(data, (str, bytes)):
        text = data if isinstance(data, str) else data.decode("utf-8")
        text = text.strip().lower()

        if text in ("true", "false"):
            return True, cast_to_type(text == "true", return_type)
        if re.match(r"^[+-]?\d+$", text):
            return True, cast_to_type(int(text), return_type)
        if re.match(r"^[+-]?((\d+\.?\d*)|(\d*\.?\d+))$", text):
            return True, cast_to_type(float(text), return_type)

    if isinstance(data, (int, float, bool)):
        return True, cast_to_type(data, return_type)

    return False, obj