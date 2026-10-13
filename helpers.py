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
    value = str(value).strip()
    if nullable and (not value or value == "None"):
        return None
    if not value:
        return f"{field_name} is required."
    if max_length and len(value) > max_length:
        return f"{field_name} must be max {max_length} digits long."
    try:
        int(value)
    except ValueError:
        return f"{field_name} must be a whole number."


def validate_date(
    value: str,
    field_name: str,
    *,
    nullable: bool = False,
) -> None | str:
    """Validate that a value is date.

    Does not type convert.
    """
    value = str(value).strip()
    if nullable and (not value or value == "None"):
        return None
    if not value:
        return f"{field_name} is required."

    try:
        date.fromisoformat(value)
    except ValueError:
        return f"{field_name} must be valid date in format YYYY-MM-DD."
