"""
Notes Manager Action — Create, list, and read quick local text notes.
"""

import os
from pathlib import Path
from actions.base import Action, ActionRegistry

def _get_notes_dir() -> Path:
    # Use user's documents folder for notes to avoid bloating the project dir
    docs = Path(os.path.expanduser("~/Documents/BuddyNotes"))
    docs.mkdir(parents=True, exist_ok=True)
    return docs

def notes_manager_action(parameters: dict, **kwargs) -> str:
    command = parameters.get("command", "list").lower().strip()
    title = parameters.get("title", "").strip()
    content = parameters.get("content", "").strip()
    
    notes_dir = _get_notes_dir()
    
    if command == "create":
        if not title:
            return "Note title is required to create a note."
        safe_title = "".join(c for c in title if c.isalnum() or c in " -_").strip()
        filepath = notes_dir / f"{safe_title}.txt"
        filepath.write_text(content, encoding="utf-8")
        return f"Note '{safe_title}' saved successfully."
        
    elif command == "read":
        if not title:
            return "Note title is required to read a note."
        safe_title = "".join(c for c in title if c.isalnum() or c in " -_").strip()
        filepath = notes_dir / f"{safe_title}.txt"
        if filepath.exists():
            data = filepath.read_text(encoding="utf-8")
            return f"--- {safe_title} ---\n{data}"
        else:
            return f"Note '{safe_title}' not found."
            
    elif command == "list":
        notes = list(notes_dir.glob("*.txt"))
        if not notes:
            return "No notes found."
        names = [n.stem for n in notes]
        return "Saved Notes:\n- " + "\n- ".join(names)
        
    else:
        return f"Unknown command: '{command}'. Use 'create', 'read', or 'list'."

class NotesManagerAction(Action):
    @property
    def name(self) -> str:
        return "notes_manager"

    @property
    def description(self) -> str:
        return "Manage quick local text notes. You can create a new note, read an existing note, or list all saved notes."

    @property
    def parameters_schema(self) -> dict:
        return {
            "type": "OBJECT",
            "properties": {
                "command": {
                    "type": "STRING",
                    "description": "Command to run: 'create', 'read', or 'list'."
                },
                "title": {
                    "type": "STRING",
                    "description": "Title of the note (required for 'create' and 'read')."
                },
                "content": {
                    "type": "STRING",
                    "description": "Content of the note (required for 'create')."
                }
            },
            "required": ["command"]
        }

    def execute(self, parameters: dict, **kwargs) -> str:
        return notes_manager_action(parameters, **kwargs)

ActionRegistry.register(NotesManagerAction)
