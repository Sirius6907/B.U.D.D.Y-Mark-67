# Core Operations Platform Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the production core-operations platform for BUDDY with strict domain isolation, a capability registry, confidence-aware planning hooks, and the first 200 Windows-native tools.

**Architecture:** Introduce a shared runtime for contracts, validation, gating, results, verification, and telemetry; move tools into strict domain packages; publish tool capabilities into a registry layer; then integrate the planner/executor against structured capability metadata and normalized results before rolling out the first 200 tools in staged domain batches.

**Tech Stack:** Python 3.12, pytest, psutil, PowerShell, Win32/WMI/COM helpers, existing `actions` and `core.tools` registry infrastructure

---

## File Map

### Existing files to modify

- `C:\Users\opcha\Downloads\SIRIUS\BUDDY-MK67-main\actions\__init__.py`
  - Replace the flat import list with domain package loading.
- `C:\Users\opcha\Downloads\SIRIUS\BUDDY-MK67-main\core\tools\registry.py`
  - Extend `ToolSpec` with capability metadata, preconditions, postconditions, idempotency, and confidence-facing fields.
- `C:\Users\opcha\Downloads\SIRIUS\BUDDY-MK67-main\agent\executor.py`
  - Prefer the structured runtime path and capability registry lookups over legacy raw handlers.
- `C:\Users\opcha\Downloads\SIRIUS\BUDDY-MK67-main\agent\kernel.py`
  - Initialize and expose the capability registry plus planner-confidence dependencies.
- `C:\Users\opcha\Downloads\SIRIUS\BUDDY-MK67-main\README.md`
  - Update tool-count and architecture claims once the first production batches land.

### New files to create

- `C:\Users\opcha\Downloads\SIRIUS\BUDDY-MK67-main\runtime\contracts\__init__.py`
- `C:\Users\opcha\Downloads\SIRIUS\BUDDY-MK67-main\runtime\contracts\models.py`
- `C:\Users\opcha\Downloads\SIRIUS\BUDDY-MK67-main\runtime\contracts\errors.py`
- `C:\Users\opcha\Downloads\SIRIUS\BUDDY-MK67-main\runtime\results\builder.py`
- `C:\Users\opcha\Downloads\SIRIUS\BUDDY-MK67-main\runtime\gating\policy.py`
- `C:\Users\opcha\Downloads\SIRIUS\BUDDY-MK67-main\runtime\validation\common.py`
- `C:\Users\opcha\Downloads\SIRIUS\BUDDY-MK67-main\runtime\validation\files.py`
- `C:\Users\opcha\Downloads\SIRIUS\BUDDY-MK67-main\runtime\validation\network.py`
- `C:\Users\opcha\Downloads\SIRIUS\BUDDY-MK67-main\runtime\verification\files.py`
- `C:\Users\opcha\Downloads\SIRIUS\BUDDY-MK67-main\runtime\verification\process.py`
- `C:\Users\opcha\Downloads\SIRIUS\BUDDY-MK67-main\runtime\verification\network.py`
- `C:\Users\opcha\Downloads\SIRIUS\BUDDY-MK67-main\runtime\telemetry\tool_metrics.py`
- `C:\Users\opcha\Downloads\SIRIUS\BUDDY-MK67-main\registries\capability_registry.py`
- `C:\Users\opcha\Downloads\SIRIUS\BUDDY-MK67-main\registries\tool_manifest.py`
- `C:\Users\opcha\Downloads\SIRIUS\BUDDY-MK67-main\registries\domain_index.py`
- `C:\Users\opcha\Downloads\SIRIUS\BUDDY-MK67-main\registries\aliases.py`
- `C:\Users\opcha\Downloads\SIRIUS\BUDDY-MK67-main\brain\planning\confidence.py`
- `C:\Users\opcha\Downloads\SIRIUS\BUDDY-MK67-main\tests\contract\test_tool_contracts.py`
- `C:\Users\opcha\Downloads\SIRIUS\BUDDY-MK67-main\tests\contract\test_capability_registry.py`
- `C:\Users\opcha\Downloads\SIRIUS\BUDDY-MK67-main\tests\unit\test_domain_isolation.py`
- `C:\Users\opcha\Downloads\SIRIUS\BUDDY-MK67-main\tests\unit\test_runtime_gating.py`
- `C:\Users\opcha\Downloads\SIRIUS\BUDDY-MK67-main\tests\unit\test_planner_confidence.py`
- `C:\Users\opcha\Downloads\SIRIUS\BUDDY-MK67-main\tests\integration\test_executor_structured_tools.py`

