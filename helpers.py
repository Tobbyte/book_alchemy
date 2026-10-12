from datetime import date


def validate_int(
    value: str,
    field_name: str,
    length: int | None = None,
    *,
    nullable: bool = False,
) -> None | str:
    """Validate that a value is an integer (op. of length)."""
    value = value.strip()
    if nullable and not value:
        return None
    if not value:
        return f"{field_name} is required."
    try:
        if length and len(value) != length:
            return f"{field_name} must be {length} digits long."
    except ValueError:
        return f"{field_name} must be a whole number."


def validate_date(
    value: str,
    field_name: str,
    *,
    nullable: bool = False,
) -> None | str:
    """Validate that a value is date."""
    value = value.strip()
    if nullable and not value:
        return None
    if not value:
        return f"{field_name} is required."

    try:
        date.fromisoformat(value)
    except ValueError:
        return f"{field_name} must be valid date in format YYYY-MM-DD."
