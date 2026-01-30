"""
ptk_blinkfix
------------
Monkey-patch for prompt_toolkit to restore blinking cursor support
in all terminals (including Windows Terminal) and optionally allow
runtime cursor style switching with a hotkey.

Usage:
    import ptk_blinkfix  # Auto-patches prompt_toolkit

    # Optional: change defaults before importing PromptSession
    ptk_blinkfix.CURSOR_STYLE = "blinking_block"
    ptk_blinkfix.CURSOR_SWITCH_KEY = "f2"  # or None to disable hotkey

    from prompt_toolkit import PromptSession
    PromptSession().prompt()
"""

import sys
from prompt_toolkit.output import vt100
from prompt_toolkit.key_binding import KeyBindings

# === CONFIGURATION ===
CURSOR_STYLE = "blinking_block"  # Startup style
CURSOR_SWITCH_KEY = "f2"         # Hotkey to cycle styles, or None to disable

# Mapping of style names to ANSI escape codes
CURSOR_CODES = {
    "blinking_block": "\x1b[1 q",
    "blinking_underline": "\x1b[3 q",
    "blinking_beam": "\x1b[5 q",
    "steady_block": "\x1b[2 q",
    "steady_underline": "\x1b[4 q",
    "steady_beam": "\x1b[6 q",
}

# Ordered list for cycling
CURSOR_ORDER = list(CURSOR_CODES.keys())

# === PATCH 1: Always re-apply style when showing cursor ===
def patched_show_cursor(self):
    if self._cursor_visible in (False, None):
        self._cursor_visible = True
        self.write_raw("\x1b[?25h")  # Show cursor
        self.write_raw(CURSOR_CODES.get(CURSOR_STYLE, "\x1b[1 q"))

vt100.Vt100_Output.show_cursor = patched_show_cursor

# === PATCH 2: Force chosen style in set_cursor_shape ===
def patched_set_cursor_shape(self, cursor_shape):
    self._cursor_shape_changed = True
    self.write_raw(CURSOR_CODES.get(CURSOR_STYLE, "\x1b[1 q"))

vt100.Vt100_Output.set_cursor_shape = patched_set_cursor_shape

# === PATCH 3: Apply style immediately at startup ===
sys.stdout.write(CURSOR_CODES.get(CURSOR_STYLE, "\x1b[1 q"))
sys.stdout.flush()

# === PATCH 4: Optional runtime style switching ===
def _add_cursor_switch_hotkey(app):
    """
    Add a hotkey to cycle through cursor styles at runtime.
    Pass in the Application instance (e.g., session.app).
    """
    kb = KeyBindings()

    @kb.add(CURSOR_SWITCH_KEY)
    def _(event):
        global CURSOR_STYLE
        idx = CURSOR_ORDER.index(CURSOR_STYLE)
        CURSOR_STYLE = CURSOR_ORDER[(idx + 1) % len(CURSOR_ORDER)]
        sys.stdout.write(CURSOR_CODES[CURSOR_STYLE])
        sys.stdout.flush()

    app.key_bindings = kb.merge(app.key_bindings, kb)

# === PATCH 5: Auto-bind hotkey if enabled ===
if CURSOR_SWITCH_KEY:
    try:
        from prompt_toolkit.application import get_app
        app = get_app()
        _add_cursor_switch_hotkey(app)
    except Exception:
        # No active app yet — user can call manually later
        pass
