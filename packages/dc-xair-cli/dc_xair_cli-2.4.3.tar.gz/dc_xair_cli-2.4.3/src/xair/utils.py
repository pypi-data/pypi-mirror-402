"""Shared utilities for CLI commands."""

from difflib import get_close_matches
from typing import Optional


def parse_channel_spec(spec: str, max_channel: int) -> list[int]:
    """Parse channel specification.

    Supports:
        "1"     -> [1]
        "1-4"   -> [1, 2, 3, 4]
        "1,3,5" -> [1, 3, 5]
        "all"   -> [1, 2, ..., max_channel]

    Args:
        spec: Channel specification string
        max_channel: Maximum valid channel number

    Returns:
        Sorted list of unique channel numbers

    Raises:
        ValueError: If channel number is out of range or spec is invalid
    """
    if spec.lower() == "all":
        return list(range(1, max_channel + 1))

    channels: list[int] = []
    for part in spec.split(","):
        part = part.strip()
        if "-" in part:
            try:
                start, end = part.split("-", 1)
                channels.extend(range(int(start), int(end) + 1))
            except ValueError:
                raise ValueError(f"Invalid range: {part}")
        else:
            try:
                channels.append(int(part))
            except ValueError:
                raise ValueError(f"Invalid channel number: {part}")

    for ch in channels:
        if not 1 <= ch <= max_channel:
            raise ValueError(f"Channel {ch} out of range (1-{max_channel})")

    return sorted(set(channels))


def validate_property(prop_name: str, valid_props: list[str]) -> None:
    """Validate property name and suggest alternatives if invalid.

    Args:
        prop_name: Property name to validate
        valid_props: List of valid property names

    Raises:
        ValueError: If property is invalid, with suggestions if available
    """
    if prop_name not in valid_props:
        suggestions = get_close_matches(prop_name, valid_props, n=1, cutoff=0.6)
        if suggestions:
            raise ValueError(
                f"Invalid property '{prop_name}'. Did you mean '{suggestions[0]}'?"
            )
        raise ValueError(
            f"Invalid property '{prop_name}'. Valid: {', '.join(valid_props)}"
        )


def level_bar(db: float, width: int = 10) -> str:
    """Generate ASCII level bar from dB value."""
    normalized = (db + 90) / 100
    filled = int(max(0, min(width, normalized * width)))
    return "\u2588" * filled + "\u2591" * (width - filled)


def parse_bool_value(value: str, current: Optional[bool] = None) -> bool:
    """Parse boolean value with toggle support.

    Args:
        value: String value ('on', 'off', 'true', 'false', '1', '0', 'toggle')
        current: Current value (required for toggle)

    Returns:
        Boolean result
    """
    v = value.lower()
    if v == "toggle":
        if current is None:
            raise ValueError("Cannot toggle without current value")
        return not current
    if v in ("on", "true", "1"):
        return True
    if v in ("off", "false", "0"):
        return False
    raise ValueError(f"Invalid boolean value: {value}")


def parse_fader_value(
    value: str, current: Optional[float] = None
) -> tuple[float, bool]:
    """Parse fader value with relative adjustment support.

    Args:
        value: String value (absolute like '-6' or relative like '+3' or '--3')
        current: Current value (required for relative adjustments)

    Returns:
        Tuple of (new_value, is_relative)
    """
    value = value.strip()

    if value.startswith("+"):
        if current is None:
            raise ValueError("Cannot use relative adjustment without current value")
        delta = float(value[1:])
        return current + delta, True
    elif value.startswith("--"):
        if current is None:
            raise ValueError("Cannot use relative adjustment without current value")
        delta = float(value[2:])
        return current - delta, True
    else:
        return float(value), False
