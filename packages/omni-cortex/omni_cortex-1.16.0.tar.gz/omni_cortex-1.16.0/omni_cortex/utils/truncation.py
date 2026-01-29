"""Output truncation utilities for Omni Cortex."""

import json
from typing import Any


DEFAULT_MAX_LENGTH = 10000
TRUNCATION_SUFFIX = "\n... [truncated]"


def truncate_output(text: str, max_length: int = DEFAULT_MAX_LENGTH) -> str:
    """Truncate text to maximum length.

    Args:
        text: Text to truncate
        max_length: Maximum allowed length

    Returns:
        Truncated text with suffix if truncated
    """
    if len(text) <= max_length:
        return text

    # Reserve space for truncation suffix
    cut_length = max_length - len(TRUNCATION_SUFFIX)
    if cut_length <= 0:
        return text[:max_length]

    return text[:cut_length] + TRUNCATION_SUFFIX


def truncate_json(data: Any, max_length: int = DEFAULT_MAX_LENGTH) -> str:
    """Serialize to JSON and truncate if necessary.

    Args:
        data: Data to serialize
        max_length: Maximum allowed length

    Returns:
        JSON string, truncated if necessary
    """
    json_str = json.dumps(data, default=str)
    return truncate_output(json_str, max_length)


def truncate_dict_values(
    data: dict[str, Any],
    max_value_length: int = 1000
) -> dict[str, Any]:
    """Truncate string values in a dictionary.

    Args:
        data: Dictionary with values to truncate
        max_value_length: Maximum length for each string value

    Returns:
        Dictionary with truncated string values
    """
    result = {}
    for key, value in data.items():
        if isinstance(value, str) and len(value) > max_value_length:
            result[key] = value[:max_value_length] + "..."
        elif isinstance(value, dict):
            result[key] = truncate_dict_values(value, max_value_length)
        elif isinstance(value, list):
            result[key] = [
                truncate_dict_values(item, max_value_length) if isinstance(item, dict)
                else (item[:max_value_length] + "..." if isinstance(item, str) and len(item) > max_value_length else item)
                for item in value
            ]
        else:
            result[key] = value
    return result


def smart_truncate(text: str, max_length: int = DEFAULT_MAX_LENGTH) -> str:
    """Truncate text at a sensible boundary (newline, sentence, word).

    Args:
        text: Text to truncate
        max_length: Maximum allowed length

    Returns:
        Truncated text at a natural boundary
    """
    if len(text) <= max_length:
        return text

    # Reserve space for suffix
    cut_length = max_length - len(TRUNCATION_SUFFIX)
    if cut_length <= 0:
        return text[:max_length]

    # Try to cut at a newline
    last_newline = text.rfind("\n", 0, cut_length)
    if last_newline > cut_length * 0.7:  # Only if reasonably close to the end
        return text[:last_newline] + TRUNCATION_SUFFIX

    # Try to cut at a sentence boundary
    for char in [". ", "! ", "? "]:
        last_sentence = text.rfind(char, 0, cut_length)
        if last_sentence > cut_length * 0.7:
            return text[:last_sentence + 1] + TRUNCATION_SUFFIX

    # Try to cut at a word boundary
    last_space = text.rfind(" ", 0, cut_length)
    if last_space > cut_length * 0.8:
        return text[:last_space] + TRUNCATION_SUFFIX

    # Fall back to hard cut
    return text[:cut_length] + TRUNCATION_SUFFIX
