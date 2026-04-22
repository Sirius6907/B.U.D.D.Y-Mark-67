"""
Zip Manager Action — Compress and extract archives.
"""

import os
import zipfile
from actions.base import Action, ActionRegistry

def zip_manager_action(parameters: dict, **kwargs) -> str:
    command = parameters.get("command", "").lower().strip()
    source = parameters.get("source", "").strip()
    destination = parameters.get("destination", "").strip()

    if not source or not destination:
        return "Both source and destination paths are required."

    if command == "compress":
        if not os.path.exists(source):
            return f"Source path '{source}' does not exist."
        try:
            with zipfile.ZipFile(destination, 'w', zipfile.ZIP_DEFLATED) as zipf:
                if os.path.isfile(source):
                    zipf.write(source, os.path.basename(source))
                elif os.path.isdir(source):
                    for root, _, files in os.walk(source):
                        for file in files:
                            file_path = os.path.join(root, file)
                            arcname = os.path.relpath(file_path, start=os.path.dirname(source))
                            zipf.write(file_path, arcname)
            return f"Successfully compressed '{source}' to '{destination}'."
        except Exception as e:
            return f"Compression failed: {e}"

    elif command == "extract":
        if not os.path.exists(source):
            return f"Source archive '{source}' does not exist."
        try:
            with zipfile.ZipFile(source, 'r') as zipf:
                zipf.extractall(destination)
            return f"Successfully extracted '{source}' to '{destination}'."
        except Exception as e:
            return f"Extraction failed: {e}"

    else:
        return f"Unknown command: '{command}'. Use 'compress' or 'extract'."

class ZipManagerAction(Action):
    @property
    def name(self) -> str:
        return "zip_manager"

    @property
    def description(self) -> str:
        return "Compresses files/folders into a ZIP archive, or extracts a ZIP archive."

    @property
    def parameters_schema(self) -> dict:
        return {
            "type": "OBJECT",
            "properties": {
                "command": {
                    "type": "STRING",
                    "description": "'compress' to create a zip, 'extract' to unzip an archive."
                },
                "source": {
                    "type": "STRING",
                    "description": "Path to the file/folder to compress, or the zip file to extract."
                },
                "destination": {
                    "type": "STRING",
                    "description": "Path where the zip file should be saved, or where files should be extracted."
                }
            },
            "required": ["command", "source", "destination"]
        }

    def execute(self, parameters: dict, **kwargs) -> str:
        return zip_manager_action(parameters, **kwargs)

ActionRegistry.register(ZipManagerAction)
