import re


_DATE_PATTERN = re.compile(r"[0-9]{4}-(0[1-9]|1[0-2])-(0[1-9]|[12][0-9]|3[01])")


def validate_date(value: str, field: str) -> str:
    if not _DATE_PATTERN.fullmatch(value):
        raise ValueError(f"Укажите {field} в формате YYYY-MM-DD.")
    return value