### New domain packages and initial vertical-slice tool files

- `C:\Users\opcha\Downloads\SIRIUS\BUDDY-MK67-main\actions\files\__init__.py`
- `C:\Users\opcha\Downloads\SIRIUS\BUDDY-MK67-main\actions\files\file_read_metadata.py`
- `C:\Users\opcha\Downloads\SIRIUS\BUDDY-MK67-main\actions\files\file_read_text.py`
- `C:\Users\opcha\Downloads\SIRIUS\BUDDY-MK67-main\actions\files\file_write_text.py`
- `C:\Users\opcha\Downloads\SIRIUS\BUDDY-MK67-main\actions\storage\__init__.py`
- `C:\Users\opcha\Downloads\SIRIUS\BUDDY-MK67-main\actions\storage\storage_list_volumes.py`
- `C:\Users\opcha\Downloads\SIRIUS\BUDDY-MK67-main\actions\process\__init__.py`
- `C:\Users\opcha\Downloads\SIRIUS\BUDDY-MK67-main\actions\process\process_list.py`
- `C:\Users\opcha\Downloads\SIRIUS\BUDDY-MK67-main\actions\process\process_start.py`
- `C:\Users\opcha\Downloads\SIRIUS\BUDDY-MK67-main\actions\network\__init__.py`
- `C:\Users\opcha\Downloads\SIRIUS\BUDDY-MK67-main\actions\network\network_list_adapters.py`
- `C:\Users\opcha\Downloads\SIRIUS\BUDDY-MK67-main\actions\network\network_reachability_check.py`

---

### Task 1: Create Shared Contracts And Result Shapes

**Files:**
- Create: `C:\Users\opcha\Downloads\SIRIUS\BUDDY-MK67-main\runtime\contracts\__init__.py`
- Create: `C:\Users\opcha\Downloads\SIRIUS\BUDDY-MK67-main\runtime\contracts\models.py`
- Create: `C:\Users\opcha\Downloads\SIRIUS\BUDDY-MK67-main\runtime\contracts\errors.py`
- Create: `C:\Users\opcha\Downloads\SIRIUS\BUDDY-MK67-main\runtime\results\builder.py`
- Test: `C:\Users\opcha\Downloads\SIRIUS\BUDDY-MK67-main\tests\contract\test_tool_contracts.py`

- [ ] **Step 1: Write the failing contract tests**

```python
from runtime.contracts.models import RiskLevel, ToolResult, VerificationRecord
from runtime.results.builder import build_tool_result


def test_tool_result_contains_idempotency_and_state_contracts():
    result = build_tool_result(
        tool_name="file_read_metadata",
        operation="read_metadata",
        risk_level=RiskLevel.LOW,
        status="success",
        summary="metadata read",
        structured_data={"path": "C:/tmp/a.txt"},
        idempotent=True,
        preconditions=["path exists"],
        postconditions=["metadata returned"],
    )
    assert result["idempotent"] is True
    assert result["preconditions"] == ["path exists"]
    assert result["postconditions"] == ["metadata returned"]
    assert result["verification"]["status"] == "not_applicable"


def test_verification_record_defaults_to_not_applicable():
    record = VerificationRecord()
    assert record.status == "not_applicable"
    assert record.observed_state == {}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/contract/test_tool_contracts.py -v`
Expected: FAIL with `ModuleNotFoundError` for `runtime.contracts.models`

- [ ] **Step 3: Add the minimal contract models and result builder**

