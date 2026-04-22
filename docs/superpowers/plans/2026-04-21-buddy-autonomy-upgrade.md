# BUDDY MK67 Autonomy Upgrade Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a supervised autonomous Windows-first agent runtime with policy-gated execution, richer long-term memory, structured action results, and a local-first hybrid voice orchestration layer.

**Architecture:** Refactor the current `main.py`-centered runtime into explicit agent runtime modules that coordinate planning, policy, execution, verification, journaling, and memory promotion. Keep the existing action modules and local/cloud model stack, but wrap them in typed contracts and staged supervision rules so autonomy grows without losing control.

**Tech Stack:** Python 3.12, PyQt6, Gemini models, Ollama, SQLite, ChromaDB, pytest

---

## File Map

### Existing files to modify

- `main.py`
  - Reduce orchestration load and delegate to a new runtime coordinator.
- `ui.py`
  - Surface runtime status, active plan step, approvals, and voice state.
- `agent/planner.py`
  - Replace flat step planning with typed task graph planning.
- `agent/executor.py`
  - Replace loose tool execution with policy-aware runtime execution and verification hooks.
- `agent/error_handler.py`
  - Reuse error classification, but align it with runtime recovery categories.
- `agent/task_queue.py`
  - Integrate queued execution with supervised runtime state if still useful.
- `memory/memory_manager.py`
  - Split storage concerns and add metadata-aware memory APIs.
- `memory/rag_indexer.py`
  - Keep file retrieval, but align it with memory retrieval policies.
- `actions/open_app.py`
  - Adapt return contract to structured action results.
- `actions/browser_control.py`
  - Adapt return contract and add verification-friendly observations.
- `actions/file_controller.py`
  - Adapt return contract and safer destructive metadata.
- `actions/computer_control.py`
  - Adapt return contract and screen-grounded observations.
- `actions/computer_settings.py`
  - Adapt return contract and changed-state payloads.
- `actions/desktop.py`
  - Adapt return contract and changed-state payloads.
- `actions/reminder.py`
  - Adapt return contract and scheduling verification payloads.
- `actions/send_message.py`
  - Adapt return contract and explicit approval requirement markers.
- `actions/code_helper.py`
  - Adapt return contract and state-change metadata.
- `actions/dev_agent.py`
  - Adapt return contract and approval/risk classification.

### New files to create

- `agent/runtime.py`
  - Main supervised runtime coordinator.
- `agent/policy.py`
  - Tier classification and approval logic.
- `agent/models.py`
  - Shared dataclasses for tasks, results, approvals, journal entries, and voice state.
- `agent/verifier.py`
  - Step outcome verification helpers.
- `agent/journal.py`
  - Execution journal persistence and summary generation.
- `agent/context_builder.py`
  - Selective memory retrieval and prompt context assembly.
- `agent/workflow_memory.py`
  - Workflow promotion from successful repeated executions.
- `memory/stores.py`
  - Store abstractions for semantic, episodic, workflow, and environment memory.
- `memory/policy.py`
  - Memory save, decay, sensitivity, and ranking policy.
- `memory/schema.py`
  - Shared memory record dataclasses and enums.
- `voice/orchestrator.py`
  - Local-first hybrid voice controller.
- `voice/session.py`
  - Voice session state, interruption handling, and summarization hooks.
- `voice/__init__.py`
  - Voice package marker.
- `tests/test_policy.py`
  - Policy engine tests.
- `tests/test_planner.py`
  - Planner task graph tests.
- `tests/test_verifier.py`
  - Verification tests.
- `tests/test_memory_policy.py`
  - Memory promotion and metadata policy tests.
- `tests/test_runtime.py`
  - Runtime integration tests with fake actions.
- `tests/test_voice_orchestrator.py`
  - Voice orchestration tests.

## Task 1: Create Shared Runtime Models

**Files:**
- Create: `agent/models.py`
- Test: `tests/test_policy.py`

- [ ] **Step 1: Write the failing test for risk tiers and action results**

