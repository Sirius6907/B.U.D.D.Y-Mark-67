import os
import time
import hashlib
from pathlib import Path
from threading import Thread
import chromadb
import PyPDF2
import docx2txt

from memory.embeddings import get_embedding_function
from memory.memory_manager import LOCAL_FILES_COLLECTION

embedding_func = get_embedding_function()

class RAGIndexer:
    def __init__(self, chroma_path: str):
        self.chroma_client = chromadb.PersistentClient(path=chroma_path)
        self.collection = self.chroma_client.get_or_create_collection(
            name=LOCAL_FILES_COLLECTION,
            embedding_function=embedding_func
        )
        self.supported_extensions = {'.txt', '.md', '.pdf', '.docx', '.py'}
        self.scan_dirs = [
            Path.home() / "Documents",
            Path.home() / "Desktop",
            Path.cwd()
        ]

    def _get_file_hash(self, file_path: Path) -> str:
        """Returns a hash based on file path and modification time."""
        stats = file_path.stat()
        return hashlib.md5(f"{file_path}{stats.st_mtime}".encode()).hexdigest()

    def _extract_text(self, file_path: Path) -> str:
        ext = file_path.suffix.lower()
        try:
            if ext in {'.txt', '.md', '.py'}:
                return file_path.read_text(encoding="utf-8", errors="ignore")
            elif ext == '.pdf':
                text = ""
                with open(file_path, "rb") as f:
                    reader = PyPDF2.PdfReader(f)
                    for page in reader.pages:
                        text += page.extract_text() + "\n"
                return text
            elif ext == '.docx':
                return docx2txt.process(file_path)
        except Exception as e:
            print(f"[RAG] ❌ Failed to extract text from {file_path}: {e}")
        return ""

    def _chunk_text(self, text: str, chunk_size=800, overlap=100) -> list[str]:
        chunks = []
        if not text:
            return chunks
        
        # Simple character-based chunking with overlap
        start = 0
        while start < len(text):
            end = start + chunk_size
            chunks.append(text[start:end])
            start += chunk_size - overlap
        return chunks

    def index_files(self):
        print("[RAG] 🔍 Scanning local files for indexing...")
        for scan_dir in self.scan_dirs:
            if not scan_dir.exists():
                continue
            
            for ext in self.supported_extensions:
                for file_path in scan_dir.rglob(f"*{ext}"):
                    if ".venv" in str(file_path) or "__pycache__" in str(file_path) or ".git" in str(file_path):
                        continue
                        
                    self._process_file(file_path)
        print("[RAG] ✅ Indexing complete.")

    def _process_file(self, file_path: Path):
        file_id_base = str(file_path.absolute())
        
        # Check if file is already indexed and unchanged
        # We'll store the file hash in metadata of each chunk or a separate index tracking
        # For simplicity, we'll use a prefix in the ID to check for existence
        
        # Chroma doesn't have a direct 'check if file_path exists in metadata' efficiently without query
        # But we can store a special 'file_meta' document for each file
        meta_id = f"meta:{file_id_base}"
        current_hash = self._get_file_hash(file_path)
        
        existing_meta = self.collection.get(ids=[meta_id], include=['metadatas'])
        if existing_meta['ids']:
            if existing_meta['metadatas'][0].get('hash') == current_hash:
                # File unchanged
                return

        # Extract and Chunk
        text = self._extract_text(file_path)
        chunks = self._chunk_text(text)
        
        if not chunks:
            return

        print(f"[RAG] 📝 Indexing {file_path.name} ({len(chunks)} chunks)")

        # Clear old chunks if any
        # We need to find all chunks for this file. IDs are file_path:chunk_index
        # Actually, if the hash changed, we should just delete all previous chunks for this file
        # and re-index.
        
        # To delete all chunks for a file, we can use a query or store IDs
        # Let's use metadata to filter
        try:
            self.collection.delete(where={"file_path": str(file_path.absolute())})
        except:
            pass

        ids = []
        documents = []
        metadatas = []
        
        for i, chunk in enumerate(chunks):
            ids.append(f"{file_id_base}:{i}")
            documents.append(chunk)
            metadatas.append({
                "file_path": str(file_path.absolute()),
                "file_name": file_path.name,
                "last_modified": file_path.stat().st_mtime,
                "chunk_index": i,
                "hash": current_hash
            })

        # Batch upsert
        self.collection.upsert(ids=ids, documents=documents, metadatas=metadatas)
        
        # Store file meta
        self.collection.upsert(
            ids=[meta_id],
            documents=["FILE_METADATA"],
            metadatas=[{"hash": current_hash, "file_path": str(file_path.absolute())}]
        )

    def start_background_indexing(self):
        thread = Thread(target=self.index_files, daemon=True)
        thread.start()

def get_indexer(chroma_path: str):
    return RAGIndexer(chroma_path)
