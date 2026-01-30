"""Custom exceptions for ValidX."""

from typing import Any, Optional


class ValidationError(Exception):
    """Raised when validation fails.

    Attributes:
        message: A human-readable description of the validation error.
        value: The value that failed validation.
        field: The name of the field that failed validation (optional).
    """

    def __init__(
        self,
        message: str,
        value: Optional[Any] = None,
        field: Optional[str] = None,
    ) -> None:
        """Initialize ValidationError.

        Args:
            message: A human-readable description of the validation error.
            value: The value that failed validation.
            field: The name of the field that failed validation.
        """
        self.message = message
        self.value = value
        self.field = field
        super().__init__(self._format_message())

    def _format_message(self) -> str:
        """Format the error message with optional field and value info."""
        parts = []
        if self.field:
            parts.append(f"Field '{self.field}'")
        parts.append(self.message)
        return ": ".join(parts)

    def __repr__(self) -> str:
        return (
            f"ValidationError(message={self.message!r}, "
            f"value={self.value!r}, field={self.field!r})"
        )
