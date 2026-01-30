"""Tests for validx.decorators module."""

import pytest

from validx.decorators import validate_args, validate_return
from validx.exceptions import ValidationError


def always_true(*args, **kwargs) -> bool:
    """Validator that always returns True."""
    return True


def always_false(*args, **kwargs) -> bool:
    """Validator that always returns False."""
    return False


def is_positive(x: int) -> bool:
    """Check if x is positive."""
    return x > 0


def is_not_none(value) -> bool:
    """Check if value is not None."""
    return value is not None


class TestValidateArgs:
    """Tests for validate_args decorator."""

    def test_passes_when_validation_succeeds(self) -> None:
        @validate_args(always_true)
        def foo(x: int) -> int:
            return x

        assert foo(1) == 1

    def test_raises_when_validation_fails(self) -> None:
        @validate_args(always_false)
        def foo(x: int) -> int:
            return x

        with pytest.raises(ValidationError):
            foo(1)

    def test_preserves_function_metadata(self) -> None:
        @validate_args(always_true)
        def documented_function(x: int) -> int:
            """This is the docstring."""
            return x

        assert documented_function.__name__ == "documented_function"
        assert documented_function.__doc__ == "This is the docstring."

    def test_works_with_kwargs(self) -> None:
        def check_name(name: str = "") -> bool:
            return len(name) > 0

        @validate_args(check_name)
        def greet(name: str = "") -> str:
            return f"Hello, {name}!"

        assert greet(name="World") == "Hello, World!"

        with pytest.raises(ValidationError):
            greet(name="")

    def test_realistic_validation_scenario(self) -> None:
        @validate_args(is_positive)
        def square(x: int) -> int:
            return x * x

        assert square(5) == 25
        assert square(1) == 1

        with pytest.raises(ValidationError):
            square(-1)

        with pytest.raises(ValidationError):
            square(0)


class TestValidateReturn:
    """Tests for validate_return decorator."""

    def test_passes_when_return_validation_succeeds(self) -> None:
        @validate_return(is_not_none)
        def get_value() -> str:
            return "value"

        assert get_value() == "value"

    def test_raises_when_return_validation_fails(self) -> None:
        @validate_return(is_not_none)
        def get_none():
            return None

        with pytest.raises(ValidationError):
            get_none()

    def test_preserves_function_metadata(self) -> None:
        @validate_return(is_not_none)
        def documented_function() -> str:
            """This is the docstring."""
            return "value"

        assert documented_function.__name__ == "documented_function"
        assert documented_function.__doc__ == "This is the docstring."

    def test_realistic_validation_scenario(self) -> None:
        def is_positive_result(result: int) -> bool:
            return result > 0

        @validate_return(is_positive_result)
        def calculate(a: int, b: int) -> int:
            return a + b

        assert calculate(3, 5) == 8

        with pytest.raises(ValidationError):
            calculate(-10, 5)
