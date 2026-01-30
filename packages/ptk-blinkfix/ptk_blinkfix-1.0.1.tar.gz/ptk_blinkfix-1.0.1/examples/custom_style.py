import ptk_blinkfix

ptk_blinkfix.CURSOR_STYLE = "steady_block"
ptk_blinkfix.CURSOR_SWITCH_KEY = None  # Disable hotkey

from prompt_toolkit import PromptSession
PromptSession().prompt("Custom style, no hotkey: ")
