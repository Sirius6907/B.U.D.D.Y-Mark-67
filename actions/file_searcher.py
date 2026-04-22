import os
import fnmatch
import logging
from .base import Action

logger = logging.getLogger(__name__)

class FileSearcherAction(Action):
    """Searches for files by name pattern or content recursively."""
    
    name = "file_searcher"
    description = "Searches for files by name pattern (e.g., '*.txt') or text content recursively in a directory."
    parameters_schema = {
        "type": "object",
        "properties": {
            "search_dir": {
                "type": "string",
                "description": "The directory to search in."
            },
            "pattern": {
                "type": "string",
                "description": "File name pattern (e.g., '*.py' or '*report*'). Default is '*' if searching by content.",
                "default": "*"
            },
            "content": {
                "type": "string",
                "description": "Text content to search for inside the files (optional)."
            }
        },
        "required": ["search_dir"]
    }
    
    def execute(self, search_dir: str, pattern: str = "*", content: str = None) -> str:
        if not os.path.exists(search_dir) or not os.path.isdir(search_dir):
            return f"Error: Directory '{search_dir}' does not exist."
            
        results = []
        try:
            for root, dirs, files in os.walk(search_dir):
                for filename in fnmatch.filter(files, pattern):
                    filepath = os.path.join(root, filename)
                    
                    if content:
                        try:
                            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                                if content in f.read():
                                    results.append(filepath)
                        except Exception:
                            continue
                    else:
                        results.append(filepath)
            
            if not results:
                return "No files found matching the criteria."
                
            return f"Found {len(results)} file(s):\n" + "\n".join(results[:50]) + ("\n...and more." if len(results) > 50 else "")
        except Exception as e:
            logger.error(f"File search failed: {e}")
            return f"Error during file search: {str(e)}"
