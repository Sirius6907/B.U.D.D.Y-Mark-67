from __future__ import annotations

from actions.base import Action, ActionRegistry
from memory.memory_manager import search_local_files
from runtime.contracts.models import RiskLevel
from runtime.results.builder import build_tool_result

class LocalKnowledgeSearchAction(Action):
    @property
    def name(self) -> str:
        return "local_knowledge_search"

    @property
    def description(self) -> str:
        return (
            "Searches through the user's local documents, code, and files indexed via RAG. "
            "Use this when the user asks about their own files, projects, or local information "
            "that wouldn't be on the web."
        )

    @property
    def parameters_schema(self) -> dict:
        return {
            "type": "OBJECT",
            "properties": {
                "query": {"type": "STRING", "description": "The search query for local files"}
            },
            "required": ["query"]
        }

    def execute(self, parameters: dict, player=None, speak=None, **kwargs):
        query = parameters.get("query", "")
        results = search_local_files(query, n_results=5)

        if not results or not results.get('documents') or not results['documents'][0]:
            return build_tool_result(
                tool_name=self.name,
                operation="search",
                risk_level=RiskLevel.LOW,
                status="success",
                summary="No relevant local information found.",
                structured_data={"query": query, "results": []},
                idempotent=True,
                preconditions=[],
                postconditions=[],
            )

        formatted_results = ["[LOCAL KNOWLEDGE SEARCH RESULTS]"]
        extracted_docs = []
        for i in range(len(results['documents'][0])):
            doc = results['documents'][0][i]
            meta = results['metadatas'][0][i]
            path = meta.get('file_path', 'Unknown')
            formatted_results.append(f"\nSource: {path}\nContent: {doc}")
            extracted_docs.append({"source": path, "content": doc})

        return build_tool_result(
            tool_name=self.name,
            operation="search",
            risk_level=RiskLevel.LOW,
            status="success",
            summary="\n".join(formatted_results),
            structured_data={"query": query, "results": extracted_docs},
            idempotent=True,
            preconditions=[],
            postconditions=[],
        )

ActionRegistry.register(LocalKnowledgeSearchAction)