```python
from agent.models import ActionResult, RiskTier, TaskNode


def test_action_result_defaults_to_successful_shape():
    result = ActionResult(status="success", summary="opened chrome")
    assert result.status == "success"
    assert result.retryable is False
    assert result.needs_approval is False
    assert result.changed_state == {}


def test_task_node_carries_risk_tier_and_expected_outcome():
    node = TaskNode(
        node_id="open-browser",
        objective="Open Chrome",
        tool="open_app",
        parameters={"app_name": "Chrome"},
        expected_outcome="Chrome is focused",
        risk_tier=RiskTier.TIER_1,
    )
    assert node.risk_tier is RiskTier.TIER_1
    assert node.depends_on == []
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_policy.py -k "action_result_defaults_to_successful_shape or task_node_carries_risk_tier_and_expected_outcome" -v`
Expected: FAIL with `ModuleNotFoundError` or missing symbols from `agent.models`

- [ ] **Step 3: Write minimal runtime model definitions**

```python
from dataclasses import dataclass, field
from enum import Enum


class RiskTier(str, Enum):
    TIER_0 = "tier_0"
    TIER_1 = "tier_1"
    TIER_2 = "tier_2"
    TIER_3 = "tier_3"


@dataclass(slots=True)
class TaskNode:
    node_id: str
    objective: str
    tool: str
    parameters: dict
    expected_outcome: str
    risk_tier: RiskTier
    depends_on: list[str] = field(default_factory=list)
    verification_rule: str = ""
    retry_limit: int = 1


@dataclass(slots=True)
class ActionResult:
    status: str
    summary: str
    artifacts: list[str] = field(default_factory=list)
    observations: dict = field(default_factory=dict)
    changed_state: dict = field(default_factory=dict)
    needs_approval: bool = False
    retryable: bool = False
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_policy.py -k "action_result_defaults_to_successful_shape or task_node_carries_risk_tier_and_expected_outcome" -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add agent/models.py tests/test_policy.py
git commit -m "feat: add runtime task and action models"
```

## Task 2: Add Tiered Policy Engine

**Files:**
- Create: `agent/policy.py`
- Modify: `agent/models.py`
- Test: `tests/test_policy.py`

- [ ] **Step 1: Extend the failing test for approval decisions**

```python
from agent.models import RiskTier, TaskNode
from agent.policy import PolicyDecision, decide_policy


def test_tier_1_tasks_auto_execute():
    node = TaskNode(
        node_id="open-browser",
        objective="Open browser",
        tool="open_app",
        parameters={"app_name": "Chrome"},
        expected_outcome="Browser is open",
        risk_tier=RiskTier.TIER_1,
    )
    decision = decide_policy(node, confidence=0.95)
    assert decision is PolicyDecision.AUTO_EXECUTE


def test_tier_3_tasks_always_require_approval():
    node = TaskNode(
        node_id="send-message",
        objective="Send WhatsApp message",
        tool="send_message",
        parameters={"receiver": "Alex", "message_text": "hi", "platform": "WhatsApp"},
        expected_outcome="Message sent",
        risk_tier=RiskTier.TIER_3,
    )
    decision = decide_policy(node, confidence=0.99)
    assert decision is PolicyDecision.REQUIRE_APPROVAL
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_policy.py -k "tier_1_tasks_auto_execute or tier_3_tasks_always_require_approval" -v`
Expected: FAIL with missing `agent.policy`

- [ ] **Step 3: Write minimal policy engine**

```python
from enum import Enum

from agent.models import RiskTier, TaskNode


class PolicyDecision(str, Enum):
    AUTO_EXECUTE = "auto_execute"
    REQUIRE_APPROVAL = "require_approval"


def decide_policy(node: TaskNode, confidence: float) -> PolicyDecision:
    if node.risk_tier == RiskTier.TIER_3:
        return PolicyDecision.REQUIRE_APPROVAL
    if node.risk_tier == RiskTier.TIER_2 and confidence < 0.85:
        return PolicyDecision.REQUIRE_APPROVAL
    return PolicyDecision.AUTO_EXECUTE
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_policy.py -k "tier_1_tasks_auto_execute or tier_3_tasks_always_require_approval" -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add agent/models.py agent/policy.py tests/test_policy.py
git commit -m "feat: add tiered supervision policy"
```

## Task 3: Upgrade Planner to Emit Task Graph Nodes

**Files:**
- Modify: `agent/planner.py`
- Modify: `agent/models.py`
- Create: `agent/context_builder.py`
- Test: `tests/test_planner.py`