```python
from dataclasses import asdict, dataclass, field
from enum import StrEnum


class RiskLevel(StrEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


@dataclass(slots=True)
class VerificationRecord:
    status: str = "not_applicable"
    observed_state: dict = field(default_factory=dict)
    details: dict = field(default_factory=dict)


def build_tool_result(**kwargs) -> dict:
    verification = kwargs.pop("verification", VerificationRecord())
    result = dict(kwargs)
    result["verification"] = asdict(verification)
    result.setdefault("artifacts", [])
    result.setdefault("error_code", None)
    result.setdefault("duration_ms", 0)
    result.setdefault("reversible", False)
    result.setdefault("retryable", False)
    return result
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/contract/test_tool_contracts.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add runtime/contracts runtime/results tests/contract/test_tool_contracts.py
git commit -m "feat: add core tool contracts and result builder"
```

### Task 2: Add Capability Registry And Manifest Lookup

**Files:**
- Create: `C:\Users\opcha\Downloads\SIRIUS\BUDDY-MK67-main\registries\capability_registry.py`
- Create: `C:\Users\opcha\Downloads\SIRIUS\BUDDY-MK67-main\registries\tool_manifest.py`
- Create: `C:\Users\opcha\Downloads\SIRIUS\BUDDY-MK67-main\registries\domain_index.py`
- Create: `C:\Users\opcha\Downloads\SIRIUS\BUDDY-MK67-main\registries\aliases.py`
- Modify: `C:\Users\opcha\Downloads\SIRIUS\BUDDY-MK67-main\core\tools\registry.py`
- Test: `C:\Users\opcha\Downloads\SIRIUS\BUDDY-MK67-main\tests\contract\test_capability_registry.py`

- [ ] **Step 1: Write the failing capability-registry tests**

```python
from registries.capability_registry import CapabilityRegistry, CapabilitySpec


def test_capability_registry_indexes_aliases_and_domains():
    registry = CapabilityRegistry()
    registry.register(
        CapabilitySpec(
            tool_name="process_list",
            domain="process",
            operation="list",
            aliases=["show running tasks", "list processes"],
            risk_level="LOW",
            idempotent=True,
            preconditions=[],
            postconditions=["process snapshot returned"],
        )
    )
    assert registry.find_by_alias("list processes")[0].tool_name == "process_list"
    assert registry.list_domain("process")[0].tool_name == "process_list"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/contract/test_capability_registry.py -v`
Expected: FAIL with `ModuleNotFoundError` for `registries.capability_registry`

- [ ] **Step 3: Implement minimal capability spec and registry surface**

```python
from dataclasses import dataclass, field


@dataclass(slots=True)
class CapabilitySpec:
    tool_name: str
    domain: str
    operation: str
    aliases: list[str] = field(default_factory=list)
    risk_level: str = "LOW"
    idempotent: bool = True
    preconditions: list[str] = field(default_factory=list)
    postconditions: list[str] = field(default_factory=list)


class CapabilityRegistry:
    def __init__(self):
        self._items: dict[str, CapabilitySpec] = {}

    def register(self, spec: CapabilitySpec) -> None:
        self._items[spec.tool_name] = spec

    def find_by_alias(self, phrase: str) -> list[CapabilitySpec]:
        normalized = phrase.strip().lower()
        return [item for item in self._items.values() if normalized in {a.lower() for a in item.aliases}]

    def list_domain(self, domain: str) -> list[CapabilitySpec]:
        return [item for item in self._items.values() if item.domain == domain]
```

- [ ] **Step 4: Extend `ToolSpec` with capability metadata**

```python
@dataclass
class ToolSpec:
    name: str
    description: str
    parameters: dict
    handler: Optional[Callable[..., str]] = None
    risk_tier: RiskTier = RiskTier.LOW
    module_path: Optional[str] = None
    fn_name: Optional[str] = None
    requires_speak: bool = False
    timeout: int = 120
    domain: str = "generic"
    operation: str = "run"
    aliases: tuple[str, ...] = ()
    idempotent: bool = False
    preconditions: tuple[str, ...] = ()
    postconditions: tuple[str, ...] = ()
    verification_mode: str = "not_applicable"
```

- [ ] **Step 5: Run tests to verify registry and metadata pass**

Run: `pytest tests/contract/test_capability_registry.py tests/contract/test_tool_contracts.py -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add registries core/tools/registry.py tests/contract/test_capability_registry.py
git commit -m "feat: add capability registry and tool metadata"
```

