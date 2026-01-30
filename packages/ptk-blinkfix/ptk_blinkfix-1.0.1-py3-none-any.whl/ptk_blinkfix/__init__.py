# Import the patch so it runs on package import
from .blink_fix import (
    CURSOR_STYLE,
    CURSOR_SWITCH_KEY,
    CURSOR_CODES,
    CURSOR_ORDER
)

__all__ = [
    "CURSOR_STYLE",
    "CURSOR_SWITCH_KEY",
    "CURSOR_CODES",
    "CURSOR_ORDER"
]
