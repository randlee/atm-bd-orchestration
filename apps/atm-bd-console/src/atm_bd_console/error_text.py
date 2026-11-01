"""Format a shared error consistently across the console."""
from __future__ import annotations

from atm_bd_types import Error
from result import kind_name


def error_text(error: Error) -> str:
    """Keep the established kind, detail and recovery text."""
    if not isinstance(error, Error):
        raise TypeError(f"unknown error variant {type(error).__name__}; add it to error_text")
    return f"{kind_name(error.kind)}: {error.message}; {error.fix}"
