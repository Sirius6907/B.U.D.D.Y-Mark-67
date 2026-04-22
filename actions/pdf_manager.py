import os
import logging
from PyPDF2 import PdfReader, PdfMerger
from .base import Action

logger = logging.getLogger(__name__)

class PdfManagerAction(Action):
    """Extracts text from a PDF or merges multiple PDFs."""
    
    name = "pdf_manager"
    description = "Extracts text from a PDF file or merges multiple PDF files into one."
    parameters_schema = {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "description": "The action to perform: 'extract' or 'merge'.",
                "enum": ["extract", "merge"]
            },
            "input_files": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of absolute paths to the PDF files. For 'extract', only the first file is used."
            },
            "output_path": {
                "type": "string",
                "description": "Required for 'merge'. Absolute path to save the merged PDF."
            }
        },
        "required": ["action", "input_files"]
    }
    
    def execute(self, action: str, input_files: list, output_path: str = None) -> str:
        if not input_files:
            return "Error: No input files provided."
            
        try:
            if action == "extract":
                pdf_path = input_files[0]
                if not os.path.exists(pdf_path):
                    return f"Error: File not found at {pdf_path}"
                
                reader = PdfReader(pdf_path)
                text = ""
                for page in reader.pages:
                    extracted = page.extract_text()
                    if extracted:
                        text += extracted + "\n"
                return f"Extracted Text:\n{text[:2000]}" + ("\n...[truncated]" if len(text) > 2000 else "")
                
            elif action == "merge":
                if not output_path:
                    return "Error: 'output_path' is required for merging."
                    
                merger = PdfMerger()
                for pdf_path in input_files:
                    if not os.path.exists(pdf_path):
                        return f"Error: File not found at {pdf_path}"
                    merger.append(pdf_path)
                    
                os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
                merger.write(output_path)
                merger.close()
                return f"Successfully merged {len(input_files)} PDFs into {output_path}."
                
            else:
                return f"Error: Unknown action '{action}'"
        except Exception as e:
            logger.error(f"PDF operation failed: {e}")
            return f"Error performing PDF action: {str(e)}"