### Task 3: Add Runtime Validation, Gating, Verification, And Telemetry

**Files:**
- Create: `C:\Users\opcha\Downloads\SIRIUS\BUDDY-MK67-main\runtime\validation\common.py`
- Create: `C:\Users\opcha\Downloads\SIRIUS\BUDDY-MK67-main\runtime\validation\files.py`
- Create: `C:\Users\opcha\Downloads\SIRIUS\BUDDY-MK67-main\runtime\validation\network.py`
- Create: `C:\Users\opcha\Downloads\SIRIUS\BUDDY-MK67-main\runtime\gating\policy.py`
- Create: `C:\Users\opcha\Downloads\SIRIUS\BUDDY-MK67-main\runtime\verification\files.py`
- Create: `C:\Users\opcha\Downloads\SIRIUS\BUDDY-MK67-main\runtime\verification\process.py`
- Create: `C:\Users\opcha\Downloads\SIRIUS\BUDDY-MK67-main\runtime\verification\network.py`
- Create: `C:\Users\opcha\Downloads\SIRIUS\BUDDY-MK67-main\runtime\telemetry\tool_metrics.py`
- Test: `C:\Users\opcha\Downloads\SIRIUS\BUDDY-MK67-main\tests\unit\test_runtime_gating.py`

- [ ] **Step 1: Write the failing gating and verification tests**

```python
from runtime.gating.policy import evaluate_gate
from runtime.validation.files import validate_existing_path
from runtime.verification.files import verify_file_written


def test_high_risk_delete_requires_approval():
    decision = evaluate_gate("HIGH", dry_run=False)
    assert decision.status == "approval_required"


def test_verify_file_written_confirms_size(tmp_path):
    target = tmp_path / "note.txt"
    target.write_text("hello", encoding="utf-8")
    record = verify_file_written(target, expected_size=5)
    assert record.status == "verified"
    assert record.observed_state["size"] == 5
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_runtime_gating.py -v`
Expected: FAIL with missing runtime modules

- [ ] **Step 3: Add the minimal gating and verification helpers**

```python
from dataclasses import dataclass
from pathlib import Path

from runtime.contracts.models import VerificationRecord


@dataclass(slots=True)
class GateDecision:
    status: str
    reason: str = ""


def evaluate_gate(risk_level: str, dry_run: bool) -> GateDecision:
    if dry_run:
        return GateDecision(status="allowed", reason="dry_run")
    if risk_level == "HIGH":
        return GateDecision(status="approval_required", reason="high_risk")
    if risk_level == "CRITICAL":
        return GateDecision(status="blocked", reason="critical_risk")
    return GateDecision(status="allowed", reason="auto")


def verify_file_written(path: Path, expected_size: int) -> VerificationRecord:
    return VerificationRecord(
        status="verified" if path.exists() and path.stat().st_size == expected_size else "failed",
        observed_state={"size": path.stat().st_size if path.exists() else None},
    )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/unit/test_runtime_gating.py tests/contract/test_tool_contracts.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add runtime/validation runtime/gating runtime/verification runtime/telemetry tests/unit/test_runtime_gating.py
git commit -m "feat: add runtime validation gating and verification"
```

### Task 4: Enforce Domain Isolation And Package-Based Action Loading

**Files:**
- Modify: `C:\Users\opcha\Downloads\SIRIUS\BUDDY-MK67-main\actions\__init__.py`
- Create: `C:\Users\opcha\Downloads\SIRIUS\BUDDY-MK67-main\tests\unit\test_domain_isolation.py`
- Create: `C:\Users\opcha\Downloads\SIRIUS\BUDDY-MK67-main\actions\files\__init__.py`
- Create: `C:\Users\opcha\Downloads\SIRIUS\BUDDY-MK67-main\actions\storage\__init__.py`
- Create: `C:\Users\opcha\Downloads\SIRIUS\BUDDY-MK67-main\actions\process\__init__.py`
- Create: `C:\Users\opcha\Downloads\SIRIUS\BUDDY-MK67-main\actions\network\__init__.py`

