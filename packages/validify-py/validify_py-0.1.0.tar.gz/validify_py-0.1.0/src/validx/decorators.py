"""Validation decorators for ValidX."""

from functools import wraps
from typing import Any, Callable, TypeVar

from validx.exceptions import ValidationError

F = TypeVar("F", bound=Callable[..., Any])


def validate_args(validator: Callable[..., bool]) -> Callable[[F], F]:
    """Decorator to validate function arguments.

    The validator function receives all arguments passed to the decorated
    function and should return True if validation passes, False otherwise.

    Args:
        validator: A callable that takes the same arguments as the decorated
            function and returns True if valid, False otherwise.

    Returns:
        A decorator that validates arguments before calling the function.

    Example:
        >>> def is_positive(x):
        ...     return x > 0
        ...
        >>> @validate_args(is_positive)
        ... def square(x):
        ...     return x * x
        ...
        >>> square(5)
        25
        >>> square(-1)  # Raises ValidationError
    """

    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            if not validator(*args, **kwargs):
                msg = f"Validation failed for arguments: args={args}, kwargs={kwargs}"
                raise ValidationError(msg)
            return func(*args, **kwargs)

        return wrapper  # type: ignore[return-value]

    return decorator


def validate_return(validator: Callable[[Any], bool]) -> Callable[[F], F]:
    """Decorator to validate function return value.

    The validator function receives the return value and should return
    True if validation passes, False otherwise.

    Args:
        validator: A callable that takes the return value and returns
            True if valid, False otherwise.

    Returns:
        A decorator that validates the return value after calling the function.

    Example:
        >>> def is_not_none(value):
        ...     return value is not None
        ...
        >>> @validate_return(is_not_none)
        ... def get_user(user_id):
        ...     return find_user(user_id)
    """

    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            result = func(*args, **kwargs)
            if not validator(result):
                raise ValidationError(f"Validation failed for return value: {result}")
            return result

        return wrapper  # type: ignore[return-value]

    return decorator
