"""Helper functions for validating form input values."""
import re
from datetime import date

from config import (
    FIELD_NAME_MUST_BE_INT_ERR,
    FIELD_NAME_MUST_BE_MAX_LENGTH_ERR,
    FILED_NAME_MUST_BE_VALID_DATE,
    FILED_NAME_REQUIRED_ERR,
    ISBN_INVALID,
)


def validate_int(
    value: str,
    field_name: str,
    max_length: int | None = None,
    *,
    nullable: bool = False,
) -> None | str:
    """Validate that a value is an integer (op. of max_length).

    Does not type convert.
    """
    value = "" if value is None else str(value).strip()
    if nullable and not value:
        return None
    if not value:
        return FILED_NAME_REQUIRED_ERR.format(filed_name=field_name)
    if max_length and len(value) > max_length:
        return FIELD_NAME_MUST_BE_MAX_LENGTH_ERR.format(
            filed_name=field_name,
            max_length=max_length,
        )
    # int() would also accept "-5", "+5", "1_000" and non-latin digits
    if not re.fullmatch(r"[0-9]+", value):
        return FIELD_NAME_MUST_BE_INT_ERR.format(filed_name=field_name)
    return None


def validate_isbn(
    value: str,
    field_name: str,
    *,
    nullable: bool = False,
) -> None | str:
    """Validate that a value is an ISBN-10 or ISBN-13 (digits only).

    ISBN-10 may end with an X. That's not verified.
    Does not type convert.
    """
    value = "" if value is None else str(value).strip()
    if nullable and not value:
        return None
    if not value:
        return FILED_NAME_REQUIRED_ERR.format(filed_name=field_name)
    if not re.fullmatch(r"[0-9]{13}|[0-9]{9}[0-9X]", value):
        return ISBN_INVALID.format(isbn=field_name)
    return None


def validate_date(
    value: str,
    field_name: str,
    *,
    nullable: bool = False,
) -> None | str:
    """Validate that a value is date.

    Does not type convert.
    """
    value = "" if value is None else str(value).strip()
    if nullable and not value:
        return None
    if not value:
        return FILED_NAME_REQUIRED_ERR.format(filed_name=field_name)

    try:
        date.fromisoformat(value)
    except ValueError:
        return FILED_NAME_MUST_BE_VALID_DATE.format(field_name=field_name)
    return None
