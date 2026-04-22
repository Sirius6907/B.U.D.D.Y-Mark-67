"""
Email Client Action — Drafts an email via default mail client.
"""

import urllib.parse
import webbrowser
from actions.base import Action, ActionRegistry

def email_client_action(parameters: dict, **kwargs) -> str:
    to = parameters.get("to", "").strip()
    subject = parameters.get("subject", "").strip()
    body = parameters.get("body", "").strip()
    
    if not to:
        return "Please specify a recipient email address."
        
    mailto_url = f"mailto:{to}"
    params = []
    if subject:
        params.append(f"subject={urllib.parse.quote(subject)}")
    if body:
        params.append(f"body={urllib.parse.quote(body)}")
        
    if params:
        mailto_url += "?" + "&".join(params)
        
    try:
        webbrowser.open(mailto_url)
        return f"Opened default email client to draft message to {to}."
    except Exception as e:
        return f"Failed to open email client: {e}"

class EmailClientAction(Action):
    @property
    def name(self) -> str:
        return "email_client"

    @property
    def description(self) -> str:
        return "Opens the system default email client to draft a new email with pre-filled recipient, subject, and body."

    @property
    def parameters_schema(self) -> dict:
        return {
            "type": "OBJECT",
            "properties": {
                "to": {
                    "type": "STRING",
                    "description": "Recipient email address."
                },
                "subject": {
                    "type": "STRING",
                    "description": "Subject of the email."
                },
                "body": {
                    "type": "STRING",
                    "description": "Body content of the email."
                }
            },
            "required": ["to"]
        }

    def execute(self, parameters: dict, **kwargs) -> str:
        return email_client_action(parameters, **kwargs)

ActionRegistry.register(EmailClientAction)