- [ ] **Step 1: Write the failing isolation test**

```python
from pathlib import Path


def test_domain_tools_do_not_import_other_domain_tools():
    root = Path("actions")
    forbidden = []
    for path in root.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        if "from actions." in text and "\\__init__.py" not in str(path):
            if any(part in text for part in ("from actions.files", "from actions.process", "from actions.network")):
                forbidden.append(path)
    assert forbidden == []
```

- [ ] **Step 2: Run test to verify it fails once domain files exist**

Run: `pytest tests/unit/test_domain_isolation.py -v`
Expected: FAIL after the first cross-domain import is introduced during migration

- [ ] **Step 3: Replace flat imports in `actions/__init__.py` with package loaders**

```python
from importlib import import_module

from .base import ActionRegistry


DOMAIN_PACKAGES = (
    "actions.files",
    "actions.storage",
    "actions.process",
    "actions.network",
)


for package_name in DOMAIN_PACKAGES:
    import_module(package_name)


__all__ = ["ActionRegistry"]
```

- [ ] **Step 4: Add domain package loaders that only import same-domain tool files**

```python
from importlib import import_module


for module_name in (
    "actions.files.file_read_metadata",
    "actions.files.file_read_text",
    "actions.files.file_write_text",
):
    import_module(module_name)
```

- [ ] **Step 5: Run tests to verify domain loading and isolation pass**

Run: `pytest tests/unit/test_domain_isolation.py tests/contract/test_capability_registry.py -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add actions/__init__.py actions/files actions/storage actions/process actions/network tests/unit/test_domain_isolation.py
git commit -m "refactor: add domain package loading and isolation checks"
```

### Task 5: Integrate Capability Registry And Confidence Scoring Into Planning

**Files:**
- Create: `C:\Users\opcha\Downloads\SIRIUS\BUDDY-MK67-main\brain\planning\confidence.py`
- Modify: `C:\Users\opcha\Downloads\SIRIUS\BUDDY-MK67-main\agent\kernel.py`
- Modify: `C:\Users\opcha\Downloads\SIRIUS\BUDDY-MK67-main\agent\executor.py`
- Test: `C:\Users\opcha\Downloads\SIRIUS\BUDDY-MK67-main\tests\unit\test_planner_confidence.py`
- Test: `C:\Users\opcha\Downloads\SIRIUS\BUDDY-MK67-main\tests\integration\test_executor_structured_tools.py`

- [ ] **Step 1: Write the failing planner-confidence tests**

```python
from brain.planning.confidence import score_plan_confidence


def test_native_verified_plan_scores_higher_than_ui_fallback_plan():
    native = score_plan_confidence(
        alias_match=0.95,
        preconditions_satisfied=True,
        verification_mode="verified_where_practical",
        native_first=True,
        telemetry_success_rate=0.98,
        ambiguity=0.05,
    )
    fallback = score_plan_confidence(
        alias_match=0.80,
        preconditions_satisfied=True,
        verification_mode="best_effort",
        native_first=False,
        telemetry_success_rate=0.70,
        ambiguity=0.25,
    )
    assert native > fallback
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_planner_confidence.py -v`
Expected: FAIL with missing `brain.planning.confidence`

- [ ] **Step 3: Add the confidence scorer and wire kernel access**

```python
def score_plan_confidence(
    *,
    alias_match: float,
    preconditions_satisfied: bool,
    verification_mode: str,
    native_first: bool,
    telemetry_success_rate: float,
    ambiguity: float,
) -> float:
    score = alias_match * 0.35 + telemetry_success_rate * 0.25 + (0.15 if native_first else 0.0)
    score += 0.15 if preconditions_satisfied else -0.20
    score += 0.10 if verification_mode == "verified_where_practical" else 0.0
    score -= ambiguity * 0.25
    return max(0.0, min(1.0, round(score, 4)))
```

- [ ] **Step 4: Make executor prefer structured ToolRegistry execution**

```python
if tool in kernel.tools:
    spec = kernel.tools.get_spec(tool)
    capability = kernel.capabilities.get(tool)
    logger.info("Dispatching structured tool '%s' (%s/%s)", tool, spec.domain, spec.operation)
    return kernel.tools.execute(tool, parameters, speak=speak)
```

