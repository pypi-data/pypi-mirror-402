"""Tests for validx.validators module."""

from validx import validators


class TestIsString:
    """Tests for is_string validator."""

    def test_returns_true_for_string(self) -> None:
        assert validators.is_string("abc") is True
        assert validators.is_string("") is True
        assert validators.is_string("hello world") is True

    def test_returns_false_for_non_string(self) -> None:
        assert validators.is_string(123) is False
        assert validators.is_string(None) is False
        assert validators.is_string([]) is False
        assert validators.is_string({}) is False


class TestIsInteger:
    """Tests for is_integer validator."""

    def test_returns_true_for_integer(self) -> None:
        assert validators.is_integer(123) is True
        assert validators.is_integer(0) is True
        assert validators.is_integer(-42) is True

    def test_returns_false_for_non_integer(self) -> None:
        assert validators.is_integer("abc") is False
        assert validators.is_integer(1.23) is False
        assert validators.is_integer(None) is False

    def test_returns_false_for_boolean(self) -> None:
        # Booleans are technically ints in Python, but we want to exclude them
        assert validators.is_integer(True) is False
        assert validators.is_integer(False) is False


class TestIsFloat:
    """Tests for is_float validator."""

    def test_returns_true_for_float(self) -> None:
        assert validators.is_float(1.23) is True
        assert validators.is_float(0.0) is True
        assert validators.is_float(-3.14) is True

    def test_returns_false_for_non_float(self) -> None:
        assert validators.is_float("1.23") is False
        assert validators.is_float(123) is False
        assert validators.is_float(None) is False


class TestIsBoolean:
    """Tests for is_boolean validator."""

    def test_returns_true_for_boolean(self) -> None:
        assert validators.is_boolean(True) is True
        assert validators.is_boolean(False) is True

    def test_returns_false_for_non_boolean(self) -> None:
        assert validators.is_boolean(1) is False
        assert validators.is_boolean(0) is False
        assert validators.is_boolean("true") is False


class TestIsList:
    """Tests for is_list validator."""

    def test_returns_true_for_list(self) -> None:
        assert validators.is_list([]) is True
        assert validators.is_list([1, 2, 3]) is True

    def test_returns_false_for_non_list(self) -> None:
        assert validators.is_list((1, 2, 3)) is False
        assert validators.is_list("abc") is False


class TestIsDict:
    """Tests for is_dict validator."""

    def test_returns_true_for_dict(self) -> None:
        assert validators.is_dict({}) is True
        assert validators.is_dict({"key": "value"}) is True

    def test_returns_false_for_non_dict(self) -> None:
        assert validators.is_dict([]) is False
        assert validators.is_dict("abc") is False


class TestIsNone:
    """Tests for is_none validator."""

    def test_returns_true_for_none(self) -> None:
        assert validators.is_none(None) is True

    def test_returns_false_for_non_none(self) -> None:
        assert validators.is_none(0) is False
        assert validators.is_none("") is False
        assert validators.is_none(False) is False


class TestIsEmail:
    """Tests for is_email validator."""

    def test_returns_true_for_valid_email(self) -> None:
        assert validators.is_email("test@example.com") is True
        assert validators.is_email("user.name@domain.org") is True
        assert validators.is_email("user+tag@example.co.uk") is True

    def test_returns_false_for_invalid_email(self) -> None:
        assert validators.is_email("not-an-email") is False
        assert validators.is_email("missing@domain") is False
        assert validators.is_email("@nodomain.com") is False
        assert validators.is_email(123) is False
        assert validators.is_email(None) is False


class TestIsUrl:
    """Tests for is_url validator."""

    def test_returns_true_for_valid_url(self) -> None:
        assert validators.is_url("https://example.com") is True
        assert validators.is_url("http://example.com") is True
        assert validators.is_url("https://example.com/path") is True
        assert validators.is_url("https://example.com:8080") is True
        assert validators.is_url("http://localhost:3000") is True

    def test_returns_false_for_invalid_url(self) -> None:
        assert validators.is_url("not-a-url") is False
        assert validators.is_url("ftp://example.com") is False
        assert validators.is_url("example.com") is False
        assert validators.is_url(123) is False
        assert validators.is_url(None) is False


class TestIsInRange:
    """Tests for is_in_range validator."""

    def test_returns_true_when_in_range(self) -> None:
        assert validators.is_in_range(5, min_value=0, max_value=10) is True
        assert validators.is_in_range(0, min_value=0, max_value=10) is True
        assert validators.is_in_range(10, min_value=0, max_value=10) is True

    def test_returns_false_when_out_of_range(self) -> None:
        assert validators.is_in_range(-1, min_value=0, max_value=10) is False
        assert validators.is_in_range(11, min_value=0, max_value=10) is False

    def test_handles_open_ended_ranges(self) -> None:
        assert validators.is_in_range(100, min_value=0) is True
        assert validators.is_in_range(-100, max_value=0) is True

    def test_returns_false_for_non_numeric(self) -> None:
        assert validators.is_in_range("5", min_value=0, max_value=10) is False
        assert validators.is_in_range(True, min_value=0, max_value=10) is False


class TestHasMinLength:
    """Tests for has_min_length validator."""

    def test_returns_true_when_meets_min_length(self) -> None:
        assert validators.has_min_length("abc", 3) is True
        assert validators.has_min_length("abcd", 3) is True
        assert validators.has_min_length([1, 2, 3], 3) is True

    def test_returns_false_when_below_min_length(self) -> None:
        assert validators.has_min_length("ab", 3) is False
        assert validators.has_min_length([], 1) is False

    def test_returns_false_for_non_sequence(self) -> None:
        assert validators.has_min_length(123, 3) is False
        assert validators.has_min_length(None, 1) is False


class TestHasMaxLength:
    """Tests for has_max_length validator."""

    def test_returns_true_when_meets_max_length(self) -> None:
        assert validators.has_max_length("abc", 3) is True
        assert validators.has_max_length("ab", 3) is True
        assert validators.has_max_length([1, 2], 3) is True

    def test_returns_false_when_above_max_length(self) -> None:
        assert validators.has_max_length("abcd", 3) is False
        assert validators.has_max_length([1, 2, 3, 4], 3) is False

    def test_returns_false_for_non_sequence(self) -> None:
        assert validators.has_max_length(123, 3) is False
        assert validators.has_max_length(None, 1) is False
