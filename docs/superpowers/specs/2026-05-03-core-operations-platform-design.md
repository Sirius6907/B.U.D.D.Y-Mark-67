# BUDDY Core Operations Platform Design

Date: 2026-05-03
Project: BUDDY MARK LXVII / Buddy-MK67
Scope: Production-grade Windows-native core operations platform with a staged path to 1000 built-in tools and stronger brain integration

## Goal

Build the first production sub-project for a Windows-first AI operator that can scale to 1000+ built-in tools without collapsing into duplicated scripts, inconsistent behaviors, or fragile orchestration.

This sub-project establishes:

- a strict domain-based tool layout
- strict domain isolation between tool packages
- thin tool files backed by shared native runtime helpers
- centralized validation, risk gating, execution, verification, and result shaping
- a first batch of 200 production-grade Windows-native tools
- a capability registry and stable brain-facing interface so later planning and orchestration layers can reason over capabilities instead of ad hoc functions

The intended outcome is not a toy assistant or prototype tool bundle. It is a maintainable Windows operations platform that the higher-level brain can use to control, monitor, inspect, manage, and automate the device in a consistent and production-safe way.

## Product Direction

The target system is a Windows-native AI operating companion with broad practical control over the laptop, not a chat shell with a few convenience actions.

It should:

- expose one production tool per concrete operation
- organize tools by domain and keep implementations thin
- enforce domain isolation so tools do not import sibling-domain tools directly
- prefer native Windows APIs and stable OS surfaces over brittle hacks
- support long tool chains with structured results and verification
- distinguish clearly between read, write, destructive, and restricted behavior
- make the main brain capable of understanding messy prompts and turning them into correct tool sequences

It should not:

- depend on giant monolithic action files
- hide destructive behavior behind vague tool names
- allow every built-in tool to improvise its own validation or error format
- treat UI automation as the first or only control path when native system paths exist
- rely on generated-code fallback as the primary way to implement built-in core operations

## Scope

This design covers the first core-operations platform only.

It includes:

- shared runtime architecture for Windows-native tools
- folder layout for domain-based tool growth
- a strict tool contract schema
- a first 200-tool production batch
- risk gating and verification policy
- brain integration metadata and runtime interface

It does not include:

- the full 1000-tool implementation
- final voice persona redesign
- full long-horizon planner redesign
- new internet research or browser-first orchestration layers
- non-Windows-first cross-platform abstractions

## Required Enhancements

The finalized spec also incorporates the following approved enhancements:

- strict domain isolation with no cross-domain tool imports
- extended tool contracts with idempotency, preconditions, and postconditions
- a dedicated capability registry layer for discovery and planning
- a slight local-domain rebalance toward processes over UI-heavy tooling
- confidence scoring in the planning layer

## Approved Design Decisions

The user-approved constraints for this sub-project are:

- one file per tool
- grouped into strict domain folders
- Windows desktop and system automation first
- real native implementations, not placeholder wrappers or toy tools
- balanced local and connectivity coverage for the first batch
- first 200 tools split into 140 local tools and 60 connectivity tools
- local domains prioritized as Files + Storage first, then Processes, with UI as a fallback layer
- connectivity domains balanced, with network slightly deeper than device connectivity
- balanced risk gating:
  - LOW: auto-execute
  - MEDIUM: auto with logging and retry-safe behavior
  - HIGH: explicit approval required
  - CRITICAL: disabled or heavily sandboxed initially
- mutating tools verify post-state where practical
- read tools return structured outputs

These constraints are treated as hard design rules, not optional preferences.

## Recommended Approach

Use a hybrid staged platform:

- build a shared core runtime once
- organize tool files by domain
- keep each tool file thin and declarative
- route native execution through domain helper layers
- normalize every result into a stable machine-readable shape
- let the brain choose tools from capability metadata rather than from loose names alone

This approach is preferred over either a single giant action module or 1000 completely standalone scripts.

Why:

- it scales to 1000 tools with manageable duplication
- it enforces consistent safety and output contracts
- it allows later planner and orchestration upgrades without rewriting every tool
- it keeps room for deep native coverage per domain