- [ ] **Step 5: Run tests to verify confidence and executor routing pass**

Run: `pytest tests/unit/test_planner_confidence.py tests/integration/test_executor_structured_tools.py -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add brain/planning/confidence.py agent/kernel.py agent/executor.py tests/unit/test_planner_confidence.py tests/integration/test_executor_structured_tools.py
git commit -m "feat: add planner confidence scoring and structured tool routing"
```

### Task 6: Build The First Vertical Slice Across Files, Storage, Process, And Network

**Files:**
- Create: `C:\Users\opcha\Downloads\SIRIUS\BUDDY-MK67-main\actions\files\file_read_metadata.py`
- Create: `C:\Users\opcha\Downloads\SIRIUS\BUDDY-MK67-main\actions\files\file_read_text.py`
- Create: `C:\Users\opcha\Downloads\SIRIUS\BUDDY-MK67-main\actions\files\file_write_text.py`
- Create: `C:\Users\opcha\Downloads\SIRIUS\BUDDY-MK67-main\actions\storage\storage_list_volumes.py`
- Create: `C:\Users\opcha\Downloads\SIRIUS\BUDDY-MK67-main\actions\process\process_list.py`
- Create: `C:\Users\opcha\Downloads\SIRIUS\BUDDY-MK67-main\actions\process\process_start.py`
- Create: `C:\Users\opcha\Downloads\SIRIUS\BUDDY-MK67-main\actions\network\network_list_adapters.py`
- Create: `C:\Users\opcha\Downloads\SIRIUS\BUDDY-MK67-main\actions\network\network_reachability_check.py`
- Test: `C:\Users\opcha\Downloads\SIRIUS\BUDDY-MK67-main\tests\integration\test_executor_structured_tools.py`

- [ ] **Step 1: Write the failing executor integration tests**

```python
from actions import ActionRegistry


def test_vertical_slice_tools_register_in_new_domains():
    assert ActionRegistry.get_action("file_read_metadata") is not None
    assert ActionRegistry.get_action("process_list") is not None
    assert ActionRegistry.get_action("network_list_adapters") is not None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/integration/test_executor_structured_tools.py -k vertical_slice -v`
Expected: FAIL because the new tool files do not exist yet

- [ ] **Step 3: Implement one read tool and one mutating tool with verification**

```python
class FileWriteTextAction(Action):
    @property
    def name(self) -> str:
        return "file_write_text"

    @property
    def parameters_schema(self) -> dict:
        return {
            "type": "OBJECT",
            "properties": {"path": {"type": "STRING"}, "text": {"type": "STRING"}},
            "required": ["path", "text"],
        }

    def execute(self, parameters: dict, player=None, speak=None, **kwargs) -> str:
        from pathlib import Path

        from runtime.results.builder import build_tool_result
        from runtime.verification.files import verify_file_written

        path = Path(parameters["path"])
        path.write_text(parameters["text"], encoding="utf-8")
        verification = verify_file_written(path, expected_size=len(parameters["text"]))
        return build_tool_result(
            tool_name=self.name,
            operation="write_text",
            risk_level="MEDIUM",
            status="success" if verification.status == "verified" else "partial",
            summary=f"Wrote text to {path}",
            structured_data={"path": str(path)},
            idempotent=False,
            preconditions=["parent directory exists"],
            postconditions=["target file contains requested text"],
            verification=verification,
        )
```

- [ ] **Step 4: Run the vertical-slice tests**

Run: `pytest tests/integration/test_executor_structured_tools.py tests/contract/test_capability_registry.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add actions/files actions/storage actions/process actions/network tests/integration/test_executor_structured_tools.py
git commit -m "feat: add initial structured core operations tools"
```

### Task 7: Roll Out The 140 Local Tools In Domain Batches

