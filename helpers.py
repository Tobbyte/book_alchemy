import re
from datetime import date


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
        return f"{field_name} is required."
    if max_length and len(value) > max_length:
        return f"{field_name} must be max {max_length} digits long."
    # int() would also accept "-5", "+5", "1_000" and non-latin digits
    if not re.fullmatch(r"[0-9]+", value):
        return f"{field_name} must be a whole number."
    return None


def validate_isbn(
    value: str,
    field_name: str,
    *,
    nullable: bool = False,
) -> None | str:
    """Validate that a value is an ISBN-10 or ISBN-13 (digits only, no hyphens).

    ISBN-10 may end with an X. The check digit is not verified.
    Does not type convert.
    """
    value = "" if value is None else str(value).strip()
    if nullable and not value:
        return None
    if not value:
        return f"{field_name} is required."
    if not re.fullmatch(r"[0-9]{13}|[0-9]{9}[0-9X]", value):
        return f"{field_name} must be 10 or 13 digits long (ISBN-10 may end with X)."
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
        return f"{field_name} is required."

    try:
        date.fromisoformat(value)
    except ValueError:
        return f"{field_name} must be valid date in format YYYY-MM-DD."
    return None
