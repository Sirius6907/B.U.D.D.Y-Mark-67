"""
Clipboard Manager — read, write, and clear the system clipboard.
"""

import subprocess
from actions.base import Action, ActionRegistry


def clipboard_manager(parameters: dict, player=None, speak=None, **kwargs) -> str:
    action = parameters.get("action", "read").lower()
    if action == "read":
        return _read()
    if action == "write":
        return _write(parameters)
    if action == "clear":
        return _clear()
    return f"Unknown clipboard_manager action: {action}"


def _read() -> str:
    try:
        import pyperclip
        content = pyperclip.paste()
    except ImportError:
        r = subprocess.run(["powershell", "-Command", "Get-Clipboard"],
                           capture_output=True, text=True, timeout=5)
        content = r.stdout.strip()
    if not content:
        return "📋 Clipboard is empty."
    display = content[:2000]
    if len(content) > 2000:
        display += f"\n... ({len(content)} total chars)"
    return f"📋 Clipboard content:\n{display}"


def _write(params: dict) -> str:
    text = params.get("text", "")
    if not text:
        return "No text provided."
    try:
        import pyperclip
        pyperclip.copy(text)
    except ImportError:
        subprocess.run(["powershell", "-Command", f"Set-Clipboard -Value '{text}'"],
                       capture_output=True, text=True, timeout=5)
    return f"📋 Copied {len(text)} characters to clipboard."


def _clear() -> str:
    try:
        import pyperclip
        pyperclip.copy("")
    except ImportError:
        subprocess.run(["powershell", "-Command", "Set-Clipboard -Value $null"],
                       capture_output=True, text=True, timeout=5)
    return "📋 Clipboard cleared."


class ClipboardManagerAction(Action):
    @property
    def name(self) -> str:
        return "clipboard_manager"

    @property
    def description(self) -> str:
        return "Manage the system clipboard. Read, write text, or clear it."

    @property
    def parameters_schema(self) -> dict:
        return {
            "type": "OBJECT",
            "properties": {
                "action": {"type": "STRING", "description": "read | write | clear"},
                "text": {"type": "STRING", "description": "Text to copy (for write)"},
            },
            "required": ["action"],
        }

    def execute(self, parameters: dict, player=None, speak=None, **kwargs) -> str:
        return clipboard_manager(parameters=parameters, player=player, speak=speak)


ActionRegistry.register(ClipboardManagerAction)