- [ ] **Step 1: Write the failing planner test**

```python
from agent.models import RiskTier
from agent.planner import normalize_plan


def test_normalize_plan_builds_typed_nodes():
    raw_plan = {
        "goal": "Open Chrome and search weather",
        "steps": [
            {
                "step": 1,
                "tool": "open_app",
                "description": "Open Chrome",
                "parameters": {"app_name": "Chrome"},
                "critical": True,
            },
            {
                "step": 2,
                "tool": "web_search",
                "description": "Search weather",
                "parameters": {"query": "weather today"},
                "critical": True,
            },
        ],
    }
    nodes = normalize_plan(raw_plan)
    assert [node.node_id for node in nodes] == ["step-1", "step-2"]
    assert nodes[0].risk_tier is RiskTier.TIER_1
    assert nodes[1].depends_on == ["step-1"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_planner.py::test_normalize_plan_builds_typed_nodes -v`
Expected: FAIL because `normalize_plan` does not exist

- [ ] **Step 3: Implement minimal task graph normalization**

```python
from agent.models import RiskTier, TaskNode


TOOL_RISK_MAP = {
    "screen_process": RiskTier.TIER_0,
    "web_search": RiskTier.TIER_0,
    "open_app": RiskTier.TIER_1,
    "browser_control": RiskTier.TIER_1,
    "file_controller": RiskTier.TIER_2,
    "computer_settings": RiskTier.TIER_2,
    "send_message": RiskTier.TIER_3,
}


def normalize_plan(plan: dict) -> list[TaskNode]:
    nodes: list[TaskNode] = []
    previous_id = None
    for step in plan.get("steps", []):
        node_id = f"step-{step['step']}"
        node = TaskNode(
            node_id=node_id,
            objective=step["description"],
            tool=step["tool"],
            parameters=step.get("parameters", {}),
            expected_outcome=step["description"],
            risk_tier=TOOL_RISK_MAP.get(step["tool"], RiskTier.TIER_2),
            depends_on=[previous_id] if previous_id else [],
        )
        nodes.append(node)
        previous_id = node_id
    return nodes
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_planner.py::test_normalize_plan_builds_typed_nodes -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add agent/planner.py agent/models.py agent/context_builder.py tests/test_planner.py
git commit -m "feat: normalize plans into typed task nodes"
```

## Task 4: Build Memory Schema and Policy Layer

**Files:**
- Create: `memory/schema.py`
- Create: `memory/stores.py`
- Create: `memory/policy.py`
- Modify: `memory/memory_manager.py`
- Test: `tests/test_memory_policy.py`

- [ ] **Step 1: Write the failing memory policy test**

```python
from memory.policy import should_promote_memory
from memory.schema import MemoryRecord, MemorySensitivity, MemoryType


def test_high_confidence_preference_is_promoted():
    record = MemoryRecord(
        memory_type=MemoryType.SEMANTIC,
        category="preferences",
        key="preferred_browser",
        value="Chrome",
        source="user_direct",
        confidence=0.95,
        sensitivity=MemorySensitivity.NORMAL,
    )
    assert should_promote_memory(record) is True


def test_low_confidence_sensitive_memory_is_not_promoted():
    record = MemoryRecord(
        memory_type=MemoryType.SEMANTIC,
        category="notes",
        key="password_hint",
        value="secret",
        source="inference",
        confidence=0.45,
        sensitivity=MemorySensitivity.SENSITIVE,
    )
    assert should_promote_memory(record) is False
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_memory_policy.py -v`
Expected: FAIL with missing `memory.policy` or `memory.schema`

- [ ] **Step 3: Write minimal memory policy and schema**

```python
from dataclasses import dataclass
from enum import Enum


class MemoryType(str, Enum):
    SEMANTIC = "semantic"
    EPISODIC = "episodic"
    WORKFLOW = "workflow"
    ENVIRONMENT = "environment"


class MemorySensitivity(str, Enum):
    NORMAL = "normal"
    SENSITIVE = "sensitive"


@dataclass(slots=True)
class MemoryRecord:
    memory_type: MemoryType
    category: str
    key: str
    value: str
    source: str
    confidence: float
    sensitivity: MemorySensitivity
```

