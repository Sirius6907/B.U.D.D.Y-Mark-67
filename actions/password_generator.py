"""
Password Generator Action — Generates strong random passwords.
"""

import string
import secrets
from actions.base import Action, ActionRegistry

def password_generator_action(parameters: dict, **kwargs) -> str:
    try:
        length = int(parameters.get("length", 16))
    except ValueError:
        length = 16
        
    if length < 8:
        length = 8
    elif length > 128:
        length = 128
        
    include_symbols = str(parameters.get("include_symbols", "true")).lower() == "true"
    
    chars = string.ascii_letters + string.digits
    if include_symbols:
        chars += "!@#$%^&*()-_=+[]{}|;:,.<>?"
        
    password = "".join(secrets.choice(chars) for _ in range(length))
    
    # We deliberately just return the password. The AI can then read it out
    # or pass it to clipboard_manager.py if the user asked to copy it.
    return f"Generated Password: {password}"

class PasswordGeneratorAction(Action):
    @property
    def name(self) -> str:
        return "password_generator"

    @property
    def description(self) -> str:
        return "Generates a highly secure, random password."

    @property
    def parameters_schema(self) -> dict:
        return {
            "type": "OBJECT",
            "properties": {
                "length": {
                    "type": "INTEGER",
                    "description": "Length of the password (default 16, min 8, max 128)."
                },
                "include_symbols": {
                    "type": "BOOLEAN",
                    "description": "Whether to include symbols (default true)."
                }
            },
            "required": []
        }

    def execute(self, parameters: dict, **kwargs) -> str:
        return password_generator_action(parameters, **kwargs)

ActionRegistry.register(PasswordGeneratorAction)
