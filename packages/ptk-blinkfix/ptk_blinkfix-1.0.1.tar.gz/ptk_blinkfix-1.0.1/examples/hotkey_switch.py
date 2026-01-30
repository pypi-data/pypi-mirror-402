import ptk_blinkfix

ptk_blinkfix.CURSOR_STYLE = "blinking_block"
ptk_blinkfix.CURSOR_SWITCH_KEY = "f2"  # Cycle styles with F2

from prompt_toolkit import PromptSession
PromptSession().prompt("Press F2 to change cursor style: ")