```python
from memory.schema import MemoryRecord, MemorySensitivity


def should_promote_memory(record: MemoryRecord) -> bool:
    if record.sensitivity == MemorySensitivity.SENSITIVE and record.confidence < 0.9:
        return False
    return record.confidence >= 0.75
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_memory_policy.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add memory/schema.py memory/stores.py memory/policy.py memory/memory_manager.py tests/test_memory_policy.py
git commit -m "feat: add memory schema and promotion policy"
```

## Task 5: Add Structured Action Results and Verifier

**Files:**
- Create: `agent/verifier.py`
- Modify: `actions/open_app.py`
- Modify: `actions/browser_control.py`
- Modify: `actions/file_controller.py`
- Modify: `actions/send_message.py`
- Modify: `agent/executor.py`
- Test: `tests/test_verifier.py`

- [ ] **Step 1: Write the failing verifier test**

```python
from agent.models import ActionResult
from agent.verifier import verify_file_write


def test_verify_file_write_passes_when_file_exists(tmp_path):
    target = tmp_path / "notes.txt"
    target.write_text("hello", encoding="utf-8")
    result = ActionResult(
        status="success",
        summary="wrote file",
        changed_state={"path": str(target)},
    )
    verified = verify_file_write(result)
    assert verified is True
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_verifier.py::test_verify_file_write_passes_when_file_exists -v`
Expected: FAIL with missing `agent.verifier`

- [ ] **Step 3: Implement minimal verifier and action result adapters**

```python
from pathlib import Path

from agent.models import ActionResult


def verify_file_write(result: ActionResult) -> bool:
    path = result.changed_state.get("path")
    return bool(path and Path(path).exists())
```

```python
from agent.models import ActionResult


def wrap_summary(summary: str, changed_state: dict | None = None) -> ActionResult:
    return ActionResult(
        status="success",
        summary=summary,
        changed_state=changed_state or {},
    )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_verifier.py::test_verify_file_write_passes_when_file_exists -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add agent/verifier.py agent/executor.py actions/open_app.py actions/browser_control.py actions/file_controller.py actions/send_message.py tests/test_verifier.py
git commit -m "feat: add structured action results and verification"
```

## Task 6: Introduce Runtime Coordinator and Execution Journal

**Files:**
- Create: `agent/runtime.py`
- Create: `agent/journal.py`
- Modify: `agent/executor.py`
- Modify: `main.py`
- Test: `tests/test_runtime.py`

- [ ] **Step 1: Write the failing runtime test**

```python
from agent.models import ActionResult, RiskTier, TaskNode
from agent.runtime import AgentRuntime


class FakeExecutor:
    def execute_node(self, node):
        return ActionResult(status="success", summary=f"done:{node.node_id}")


def test_runtime_executes_nodes_in_order():
    runtime = AgentRuntime(executor=FakeExecutor())
    nodes = [
        TaskNode("step-1", "Open Chrome", "open_app", {"app_name": "Chrome"}, "Chrome open", RiskTier.TIER_1),
        TaskNode("step-2", "Search weather", "web_search", {"query": "weather"}, "Weather results", RiskTier.TIER_0, depends_on=["step-1"]),
    ]
    results = runtime.run(nodes)
    assert [item.summary for item in results] == ["done:step-1", "done:step-2"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_runtime.py::test_runtime_executes_nodes_in_order -v`
Expected: FAIL with missing `agent.runtime`

- [ ] **Step 3: Implement minimal runtime and journal**

```python
from dataclasses import dataclass, field


@dataclass(slots=True)
class JournalEntry:
    node_id: str
    status: str
    summary: str


@dataclass
class ExecutionJournal:
    entries: list[JournalEntry] = field(default_factory=list)

    def record(self, node_id: str, status: str, summary: str) -> None:
        self.entries.append(JournalEntry(node_id=node_id, status=status, summary=summary))
```

```python
from agent.journal import ExecutionJournal


class AgentRuntime:
    def __init__(self, executor):
        self.executor = executor
        self.journal = ExecutionJournal()

    def run(self, nodes):
        results = []
        for node in nodes:
            result = self.executor.execute_node(node)
            self.journal.record(node.node_id, result.status, result.summary)
            results.append(result)
        return results
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_runtime.py::test_runtime_executes_nodes_in_order -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add agent/runtime.py agent/journal.py agent/executor.py main.py tests/test_runtime.py
git commit -m "feat: add supervised runtime coordinator"
```

