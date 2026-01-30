"""Tests for validx.exceptions module."""

import pytest

from validx.exceptions import ValidationError


class TestValidationError:
    """Tests for ValidationError exception."""

    def test_creates_with_message_only(self) -> None:
        error = ValidationError("Invalid value")
        assert str(error) == "Invalid value"
        assert error.message == "Invalid value"
        assert error.value is None
        assert error.field is None

    def test_creates_with_value(self) -> None:
        error = ValidationError("Invalid value", value="bad")
        assert error.value == "bad"
        assert error.message == "Invalid value"

    def test_creates_with_field(self) -> None:
        error = ValidationError("Invalid value", field="email")
        assert str(error) == "Field 'email': Invalid value"
        assert error.field == "email"

    def test_creates_with_all_params(self) -> None:
        error = ValidationError("Must be positive", value=-1, field="age")
        assert str(error) == "Field 'age': Must be positive"
        assert error.message == "Must be positive"
        assert error.value == -1
        assert error.field == "age"

    def test_repr(self) -> None:
        error = ValidationError("Invalid", value=123, field="count")
        repr_str = repr(error)
        assert "ValidationError" in repr_str
        assert "Invalid" in repr_str
        assert "123" in repr_str
        assert "count" in repr_str

    def test_is_exception(self) -> None:
        error = ValidationError("Test error")
        assert isinstance(error, Exception)

    def test_can_be_raised_and_caught(self) -> None:
        with pytest.raises(ValidationError) as exc_info:
            raise ValidationError("Test error", value="bad", field="test")

        assert exc_info.value.message == "Test error"
        assert exc_info.value.value == "bad"
        assert exc_info.value.field == "test"
