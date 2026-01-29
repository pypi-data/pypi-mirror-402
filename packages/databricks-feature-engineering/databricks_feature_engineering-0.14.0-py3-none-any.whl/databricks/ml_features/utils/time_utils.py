import datetime
from decimal import ROUND_HALF_EVEN, Decimal, InvalidOperation
from typing import Dict

DAYS_FIELD_NAME = "days"
SECONDS_FIELD_NAME = "seconds"
MICROSECONDS_FIELD_NAME = "microseconds"


def format_duration(delta: datetime.timedelta) -> str:
    """
    Formats a timedelta into a comprehensive string representation.

    Returns a string showing all non-zero time components from days down to milliseconds,
    separated by underscores.

    :param delta: The timedelta to format
    :return: String representation (e.g., "7d", "7d_2h_30m", "45s", "500ms")

    Examples:
        format_duration(timedelta(days=7)) -> "7d"
        format_duration(timedelta(days=7, hours=2, minutes=30)) -> "7d_2h_30m"
        format_duration(timedelta(minutes=30, seconds=45)) -> "30m_45s"
        format_duration(timedelta(seconds=45)) -> "45s"
        format_duration(timedelta(milliseconds=500)) -> "500ms"
    """
    total_seconds = delta.total_seconds()
    assert total_seconds >= 0

    # Extract components
    days = int(total_seconds // 86400)
    remaining_seconds = total_seconds % 86400

    hours = int(remaining_seconds // 3600)
    remaining = remaining_seconds % 3600

    minutes = int(remaining // 60)
    remaining = remaining % 60

    seconds = int(remaining)

    # Extract milliseconds from microseconds
    milliseconds = delta.microseconds // 1000

    # Build components list with non-zero values
    components = []

    if days > 0:
        components.append(f"{days}d")
    if hours > 0:
        components.append(f"{hours}h")
    if minutes > 0:
        components.append(f"{minutes}m")
    if seconds > 0:
        components.append(f"{seconds}s")
    if milliseconds > 0:
        components.append(f"{milliseconds}ms")

    # Special case: if everything is zero
    if not components:
        return "0s"

    return "_".join(components)


def timedelta_to_dict(time_delta: datetime.timedelta) -> Dict[str, int]:
    """
    Serialize a timedelta into a dictionary that can be used to generate a YAML file.
    """
    return {
        DAYS_FIELD_NAME: time_delta.days,
        SECONDS_FIELD_NAME: time_delta.seconds,
        MICROSECONDS_FIELD_NAME: time_delta.microseconds,
    }


def dict_to_timedelta(time_dict: Dict[str, int]) -> datetime.timedelta:
    """
    Deserialize a dictionary back into a timedelta object.

    It's expected that the dictionary contains only days, seconds, and microseconds.
    """
    return datetime.timedelta(
        days=time_dict.get(DAYS_FIELD_NAME, 0),
        seconds=time_dict.get(SECONDS_FIELD_NAME, 0),
        microseconds=time_dict.get(MICROSECONDS_FIELD_NAME, 0),
    )


_SECONDS_PER_DAY = 86400
_MICROSECONDS_PER_SECOND = 1_000_000


def timedelta_to_duration_string(delta: datetime.timedelta) -> str:
    """Convert a ``datetime.timedelta`` to a JSON duration string (e.g. ``"60s"``)."""
    total_microseconds = (
        delta.days * _SECONDS_PER_DAY * _MICROSECONDS_PER_SECOND
        + delta.seconds * _MICROSECONDS_PER_SECOND
        + delta.microseconds
    )

    sign = "-" if total_microseconds < 0 else ""
    total_microseconds = abs(total_microseconds)

    seconds_decimal = Decimal(total_microseconds) / Decimal(_MICROSECONDS_PER_SECOND)
    seconds_str = format(seconds_decimal, "f")
    if "." in seconds_str:
        seconds_str = seconds_str.rstrip("0").rstrip(".")
    if not seconds_str:
        seconds_str = "0"

    return f"{sign}{seconds_str}s"


def duration_string_to_timedelta(value: str) -> datetime.timedelta:
    """Parse a JSON duration string (e.g. ``"60s"``) into ``datetime.timedelta``."""
    if not isinstance(value, str):
        raise TypeError("Duration value must be a string")

    if not value.endswith("s"):
        raise ValueError(f"Invalid duration string '{value}', expected suffix 's'")

    numeric_portion = value[:-1]
    if numeric_portion == "":
        raise ValueError("Duration string is missing numeric value")

    try:
        seconds_decimal = Decimal(numeric_portion)
    except InvalidOperation as exc:
        raise ValueError(f"Invalid duration string '{value}'") from exc
    microseconds_decimal = seconds_decimal * Decimal(_MICROSECONDS_PER_SECOND)
    microseconds = int(microseconds_decimal.to_integral_value(rounding=ROUND_HALF_EVEN))

    return datetime.timedelta(microseconds=microseconds)
