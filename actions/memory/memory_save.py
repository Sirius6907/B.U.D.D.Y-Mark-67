from __future__ import annotations

from actions.base import Action, ActionRegistry
from memory.memory_manager import update_memory
from runtime.contracts.models import RiskLevel
from runtime.results.builder import build_tool_result

class SaveMemoryAction(Action):
    @property
    def name(self) -> str:
        return "save_memory"

    @property
    def description(self) -> str:
        return (
            "Save an important personal fact about the user to long-term memory. "
            "Call this silently whenever the user reveals something worth remembering: "
            "name, age, city, job, preferences, hobbies, relationships, projects, or future plans. "
            "Do NOT call for: weather, reminders, searches, or one-time commands. "
            "Do NOT announce that you are saving — just call it silently. "
            "Values must be in English regardless of the conversation language."
        )

    @property
    def parameters_schema(self) -> dict:
        return {
            "type": "OBJECT",
            "properties": {
                "category": {
                    "type": "STRING",
                    "description": (
                        "identity — name, age, birthday, city, job, language, nationality | "
                        "preferences — favorite food/color/music/film/game/sport, hobbies | "
                        "projects — active projects, goals, things being built | "
                        "relationships — friends, family, partner, colleagues | "
                        "wishes — future plans, things to buy, travel dreams | "
                        "notes — habits, schedule, anything else worth remembering"
                    )
                },
                "key":   {"type": "STRING", "description": "Short snake_case key (e.g. name, favorite_food, sister_name)"},
                "value": {"type": "STRING", "description": "Concise value in English (e.g. Fatih, pizza, older sister)"},
            },
            "required": ["category", "key", "value"]
        }

    def execute(self, parameters: dict, player=None, speak=None, **kwargs):
        category = parameters.get("category", "notes")
        key      = parameters.get("key", "")
        value    = parameters.get("value", "")
        
        if key and value:
            update_memory({category: {key: {"value": value}}})
            print(f"[Memory] 💾 save_memory: {category}/{key} = {value}")
            
        return build_tool_result(
            tool_name=self.name,
            operation="save",
            risk_level=RiskLevel.LOW,
            status="success",
            summary="Memory saved.",
            structured_data={"category": category, "key": key, "value": value},
            idempotent=True,
            preconditions=[],
            postconditions=["memory updated"],
        )

ActionRegistry.register(SaveMemoryAction)