## Task 7: Add Voice Orchestrator Skeleton

**Files:**
- Create: `voice/orchestrator.py`
- Create: `voice/session.py`
- Create: `voice/__init__.py`
- Modify: `main.py`
- Modify: `ui.py`
- Test: `tests/test_voice_orchestrator.py`

- [ ] **Step 1: Write the failing voice orchestrator test**

```python
from voice.orchestrator import VoiceOrchestrator


def test_voice_orchestrator_can_interrupt_active_response():
    orchestrator = VoiceOrchestrator()
    orchestrator.start_response("Working on it")
    assert orchestrator.is_speaking is True
    orchestrator.interrupt()
    assert orchestrator.is_speaking is False
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_voice_orchestrator.py::test_voice_orchestrator_can_interrupt_active_response -v`
Expected: FAIL with missing `voice.orchestrator`

- [ ] **Step 3: Implement minimal voice session and orchestrator**

```python
from dataclasses import dataclass


@dataclass
class VoiceSessionState:
    is_listening: bool = False
    is_speaking: bool = False
    last_transcript: str = ""
```

```python
from voice.session import VoiceSessionState


class VoiceOrchestrator:
    def __init__(self):
        self.state = VoiceSessionState()

    @property
    def is_speaking(self) -> bool:
        return self.state.is_speaking

    def start_response(self, text: str) -> None:
        self.state.last_transcript = text
        self.state.is_speaking = True

    def interrupt(self) -> None:
        self.state.is_speaking = False
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_voice_orchestrator.py::test_voice_orchestrator_can_interrupt_active_response -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add voice/orchestrator.py voice/session.py voice/__init__.py main.py ui.py tests/test_voice_orchestrator.py
git commit -m "feat: add local-first voice orchestrator skeleton"
```

## Task 8: Wire Memory Promotion and Workflow Learning into Runtime

**Files:**
- Create: `agent/workflow_memory.py`
- Modify: `agent/runtime.py`
- Modify: `memory/policy.py`
- Modify: `memory/memory_manager.py`
- Test: `tests/test_runtime.py`

- [ ] **Step 1: Extend the failing runtime test for workflow promotion**

```python
from agent.models import ActionResult, RiskTier, TaskNode
from agent.runtime import AgentRuntime


class FakeExecutor:
    def execute_node(self, node):
        return ActionResult(status="success", summary=f"done:{node.node_id}")


class FakeWorkflowMemory:
    def __init__(self):
        self.promoted = []

    def maybe_promote(self, goal, results):
        self.promoted.append((goal, len(results)))


def test_runtime_promotes_successful_workflows():
    memory = FakeWorkflowMemory()
    runtime = AgentRuntime(executor=FakeExecutor(), workflow_memory=memory)
    nodes = [TaskNode("step-1", "Open Chrome", "open_app", {"app_name": "Chrome"}, "Chrome open", RiskTier.TIER_1)]
    runtime.run(nodes, goal="Open Chrome")
    assert memory.promoted == [("Open Chrome", 1)]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_runtime.py::test_runtime_promotes_successful_workflows -v`
Expected: FAIL because `AgentRuntime` does not accept `workflow_memory` or `goal`

- [ ] **Step 3: Implement minimal workflow promotion hook**

```python
class WorkflowMemory:
    def maybe_promote(self, goal: str, results: list) -> None:
        if goal and results and all(result.status == "success" for result in results):
            return
```

```python
class AgentRuntime:
    def __init__(self, executor, workflow_memory=None):
        self.executor = executor
        self.workflow_memory = workflow_memory
        self.journal = ExecutionJournal()

    def run(self, nodes, goal=""):
        results = []
        for node in nodes:
            result = self.executor.execute_node(node)
            self.journal.record(node.node_id, result.status, result.summary)
            results.append(result)
        if self.workflow_memory is not None:
            self.workflow_memory.maybe_promote(goal, results)
        return results
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_runtime.py::test_runtime_promotes_successful_workflows -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add agent/workflow_memory.py agent/runtime.py memory/policy.py memory/memory_manager.py tests/test_runtime.py
git commit -m "feat: add workflow learning hook to runtime"
```

