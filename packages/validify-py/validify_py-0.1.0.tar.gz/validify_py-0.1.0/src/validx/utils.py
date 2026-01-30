"""Utility functions for ValidX."""

from typing import Any


def is_empty(value: Any) -> bool:
    """Check if a value is considered empty.

    A value is considered empty if it is:
    - None
    - An empty string ('')
    - An empty collection (list, dict, set, tuple with length 0)

    Args:
        value: The value to check.

    Returns:
        True if value is empty, False otherwise.
    """
    if value is None:
        return True
    if isinstance(value, str) and value == "":
        return True
    if hasattr(value, "__len__"):
        try:
            return len(value) == 0
        except TypeError:
            pass
    return False


def is_not_empty(value: Any) -> bool:
    """Check if a value is not empty.

    The inverse of is_empty().

    Args:
        value: The value to check.

    Returns:
        True if value is not empty, False otherwise.
    """
    return not is_empty(value)
