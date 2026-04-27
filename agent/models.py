from enum import Enum
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, field_validator


class RiskTier(str, Enum):
    TIER_0 = "tier_0"  # Read-only, safe
    TIER_1 = "tier_1"  # Simple UI automation, web search
    TIER_2 = "tier_2"  # File system modifications, app launches
    TIER_3 = "tier_3"  # Destructive actions, system settings, shell commands


class ActionResult(BaseModel):
    """Result of a single tool execution."""
    status: str = Field(..., description="success | failure | error | pending_approval")
    summary: str = Field(..., description="Short natural language summary of what happened")
    artifacts: List[str] = Field(default_factory=list, description="Paths to files created or modified")
    observations: Dict[str, Any] = Field(default_factory=dict, description="Structured data returned by the tool")
    changed_state: Dict[str, Any] = Field(default_factory=dict, description="System state delta (e.g. volume level)")
    needs_approval: bool = False
    retryable: bool = False
    error_message: Optional[str] = None


class TaskNode(BaseModel):
    """A single node in a multi-step execution plan."""
    node_id: str
    objective: str
    tool: str
    parameters: Dict[str, Any]
    expected_outcome: str
    risk_tier: RiskTier = RiskTier.TIER_1
    depends_on: List[str] = Field(default_factory=list, description="IDs of nodes that must finish first")
    verification_rule: str = Field("", description="Natural language rule to verify success")
    retry_limit: int = 1
    timeout: int = 60
    
    # Runtime status
    result: Optional[ActionResult] = None


class TaskPlan(BaseModel):
    """A full graph of tasks to be executed by the runtime coordinator."""
    plan_id: str
    goal: str
    nodes: List[TaskNode]
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    @field_validator('nodes')
    @classmethod
    def check_node_ids_unique(cls, v: List[TaskNode]) -> List[TaskNode]:
        ids = [node.node_id for node in v]
        if len(ids) != len(set(ids)):
            raise ValueError("All task node IDs must be unique within a plan")
        return v

    def get_node(self, node_id: str) -> Optional[TaskNode]:
        for node in self.nodes:
            if node.node_id == node_id:
                return node
        return None


class WorkflowVerification(BaseModel):
    """Verification rule for a workflow step."""
    method: str
    target: str = ""
    expected_state: str = ""


class WorkflowStep(BaseModel):
    """A single deterministic step in a local automation workflow."""
    kind: str
    action: str
    parameters: Dict[str, Any] = Field(default_factory=dict)
    verify: Optional[WorkflowVerification] = None
    timeout: int = 30
    retry_limit: int = 1
    optional: bool = False


class WorkflowRecipe(BaseModel):
    """A deterministic local automation recipe executed without planner LLM."""
    recipe_id: str
    intent_family: str
    goal: str
    steps: List[WorkflowStep]
    requires_approval: bool = False
    success_reply_key: str = "generic"
    approval_tool: str = "computer_control"
    approval_parameters: Dict[str, Any] = Field(default_factory=dict)
    risk_tier: RiskTier = RiskTier.TIER_1
    metadata: Dict[str, Any] = Field(default_factory=dict)
