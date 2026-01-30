"""Text formatters for AssertionEngine."""

import re
from typing import Callable


def normalize_spaces(value: str) -> str:
    """Collapse multiple whitespace to single space."""
    return " ".join(value.split())


def strip(value: str) -> str:
    """Remove leading and trailing whitespace."""
    return value.strip()


def lowercase(value: str) -> str:
    """Convert to lowercase."""
    return value.lower()


def uppercase(value: str) -> str:
    """Convert to uppercase."""
    return value.upper()


def strip_html_tags(value: str) -> str:
    """Remove HTML tags from string."""
    return re.sub(r"<[^>]+>", "", value)


# Registry of available formatters
FORMATTERS = {
    "normalize_spaces": normalize_spaces,
    "strip": strip,
    "lowercase": lowercase,
    "uppercase": uppercase,
    "strip_html_tags": strip_html_tags,
}


def get_formatter(name: str) -> Callable[[str], str]:
    """Get formatter by name."""
    if name not in FORMATTERS:
        raise ValueError(
            f"Unknown formatter: {name}. Available: {list(FORMATTERS.keys())}"
        )
    return FORMATTERS[name]


def apply_formatters(value: str, formatter_names: list) -> str:
    """Apply multiple formatters in sequence."""
    for name in formatter_names:
        formatter = get_formatter(name)
        value = formatter(value)
    return value
