from abc import ABC, abstractmethod
from typing import Callable, Any, Optional

class Action(ABC):
    """
    Abstract Base Class for all BUDDY actions.
    Ensures a unified interface across all modular capabilities.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """The tool name registered with the LLM (e.g., 'weather_report')"""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """The tool description registered with the LLM"""
        pass

    @property
    @abstractmethod
    def parameters_schema(self) -> dict:
        """The parameter schema (JSON Schema dict) for the LLM"""
        pass

    @abstractmethod
    def execute(self, parameters: dict, player: Optional[Any] = None, speak: Optional[Callable] = None, **kwargs) -> str:
        """
        Executes the action.
        Returns a string indicating success, state, or failure.
        """
        pass


class ActionRegistry:
    """Dynamic dispatch registry for all actions."""
    
    _actions: dict[str, Action] = {}

    @classmethod
    def register(cls, action_class: type[Action]):
        instance = action_class()
        cls._actions[instance.name] = instance
        return action_class

    @classmethod
    def get_action(cls, name: str) -> Optional[Action]:
        return cls._actions.get(name)

    @classmethod
    def execute(cls, name: str, parameters: dict, player: Optional[Any] = None, speak: Optional[Callable] = None, **kwargs) -> str:
        action = cls.get_action(name)
        if not action:
            raise ValueError(f"Unknown action: {name}")
        return action.execute(parameters, player, speak, **kwargs)

    @classmethod
    def get_all_declarations(cls) -> list[dict]:
        declarations = []
        for name, action in cls._actions.items():
            declarations.append({
                "name": action.name,
                "description": action.description,
                "parameters": action.parameters_schema
            })
        return declarations
