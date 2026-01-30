# ptk-blinkfix

**Blinking cursor fix for Python [`prompt_toolkit`](https://github.com/prompt-toolkit/python-prompt-toolkit) apps**  
Enables and preserves cursor blinking in `PromptSession` and full‑screen apps (`TextArea`, etc.) across Linux, macOS, and Windows Terminal — without modifying or recompiling `prompt_toolkit`.

## ✨ Features
- Works with **PromptSession** and **full‑screen `Application`** widgets.
- Keeps your chosen cursor style **even after selection, scrolling, or redraws**.
- Supports **runtime style switching** (default hotkey: `F2`).
- Fully configurable **startup cursor style**.
- No fork or rebuild — just import and patch.

## 🚀 Installation
```bash
pip install ptk-blinkfix
```

## 📦 Usage
```python
import ptk_blinkfix as blinkfix

# Optional: set startup style and hotkey
blinkfix.CURSOR_STYLE = "blinking_block"  # or blinking_underline, blinking_beam, steady_block, etc.
blinkfix.CURSOR_SWITCH_KEY = "f2"

from prompt_toolkit import PromptSession

session = PromptSession()
while True:
    try:
        text = session.prompt(">>> ")
        print(f"You typed: {text}")
    except (EOFError, KeyboardInterrupt):
        break
```

## 🎯 Supported Cursor Styles
- `blinking_block`
- `blinking_underline`
- `blinking_beam`
- `steady_block`
- `steady_underline`
- `steady_beam`

## 📜 License
This project is licensed under the BSD‑3‑Clause License.  
It interacts with [`prompt_toolkit`](https://github.com/prompt-toolkit/python-prompt-toolkit), which is also licensed under BSD‑3‑Clause.  
See [LICENSE](LICENSE) for details.