**Files:**
- Modify: `C:\Users\opcha\Downloads\SIRIUS\BUDDY-MK67-main\registries\domain_index.py`
- Modify: `C:\Users\opcha\Downloads\SIRIUS\BUDDY-MK67-main\registries\tool_manifest.py`
- Create: `C:\Users\opcha\Downloads\SIRIUS\BUDDY-MK67-main\tests\smoke\test_local_domain_counts.py`
- Create or modify domain tool files under:
  - `C:\Users\opcha\Downloads\SIRIUS\BUDDY-MK67-main\actions\files\`
  - `C:\Users\opcha\Downloads\SIRIUS\BUDDY-MK67-main\actions\storage\`
  - `C:\Users\opcha\Downloads\SIRIUS\BUDDY-MK67-main\actions\process\`
  - `C:\Users\opcha\Downloads\SIRIUS\BUDDY-MK67-main\actions\apps\`
  - `C:\Users\opcha\Downloads\SIRIUS\BUDDY-MK67-main\actions\services\`
  - `C:\Users\opcha\Downloads\SIRIUS\BUDDY-MK67-main\actions\windows\`
  - `C:\Users\opcha\Downloads\SIRIUS\BUDDY-MK67-main\actions\input\`
  - `C:\Users\opcha\Downloads\SIRIUS\BUDDY-MK67-main\actions\clipboard\`
  - `C:\Users\opcha\Downloads\SIRIUS\BUDDY-MK67-main\actions\screen\`
  - `C:\Users\opcha\Downloads\SIRIUS\BUDDY-MK67-main\actions\printers\`

- [ ] **Step 1: Lock the local domain counts in a failing smoke test**

```python
from registries.domain_index import DOMAIN_TARGET_COUNTS


def test_local_domain_targets_match_the_approved_plan():
    assert DOMAIN_TARGET_COUNTS["files"] == 45
    assert DOMAIN_TARGET_COUNTS["storage"] == 25
    assert DOMAIN_TARGET_COUNTS["process"] == 26
    assert DOMAIN_TARGET_COUNTS["apps"] == 10
    assert DOMAIN_TARGET_COUNTS["services"] == 10
    assert DOMAIN_TARGET_COUNTS["windows"] == 8
    assert DOMAIN_TARGET_COUNTS["input"] == 5
    assert DOMAIN_TARGET_COUNTS["clipboard"] == 3
    assert DOMAIN_TARGET_COUNTS["screen"] == 4
    assert DOMAIN_TARGET_COUNTS["printers"] == 4
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/smoke/test_local_domain_counts.py -v`
Expected: FAIL until `DOMAIN_TARGET_COUNTS` is added

- [ ] **Step 3: Add the approved local-domain count map**

```python
DOMAIN_TARGET_COUNTS = {
    "files": 45,
    "storage": 25,
    "process": 26,
    "apps": 10,
    "services": 10,
    "windows": 8,
    "input": 5,
    "clipboard": 3,
    "screen": 4,
    "printers": 4,
}
```

- [ ] **Step 4: Implement the local batches in this order**

```text
Batch A: files (45) + storage (25)
Batch B: process (26) + apps (10) + services (10)
Batch C: windows (8) + input (5) + clipboard (3) + screen (4) + printers (4)
```

- [ ] **Step 5: Run smoke and contract tests after each batch**

Run: `pytest tests/smoke/test_local_domain_counts.py tests/unit/test_domain_isolation.py tests/contract/test_capability_registry.py -v`
Expected: PASS after each batch lands with no isolation violations

- [ ] **Step 6: Commit after each batch**

```bash
git add actions/files actions/storage registries/domain_index.py registries/tool_manifest.py tests/smoke/test_local_domain_counts.py
git commit -m "feat: add files and storage tool batches"

git add actions/process actions/apps actions/services
git commit -m "feat: add process app and service tool batches"

