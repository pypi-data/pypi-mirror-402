"""Tests for validx.utils module."""

from validx.utils import is_empty, is_not_empty


class TestIsEmpty:
    """Tests for is_empty utility function."""

    def test_returns_true_for_none(self) -> None:
        assert is_empty(None) is True

    def test_returns_true_for_empty_string(self) -> None:
        assert is_empty("") is True

    def test_returns_true_for_empty_collections(self) -> None:
        assert is_empty([]) is True
        assert is_empty({}) is True
        assert is_empty(set()) is True
        assert is_empty(()) is True

    def test_returns_false_for_non_empty_string(self) -> None:
        assert is_empty("hello") is False
        assert is_empty(" ") is False  # Whitespace is not empty

    def test_returns_false_for_non_empty_collections(self) -> None:
        assert is_empty([1]) is False
        assert is_empty({"key": "value"}) is False
        assert is_empty({1}) is False
        assert is_empty((1,)) is False

    def test_returns_false_for_zero(self) -> None:
        # Zero is a valid value, not empty
        assert is_empty(0) is False
        assert is_empty(0.0) is False

    def test_returns_false_for_false(self) -> None:
        # False is a valid value, not empty
        assert is_empty(False) is False


class TestIsNotEmpty:
    """Tests for is_not_empty utility function."""

    def test_returns_false_for_none(self) -> None:
        assert is_not_empty(None) is False

    def test_returns_false_for_empty_string(self) -> None:
        assert is_not_empty("") is False

    def test_returns_false_for_empty_collections(self) -> None:
        assert is_not_empty([]) is False
        assert is_not_empty({}) is False

    def test_returns_true_for_non_empty_values(self) -> None:
        assert is_not_empty("hello") is True
        assert is_not_empty([1, 2, 3]) is True
        assert is_not_empty({"key": "value"}) is True
        assert is_not_empty(0) is True
        assert is_not_empty(False) is True
