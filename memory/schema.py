from datetime import datetime
from enum import Enum
from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field


class MemoryType(str, Enum):
    SEMANTIC = "semantic"
    EPISODIC = "episodic"
    WORKFLOW = "workflow"
    ENVIRONMENT = "environment"


class MemorySensitivity(str, Enum):
    NORMAL = "normal"
    SENSITIVE = "sensitive"


class MemoryEntry(BaseModel):
    """A single structured fact in memory."""
    category: str
    key: str
    value: str
    updated: str = Field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d"))


class MemoryRecord(BaseModel):
    memory_type: MemoryType
    category: str
    key: str
    value: str
    source: str
    confidence: float
    sensitivity: MemorySensitivity = MemorySensitivity.NORMAL
    last_used: Optional[str] = None
    times_confirmed: int = 0
    decay_score: float = 0.0


class TaskEpisode(BaseModel):
    """Episodic memory of a completed task plan."""
    plan_id: str
    goal: str
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    success: bool
    nodes_summary: List[Dict[str, Any]]  # Simplified summary of what happened
    final_observation: Optional[str] = None
    learned_lesson: Optional[str] = None