git add actions/windows actions/input actions/clipboard actions/screen actions/printers
git commit -m "feat: add ui fallback and printer tool batches"
```

### Task 8: Roll Out The 60 Connectivity Tools

**Files:**
- Modify: `C:\Users\opcha\Downloads\SIRIUS\BUDDY-MK67-main\registries\domain_index.py`
- Create: `C:\Users\opcha\Downloads\SIRIUS\BUDDY-MK67-main\tests\smoke\test_connectivity_domain_counts.py`
- Create or modify domain tool files under:
  - `C:\Users\opcha\Downloads\SIRIUS\BUDDY-MK67-main\actions\network\`
  - `C:\Users\opcha\Downloads\SIRIUS\BUDDY-MK67-main\actions\wifi\`
  - `C:\Users\opcha\Downloads\SIRIUS\BUDDY-MK67-main\actions\bluetooth\`
  - `C:\Users\opcha\Downloads\SIRIUS\BUDDY-MK67-main\actions\usb\`
  - `C:\Users\opcha\Downloads\SIRIUS\BUDDY-MK67-main\actions\serial\`
  - `C:\Users\opcha\Downloads\SIRIUS\BUDDY-MK67-main\actions\shares\`

- [ ] **Step 1: Lock the connectivity counts in a failing smoke test**

```python
from registries.domain_index import DOMAIN_TARGET_COUNTS


def test_connectivity_domain_targets_match_the_approved_plan():
    assert DOMAIN_TARGET_COUNTS["network"] == 30
    assert DOMAIN_TARGET_COUNTS["wifi"] == 8
    assert DOMAIN_TARGET_COUNTS["bluetooth"] == 8
    assert DOMAIN_TARGET_COUNTS["usb"] == 6
    assert DOMAIN_TARGET_COUNTS["serial"] == 4
    assert DOMAIN_TARGET_COUNTS["shares"] == 4
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/smoke/test_connectivity_domain_counts.py -v`
Expected: FAIL until the connectivity targets are added

- [ ] **Step 3: Add the connectivity counts and land the batches**

```python
DOMAIN_TARGET_COUNTS.update(
    {
        "network": 30,
        "wifi": 8,
        "bluetooth": 8,
        "usb": 6,
        "serial": 4,
        "shares": 4,
    }
)
```

- [ ] **Step 4: Implement the connectivity batches in this order**

```text
Batch D: network (30)
Batch E: wifi (8) + bluetooth (8)
Batch F: usb (6) + serial (4) + shares (4)
```

- [ ] **Step 5: Run smoke, contract, and executor tests after each batch**

Run: `pytest tests/smoke/test_connectivity_domain_counts.py tests/integration/test_executor_structured_tools.py tests/unit/test_runtime_gating.py -v`
Expected: PASS after each batch lands

- [ ] **Step 6: Commit after each batch**

```bash
git add actions/network actions/wifi actions/bluetooth registries/domain_index.py tests/smoke/test_connectivity_domain_counts.py
git commit -m "feat: add network wifi and bluetooth tool batches"

git add actions/usb actions/serial actions/shares
git commit -m "feat: add usb serial and share tool batches"
```

### Task 9: Finalize Planner/Registry Integration And Ship Checks

**Files:**
- Modify: `C:\Users\opcha\Downloads\SIRIUS\BUDDY-MK67-main\agent\kernel.py`
- Modify: `C:\Users\opcha\Downloads\SIRIUS\BUDDY-MK67-main\agent\executor.py`
- Modify: `C:\Users\opcha\Downloads\SIRIUS\BUDDY-MK67-main\README.md`
- Create: `C:\Users\opcha\Downloads\SIRIUS\BUDDY-MK67-main\tests\smoke\test_production_registry_counts.py`

- [ ] **Step 1: Write the final failing registry-count smoke test**

```python
from actions import ActionRegistry


def test_registry_reaches_first_production_milestone():
    assert len(ActionRegistry._actions) >= 200
```

- [ ] **Step 2: Run test to verify it fails before all batches are merged**

Run: `pytest tests/smoke/test_production_registry_counts.py -v`
Expected: FAIL until the 200-tool milestone is reached

- [ ] **Step 3: Add a final ship-check command and README update**

```text
README updates:
- replace stale "95+ tools" wording with current built-in count
- document domain isolation
- document capability registry and confidence-aware planning

Ship-check command:
pytest tests/contract tests/unit tests/integration tests/smoke -v
```

- [ ] **Step 4: Run the full verification suite**

Run: `pytest tests/contract tests/unit tests/integration tests/smoke -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add agent/kernel.py agent/executor.py README.md tests/smoke/test_production_registry_counts.py
git commit -m "feat: complete core operations platform milestone"
```
