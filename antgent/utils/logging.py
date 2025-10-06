from typing import Any


def truncate_for_log(value: Any, max_len: int = 200) -> str:
    """
    Truncate a value to a reasonable length for logging.

    Args:
        value: Any value to convert to string and truncate
        max_len: Maximum length before truncation (default: 200)

    Returns:
        Truncated string representation with "..." if truncated
    """
    str_val = str(value)
    if len(str_val) <= max_len:
        return str_val
    return str_val[:max_len] + "..."
