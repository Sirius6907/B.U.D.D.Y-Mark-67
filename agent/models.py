import hashlib
from enum import Enum
from typing import List, Dict, Any, Optional, Set
from pydantic import BaseModel, Field, field_validator, model_validator


class RiskTier(str, Enum):
    TIER_0 = "tier_0"  # Read-only, safe
    TIER_1 = "tier_1"  # Simple UI automation, web search
    TIER_2 = "tier_2"  # File system modifications, app launches
    TIER_3 = "tier_3"  # Destructive actions, system settings, shell commands


class PermissionScope(str, Enum):
    """Capability-based permission scopes. Deny-by-default for unlisted scopes."""
    CAN_READ_FILES     = "can_read_files"
    CAN_WRITE_FILES    = "can_write_files"
    CAN_DELETE_FILES   = "can_delete_files"
    CAN_READ_SCREEN    = "can_read_screen"
    CAN_CONTROL_INPUT  = "can_control_input"
    CAN_LAUNCH_APP     = "can_launch_app"
    CAN_BROWSE_WEB     = "can_browse_web"
    CAN_MODIFY_SYSTEM  = "can_modify_system"
    CAN_EXECUTE_SHELL  = "can_execute_shell"
    CAN_RECORD_SCREEN  = "can_record_screen"
    CAN_SEND_MESSAGES  = "can_send_messages"
    CAN_POST_PUBLICLY  = "can_post_publicly"
    CAN_ACCESS_VAULT   = "can_access_vault"
    CAN_NETWORK_ADMIN  = "can_network_admin"
    # Kali / Security Operations
    CAN_RECON          = "can_recon"
    CAN_VULN_SCAN      = "can_vuln_scan"
    CAN_BRUTEFORCE     = "can_bruteforce"
    CAN_EXPLOIT        = "can_exploit"


# Scopes that are safe to grant by default
DEFAULT_GRANTED_SCOPES: Set[PermissionScope] = {
    PermissionScope.CAN_READ_FILES,
    PermissionScope.CAN_READ_SCREEN,
    PermissionScope.CAN_LAUNCH_APP,
    PermissionScope.CAN_BROWSE_WEB,
    PermissionScope.CAN_CONTROL_INPUT,
}

# Scopes that always require explicit approval
DANGEROUS_SCOPES: Set[PermissionScope] = {
    PermissionScope.CAN_DELETE_FILES,
    PermissionScope.CAN_EXECUTE_SHELL,
    PermissionScope.CAN_MODIFY_SYSTEM,
    PermissionScope.CAN_POST_PUBLICLY,
    PermissionScope.CAN_NETWORK_ADMIN,
    # Kali / Security Operations — always require approval
    PermissionScope.CAN_RECON,
    PermissionScope.CAN_VULN_SCAN,
    PermissionScope.CAN_BRUTEFORCE,
    PermissionScope.CAN_EXPLOIT,
}


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
    timeout: float = 60.0
    required_scopes: List[str] = Field(default_factory=list, description="PermissionScope values this node needs")
    
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
    required_scopes: List[str] = Field(default_factory=list, description="PermissionScope values this recipe needs")
    metadata: Dict[str, Any] = Field(default_factory=dict)


class DPPromotionPolicy(str, Enum):
    SESSION_ONLY = "session_only"
    STABLE_ONLY = "stable_only"
    SESSION_AND_DISK = "session_and_disk"


class SubproblemKey(BaseModel):
    normalized_goal: str
    intent_family: str
    environment_signature: str
    state_hash: str = ""
    tool_surface: str = "generic"
    schema_version: str = "dp-v2"
    surface: Optional[str] = None
    goal_hash: Optional[str] = None

    @model_validator(mode="after")
    def finalize_compat_fields(self):
        if not self.surface:
            self.surface = self.tool_surface
        if not self.tool_surface:
            self.tool_surface = self.surface or "generic"
        if not self.goal_hash:
            raw = "|".join(
                [
                    self.normalized_goal,
                    self.intent_family,
                    self.environment_signature,
                    self.state_hash,
                    self.tool_surface,
                    self.schema_version,
                ]
            )
            self.goal_hash = hashlib.sha1(raw.encode("utf-8")).hexdigest()
        return self

    @property
    def cache_key(self) -> str:
        return self.goal_hash or ""


class SubproblemValue(BaseModel):
    status: str = Field(..., description="solved | partial | failed")
    solution_steps: List[Dict[str, Any]] = Field(default_factory=list)
    verified_boundaries: Dict[str, Any] = Field(default_factory=dict)
    confidence: float = 0.5
    evidence: Dict[str, Any] = Field(default_factory=dict)
    reward_score: float = 0.0
    use_count: int = 0
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    solution_type: str = "task_plan"
    solution_payload: Dict[str, Any] = Field(default_factory=dict)
    verified_count: int = 0
    artifacts: Dict[str, Any] = Field(default_factory=dict)
    preconditions: Dict[str, Any] = Field(default_factory=dict)
    semantic_selectors: List[str] = Field(default_factory=list)
    template_variables: Dict[str, str] = Field(default_factory=dict)
    last_completed_step: int = 0
    negative_reason: Optional[str] = None
    last_used_at: Optional[str] = None
    stale_after: Optional[str] = None
    ttl_seconds: int = 0
    reuse_count: int = 0
    updated_from_result: Dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def finalize_compat_fields(self):
        if self.solution_type == "task_plan" and "recipe" in self.evidence:
            self.solution_type = "workflow_recipe"
        if self.solution_type == "task_plan" and self.solution_steps:
            first_step = self.solution_steps[0]
            if isinstance(first_step, dict) and "kind" in first_step and "action" in first_step:
                self.solution_type = "workflow_recipe"
        if not self.solution_steps and self.solution_payload:
            if self.solution_type == "workflow_recipe":
                self.solution_steps = list(self.solution_payload.get("steps", []))
            elif self.solution_type == "task_plan":
                self.solution_steps = list(self.solution_payload.get("nodes", []))
        if not self.solution_payload and self.solution_steps:
            if self.solution_type == "workflow_recipe":
                self.solution_payload = {"steps": self.solution_steps}
            elif self.solution_type == "task_plan":
                self.solution_payload = {"nodes": self.solution_steps}
        if not self.verified_boundaries and self.last_completed_step:
            self.verified_boundaries = {"last_completed_step": self.last_completed_step}
        if not self.updated_at:
            self.updated_at = self.last_used_at or self.created_at
        if not self.reuse_count and self.use_count:
            self.reuse_count = self.use_count
        if not self.use_count and self.reuse_count:
            self.use_count = self.reuse_count
        return self


class DPHit(BaseModel):
    hit_type: str = Field(..., description="exact | partial-prefix | related")
    reuse_strategy: str = Field(..., description="direct | resume | replan-tail | avoid")
    key: SubproblemKey
    value: SubproblemValue
    source: str = Field("session", description="session | disk")