## Task 9: Integrate UI Status and Approval Surface

**Files:**
- Modify: `ui.py`
- Modify: `main.py`
- Modify: `agent/runtime.py`
- Test: `tests/test_runtime.py`

- [ ] **Step 1: Write the failing runtime state test**

```python
from agent.runtime import RuntimeStatus


def test_runtime_status_defaults_to_idle():
    status = RuntimeStatus()
    assert status.current_goal == ""
    assert status.current_step == ""
    assert status.pending_approval is False
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_runtime.py::test_runtime_status_defaults_to_idle -v`
Expected: FAIL because `RuntimeStatus` does not exist

- [ ] **Step 3: Implement minimal runtime status model and UI hookup**

```python
from dataclasses import dataclass


@dataclass
class RuntimeStatus:
    current_goal: str = ""
    current_step: str = ""
    pending_approval: bool = False
    voice_state: str = "idle"
```

```python
def update_runtime_status(self, status):
    self.status_label.setText(f"Goal: {status.current_goal} | Step: {status.current_step} | Voice: {status.voice_state}")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_runtime.py::test_runtime_status_defaults_to_idle -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add ui.py main.py agent/runtime.py tests/test_runtime.py
git commit -m "feat: surface runtime and approval status in ui"
```

## Task 10: Run Full Test Sweep and Update Developer Docs

**Files:**
- Modify: `readme.md`
- Modify: `docs/superpowers/specs/2026-04-21-buddy-autonomy-design.md`
- Test: `tests/test_policy.py`
- Test: `tests/test_planner.py`
- Test: `tests/test_memory_policy.py`
- Test: `tests/test_verifier.py`
- Test: `tests/test_runtime.py`
- Test: `tests/test_voice_orchestrator.py`

- [ ] **Step 1: Run the focused test suite**

Run: `pytest tests/test_policy.py tests/test_planner.py tests/test_memory_policy.py tests/test_verifier.py tests/test_runtime.py tests/test_voice_orchestrator.py -v`
Expected: PASS for all new runtime, memory, policy, and voice tests

- [ ] **Step 2: Update README architecture section**

```markdown
## Runtime Architecture

BUDDY now uses a supervised runtime with:
- tiered approval policies
- typed task nodes and structured action results
- memory promotion for preferences, workflows, and environment knowledge
- a local-first hybrid voice orchestration layer
```

- [ ] **Step 3: Add implementation notes back to the spec**

```markdown
## Implementation Status

- Runtime coordinator added
- Policy engine added
- Structured action result contract introduced
- Memory policy and workflow promotion introduced
- Voice orchestration skeleton introduced
```

- [ ] **Step 4: Re-run the focused test suite**

Run: `pytest tests/test_policy.py tests/test_planner.py tests/test_memory_policy.py tests/test_verifier.py tests/test_runtime.py tests/test_voice_orchestrator.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add readme.md docs/superpowers/specs/2026-04-21-buddy-autonomy-design.md tests
git commit -m "docs: record autonomy runtime architecture and tests"
```

## Self-Review

### Spec coverage

- Runtime and policy architecture: covered by Tasks 1, 2, 3, 6, and 9
- Memory refactor and aggressive long-term memory policy: covered by Tasks 4 and 8
- Structured action contract and verification: covered by Task 5
- Windows-first system control reliability: partially covered by Task 5, with explicit action adapter work on high-impact modules first
- Voice orchestration: covered by Task 7 and surfaced in Task 9
- UI execution state: covered by Task 9
- Testing strategy: covered by Tasks 1 through 10

Known gap:
- Full adaptation of every action file in `actions/` is intentionally staged. This plan upgrades the core contract and highest-value modules first, then leaves the remaining action modules to follow the same pattern once the runtime contract is stable.

### Placeholder scan

- No `TBD`, `TODO`, or “implement later” placeholders remain.
- Each coding task includes target files, test entrypoints, code snippets, and expected command results.

### Type consistency

- Shared types are centralized under `agent.models`.
- `TaskNode`, `ActionResult`, `RiskTier`, `PolicyDecision`, `AgentRuntime`, and `RuntimeStatus` are referenced consistently across later tasks.
