"""Core validation functions for ValidX."""

import re
from typing import Any, Optional, Union

# Precompiled regex patterns for better performance
EMAIL_PATTERN = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
URL_PATTERN = re.compile(
    r"^https?://"
    r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|"
    r"localhost|"
    r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"
    r"(?::\d+)?"
    r"(?:/?|[/?]\S+)$",
    re.IGNORECASE,
)


def is_string(value: Any) -> bool:
    """Check if value is a string.

    Args:
        value: The value to check.

    Returns:
        True if value is a string, False otherwise.
    """
    return isinstance(value, str)


def is_integer(value: Any) -> bool:
    """Check if value is an integer (excludes booleans).

    Args:
        value: The value to check.

    Returns:
        True if value is an integer and not a boolean, False otherwise.
    """
    return isinstance(value, int) and not isinstance(value, bool)


def is_float(value: Any) -> bool:
    """Check if value is a float.

    Args:
        value: The value to check.

    Returns:
        True if value is a float, False otherwise.
    """
    return isinstance(value, float)


def is_boolean(value: Any) -> bool:
    """Check if value is a boolean.

    Args:
        value: The value to check.

    Returns:
        True if value is a boolean, False otherwise.
    """
    return isinstance(value, bool)


def is_list(value: Any) -> bool:
    """Check if value is a list.

    Args:
        value: The value to check.

    Returns:
        True if value is a list, False otherwise.
    """
    return isinstance(value, list)


def is_dict(value: Any) -> bool:
    """Check if value is a dictionary.

    Args:
        value: The value to check.

    Returns:
        True if value is a dictionary, False otherwise.
    """
    return isinstance(value, dict)


def is_none(value: Any) -> bool:
    """Check if value is None.

    Args:
        value: The value to check.

    Returns:
        True if value is None, False otherwise.
    """
    return value is None


def is_email(value: Any) -> bool:
    """Check if value is a valid email address.

    Args:
        value: The value to check.

    Returns:
        True if value is a valid email format, False otherwise.
    """
    if not isinstance(value, str):
        return False
    return bool(EMAIL_PATTERN.match(value))


def is_url(value: Any) -> bool:
    """Check if value is a valid URL.

    Args:
        value: The value to check.

    Returns:
        True if value is a valid URL format, False otherwise.
    """
    if not isinstance(value, str):
        return False
    return bool(URL_PATTERN.match(value))


def is_in_range(
    value: Union[int, float],
    min_value: Optional[Union[int, float]] = None,
    max_value: Optional[Union[int, float]] = None,
) -> bool:
    """Check if a numeric value is within a specified range.

    Args:
        value: The numeric value to check.
        min_value: Minimum allowed value (inclusive). None means no minimum.
        max_value: Maximum allowed value (inclusive). None means no maximum.

    Returns:
        True if value is within the range, False otherwise.
    """
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        return False

    if min_value is not None and value < min_value:
        return False
    if max_value is not None and value > max_value:
        return False
    return True


def has_min_length(value: Any, min_length: int) -> bool:
    """Check if value has at least a minimum length.

    Args:
        value: The value to check (must support len()).
        min_length: The minimum required length.

    Returns:
        True if value has at least min_length, False otherwise.
    """
    try:
        return len(value) >= min_length
    except TypeError:
        return False


def has_max_length(value: Any, max_length: int) -> bool:
    """Check if value does not exceed a maximum length.

    Args:
        value: The value to check (must support len()).
        max_length: The maximum allowed length.

    Returns:
        True if value does not exceed max_length, False otherwise.
    """
    try:
        return len(value) <= max_length
    except TypeError:
        return False