## Folder Layout

The repository should move toward the following structure for the core operations platform:

```text
actions\
  files\
  storage\
  process\
  apps\
  services\
  windows\
  input\
  clipboard\
  screen\
  network\
  wifi\
  bluetooth\
  usb\
  serial\
  printers\
  shares\

runtime\
  contracts\
  execution\
  validation\
  gating\
  results\
  verification\
  powershell\
  win32\
  wmi\
  com\
  telemetry\

registries\
  capability_registry\
  tool_manifest\
  domain_index\
  aliases\

brain\
  intent\
  planning\
  routing\
  orchestration\
  response_policy\

tests\
  unit\
  integration\
  contract\
  smoke\

docs\
  tool-catalog\
  superpowers\
    specs\
    plans
```

### Layout Rules

- Root `actions\` should stop accumulating unrelated tool files.
- Every new production tool belongs to exactly one domain folder.
- One tool file equals one registered operation.
- Tool files may import only:
  - shared runtime modules
  - shared registry metadata helpers
  - same-domain private helpers when those helpers do not expose another tool
- Tool files must not import executable tools from other domains.
- Shared helpers and Windows integration code belong in `runtime\`, not in individual tool files.
- Registry metadata should be explicit and queryable rather than inferred from imports alone.
- Tests should be grouped by type so contract and safety coverage can be tracked separately from integration coverage.

## Tool File Design

Each tool file should be intentionally small and predictable.

A production tool file should do only five things:

1. declare its identity and metadata
2. declare its parameter schema
3. call shared validation helpers
4. invoke the appropriate native runtime helper
5. return a normalized result object

It should not:

- embed large PowerShell scripts inline unless unavoidable
- own its own retry policy
- perform custom risk gating logic in arbitrary ways
- construct free-form user-facing prose as its primary output
- duplicate Windows parsing logic from sibling tools
- call tool implementations from other domains directly

### Thin Tool Example Shape

```python
class FileReadMetadataAction(Action):
    @property
    def name(self) -> str:
        return "file_read_metadata"

    @property
    def description(self) -> str:
        return "Read metadata for a file or directory."

    @property
    def parameters_schema(self) -> dict:
        return {
            "type": "OBJECT",
            "properties": {
                "path": {"type": "STRING"},
            },
            "required": ["path"],
        }

    def execute(self, parameters: dict, player=None, speak=None, **kwargs) -> str:
        from runtime.validation.files import validate_existing_path
        from runtime.results.builder import build_tool_result
        from runtime.win32.files import read_path_metadata

        path = validate_existing_path(parameters["path"])
        data = read_path_metadata(path)
        return build_tool_result(
            tool_name=self.name,
            operation="read_metadata",
            risk_level="LOW",
            status="success",
            summary=f"Read metadata for {path}.",
            structured_data=data,
        )
```

The final platform may use richer types than the current `Action.execute(...)->str` surface, but the design principle remains the same: thin tool files, heavy shared runtime.

## Tool Contract Schema

Every production tool must conform to a stable machine-oriented contract.

### Request Shape

```python
class ToolRequest(TypedDict):
    tool_name: str
    operation: str
    params: dict
    correlation_id: str
    dry_run: bool
    timeout_s: int
    idempotency_key: str | None
```

### Result Shape

```python
class ToolResult(TypedDict):
    tool_name: str
    operation: str
    status: Literal["success", "error", "blocked", "approval_required", "partial"]
    risk_level: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    summary: str
    structured_data: dict
    artifacts: list[str]
    verification: dict
    reversible: bool
    retryable: bool
    duration_ms: int
    error_code: str | None
    idempotent: bool
    preconditions: list[str]
    postconditions: list[str]
```

### Contract Rules

- Read tools return rich `structured_data`.
- Mutating tools return both requested intent and observed post-state where practical.
- `summary` remains concise and machine-safe so the brain can speak over it without parsing messy prose.
- `verification` is always present, even if it reports `"not_applicable"` or `"not_performed"`.
- `error_code` should come from a shared catalog, not arbitrary strings.
- Every tool must declare whether it is idempotent under identical inputs and state.
- Every tool must publish explicit preconditions and intended postconditions for planning and verification.
- Tool outputs must be stable enough for planning, replanning, logging, and audit trails.

## Shared Runtime Architecture

The platform should execute every tool through a shared runtime pipeline:

`tool file -> validation -> risk gate -> native execution -> post-check verification -> normalized result -> telemetry`

### Runtime Layers

#### 1. Contracts

`runtime.contracts` defines:

- canonical request/result types
- metadata structures
- error codes
- verification record types
- precondition and postcondition record types
- idempotency metadata

#### 2. Validation

`runtime.validation` is responsible for:

- path validation
- parameter type checks
- enum and range checks
- hostname and share target validation
- device identifier validation
- domain-specific precondition checks

Validation must be centralized so all tools in the same domain behave consistently.

#### 3. Gating

`runtime.gating` is responsible for:

- risk tier evaluation
- approval requirements
- deny rules for dangerous or unsupported actions
- dry-run behavior where supported
- audit reasons for blocked or approval-required actions

The approved gating model is:

- `LOW`: auto-execute
- `MEDIUM`: auto-execute with logging and retry-safe expectations
- `HIGH`: explicit approval required
- `CRITICAL`: disabled or heavily sandboxed initially

#### 4. Execution

`runtime.execution` is responsible for:

- timeout enforcement
- bounded retries
- cancellation
- subprocess policy
- fallback selection between PowerShell, Win32, WMI, COM, and domain-native helpers

Tool files should not decide these behaviors independently.

#### 5. Native Integration

Windows-native helper layers should be split by stable surface:

- `runtime.win32`: files, windows, processes, handles, device and shell integration where Win32 is strongest
- `runtime.wmi`: system inventory, adapters, services, hardware, event-friendly system state
- `runtime.com`: shell/application control where COM gives the cleanest interface
- `runtime.powershell`: stable command orchestration and typed parsing for Windows features exposed best by PowerShell

Native-first policy:

- prefer Win32, COM, WMI, or Windows-native APIs where feasible
- use PowerShell where it is the most stable operational surface
- avoid using UI automation for tasks that have a native system path

#### 6. Verification

`runtime.verification` is responsible for checking post-state where practical.

Examples:

- file creation checks the file exists and matches expected metadata
- rename checks the old path is absent and the new path exists
- process start checks the process is running
- service stop checks service state transitioned
- network profile change checks observed adapter/config state

Read tools do not need post-mutation checks, but their outputs still need schema consistency.

#### 7. Results

`runtime.results` is responsible for:

- creating normalized success and error payloads
- attaching verification records
- attaching artifact paths
- setting retryability and reversibility hints
- keeping summaries concise and planner-safe

#### 8. Telemetry

`runtime.telemetry` is responsible for:

- latency
- call counts
- error counts
- approval frequency
- verification pass/fail rates
- domain-level reliability tracking

This telemetry becomes critical later for tool ranking and planner confidence.

## Capability Registry Layer

Capability discovery should be its own layer rather than an incidental property of imports.

`registries.capability_registry` is responsible for:

- storing tool capability metadata in one queryable index
- exposing tool lookup by domain, verb, aliases, risk level, and read/write class
- exposing preconditions, postconditions, idempotency, verification support, and latency hints
- supporting planner search without requiring the brain to inspect Python modules directly

This registry should become the planner’s source of truth for candidate tool discovery.

Each tool registration should emit:

- canonical tool name
- domain
- operation verb
- synonyms and intent aliases
- risk level
- idempotent flag
- preconditions
- postconditions
- verification support mode
- reversible flag
- retryable flag
- native-first or UI-fallback classification

## Risk Model

The risk model is part of the core platform, not a side feature.

### LOW

Examples:

- read file metadata
- list processes
- get disk usage
- inspect network adapters

Behavior:

- auto-execute
- structured result required

### MEDIUM

Examples:

- create file
- move file in user space
- launch application
- save report
- connect to a known share

Behavior:

- auto-execute with full logging
- should remain retry-safe where possible
- verify post-state where practical

### HIGH

Examples:

- delete files
- terminate processes
- disable services
- change network configuration
- remove startup entries

Behavior:

- explicit approval required
- must clearly state requested action scope before execution
- strong verification required where practical

### CRITICAL

Examples:

- destructive disk operations
- registry changes with system-wide impact
- partitioning
- firewall profile rewrites across the machine
- irreversible system-level changes

Behavior:

- disabled or heavily sandboxed in the initial platform
- must not silently degrade into execution via another helper path

## First 200 Tool Domain Map

The first implementation batch is intentionally broad but not shallow:

- `140 local tools`
- `60 connectivity tools`

### Local Tool Distribution

- Files: `45`
- Storage: `25`
- Processes: `26`
- Apps: `10`
- Services: `10`
- Windows: `8`
- Input: `5`
- Clipboard: `3`
- Screen: `4`
- Printers (local side): `4`

### Connectivity Tool Distribution

- Network: `30`
- Wi-Fi: `8`
- Bluetooth: `8`
- USB: `6`
- Serial/COM ports: `4`
- Shares/remote discovery: `4`

### Local Priority Rationale

The local batch prioritizes Files + Storage first, then Processes. UI-oriented domains are present but intentionally lighter because UI automation should be a fallback control layer when native system APIs are available.

### Connectivity Priority Rationale

Connectivity remains balanced, but the network stack gets deeper coverage first because it provides stronger practical monitoring, diagnostics, reachability checks, and environmental awareness for the future brain.

## First Batch Domain Intent

The first 200 tools should cover the machine’s most useful operator primitives.

### Files

This domain should include tools for:

- file and directory creation
- reading text and metadata
- writing and appending
- copy, move, rename
- deletion with gating
- hashing
- permissions inspection
- bulk search and filtering
- recent file inspection
- archive handoff integration

### Storage

This domain should include tools for:

- drive and volume inventory
- free space and utilization
- mount point and filesystem information
- removable media detection
- storage health surfaces available through native Windows interfaces
- directory size and tree summaries
- cleanup-safe inspection tools

### Processes

This domain should include tools for:

- process inventory
- process detail inspection
- launch and terminate operations
- parent-child relationships
- resource usage surfaces
- priority and affinity controls where safe
- module inspection and path discovery

### Apps

This domain should include tools for:

- installed software inventory
- app launch by path or known identity
- app existence checks
- focused app state helpers
- default application resolution where practical

### Services

This domain should include tools for:

- list services
- inspect service state
- start service
- stop service
- restart service
- startup type inspection and controlled mutation with gating

### Windows

This domain should include tools for:

- enumerate windows
- find active window
- focus
- minimize
- maximize
- move/resize
- close with gating where needed

### Input

This domain should include tools for:

- click
- move cursor
- scroll
- type text
- press keys
- send hotkeys
- controlled sequences for fallback UI flows

### Clipboard

This domain should include tools for:

- read clipboard text
- write clipboard text
- clear clipboard
- inspect clipboard formats at a basic level

### Screen

This domain should include tools for:

- full screenshot
- region screenshot
- current monitor inventory
- basic screen geometry/state helpers

### Printers

This domain should include tools for:

- local printer inventory
- default printer inspection
- queue inspection where practical
- connectivity/status read operations

### Network

This domain should include tools for:

- adapter inventory
- IP configuration read
- DNS configuration read
- route table read
- port and socket inventory
- reachability checks
- local network diagnostics
- firewall profile inspection
- connection summaries

### Wi-Fi

This domain should include tools for:

- adapter state
- current SSID/profile inspection
- scan results where available
- saved profile inventory
- connect/disconnect behaviors with gating

### Bluetooth

This domain should include tools for:

- adapter state
- paired device inventory
- nearby discoverable scans where supported
- connect/disconnect and trust-state operations with gating

### USB

This domain should include tools for:

- attached USB inventory
- device detail inspection
- removable device state
- event-friendly device awareness

### Serial / COM Ports

This domain should include tools for:

- COM port inventory
- port metadata
- openability or availability checks
- device-to-port mapping where practical

### Shares / Remote Discovery

This domain should include tools for:

- local share inventory
- remote share reachability checks
- mapped drive/share status
- nearby share or host discovery where feasible without drifting into intrusive scanning

## Brain Integration Interface

The future brain should consume capabilities, metadata, and structured results rather than loose strings and handwritten heuristics.

### Capability Model

Each tool should publish metadata including:

- tool name
- domain
- operation verb
- intent aliases
- parameter schema
- risk level
- read/write classification
- idempotent or non-idempotent behavior
- retryability
- reversibility
- preconditions
- postconditions
- verification support
- estimated latency class
- whether the tool requires UI focus
- whether it is native-first or UI-fallback

This metadata should be queryable from a registry index.

### Brain Responsibilities

The brain layer should be able to:

- interpret messy user prompts into goals, constraints, and entities
- search candidate tools by capability metadata
- prefer read/inspect tools first when context is incomplete
- plan multi-step sequences with preconditions and postconditions
- score candidate plans by confidence before execution
- request approval when the next step crosses a HIGH gate
- replan on failure, timeout, blocked action, or failed verification
- summarize actions in concise operator-style language

### Planner Confidence Scoring

The planning layer should assign a confidence score to candidate plans and major steps.

Confidence should consider:

- match strength between user intent and capability aliases
- whether required entities were resolved cleanly
- whether preconditions are satisfied
- whether the chosen tool is native-first or only a UI fallback
- recent reliability telemetry for the tool or domain
- ambiguity remaining after the inspect phase

Low-confidence plans should bias toward:

- more read/inspect steps before mutation
- narrower-scoped actions
- explicit approval or clarification when risk and ambiguity intersect

### Sequence Design Principle

The brain should operate with a staged tool usage model:

1. understand request
2. inspect state
3. choose safe tool path
4. execute mutation if needed
5. verify result
6. replan if mismatch remains

This allows the system to feel more like a competent operator than a text assistant guessing at actions.

### User-Facing Language Policy

Tools should not own final phrasing beyond concise summary fields.

The brain should decide:

- what to say before execution
- how to ask for approval
- how much detail to expose during long chains
- how to summarize final outcomes

This separation is required for future voice, persona, and long-horizon orchestration work.

## Testing Strategy

This platform must be test-first and contract-heavy.

Each new tool should have:

- unit tests for validation and helper behavior
- contract tests for request/result shape
- integration tests for safe native execution paths
- smoke tests for registry visibility and execution readiness

Platform-wide test goals:

- all tools register correctly
- risk tiers are explicitly declared
- contract output is stable
- HIGH and CRITICAL tools cannot bypass gating
- verification records are attached where expected

The first 200-tool batch should not be treated as complete until registry, contract, and gating coverage are all reliable.

## Migration Strategy

The current repository already has tools registered through `ActionRegistry` and partial strict registry support in `core.tools.registry`.

The migration path for this sub-project should be:

1. establish shared runtime contracts and helpers
2. establish domain folder structure
3. introduce manifest and capability metadata
4. introduce capability registry lookup surfaces for the planner
5. migrate or replace existing overlapping tools domain by domain
6. register first 200 tools through the new structure
7. adapt the brain/runtime to prefer structured results and capability registry lookups from the new platform

The existing system should remain runnable during migration. This is an incremental platform build, not a full stop-and-rewrite.

## Success Criteria

This sub-project is successful when:

- the repository has a clear domain-based structure for production tools
- the first 200 tools are implemented as thin files over shared native helpers
- all tools share one contract model for validation, execution, and result shaping
- all tools obey domain isolation rules
- mutating tools verify post-state where practical
- read tools return structured outputs consistently
- the risk gating model is enforced centrally
- the capability registry is the planner’s source of discovery truth
- the brain can query capabilities, score plans by confidence, and consume structured results without relying on tool-specific parsing

## Next Step

The next phase after this design is a concrete implementation plan for:

- shared runtime scaffolding
- domain folder migration
- manifest and registration architecture
- first 200-tool rollout in staged batches
- brain integration points for capability lookup and structured execution results
