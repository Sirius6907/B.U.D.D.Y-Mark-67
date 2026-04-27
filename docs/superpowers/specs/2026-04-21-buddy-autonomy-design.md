# BUDDY MK67 Autonomy Upgrade Design

Date: 2026-04-21
Project: BUDDY MARK LXVII / Buddy-MK67
Scope: Architecture upgrade for supervised autonomy, aggressive long-term memory, Windows-first system control, and local-first hybrid voice

## Goal

Transform the current desktop assistant into a supervised autonomous Windows operator that can plan and execute multi-step tasks, remember users and workflows over time, control the local machine more reliably, and support a companion-style voice experience with local-first responsiveness.

## Product Direction

The target system is a supervised autonomous agent, not a fully unsupervised operator.

It should:
- autonomously handle read-only and low-risk actions
- ask for approval before higher-risk or sensitive actions
- learn from repeated successful workflows
- build long-term memory aggressively by default, while applying sensitivity and confidence policies
- prioritize Windows-native power over cross-platform abstraction
- use a local-first hybrid voice pipeline tuned for companion-operator behavior

It should not:
- silently perform high-impact actions such as sending messages, destructive edits, installs, purchases, or credentialed actions
- depend entirely on cloud models for every interaction
- remain a flat tool-calling loop without structured verification and recovery

## Current State

The existing codebase already provides useful building blocks:
- `main.py` contains the primary runtime, tool declarations, Gemini live audio usage, and high-level orchestration
- `agent/planner.py` generates compact JSON plans using Gemini
- `agent/executor.py` executes tools and includes replanning and generated-code fallbacks
- `agent/kernel.py` provides local model routing, a GPU lock, and deterministic retries
- `memory/memory_manager.py` provides a hybrid SQLite and Chroma memory store
- `memory/rag_indexer.py` indexes local files into Chroma for retrieval
- `actions/` contains the OS, browser, file, messaging, code, and device control capabilities

The current weaknesses are structural rather than conceptual:
- orchestration is concentrated in `main.py`
- planning is flat and step-based rather than graph-based
- execution returns mostly raw strings instead of strongly typed outcomes
- memory is broad but not policy-aware
- approvals are not formalized as a supervision layer
- voice is coupled too tightly to a single live path instead of a dedicated orchestration layer

## Proposed Architecture

Refactor the system into five explicit layers.

### 1. Perception Layer

Responsibilities:
- ingest typed input and voice input
- capture screen and environment observations
- normalize user commands into runtime-ready requests

Primary components:
- voice input loop
- screen analysis adapters
- environment sensing for apps, files, browser state, and local capabilities

### 2. Reasoning Layer

Responsibilities:
- interpret intent
- create plans
- compress context
- decide tool usage
- critique plans before execution

Primary components:
- intent router
- task planner
- risk scorer
- context assembler
- self-critique pass

### 3. Execution Layer

Responsibilities:
- enforce approval policy
- execute task graphs
- verify results
- retry safely
- record execution traces

Primary components:
- supervised task runtime
- policy engine
- tool adapter interface
- verifier
- recovery manager

### 4. Memory Layer

Responsibilities:
- store stable user facts
- record task episodes
- promote repeated workflows
- store environment intelligence
- retrieve high-value context for future tasks

Primary components:
- semantic profile memory
- episodic memory
- workflow memory
- environment memory
- retrieval and ranking policy

### 5. Voice and Persona Layer

Responsibilities:
- manage real-time voice behavior
- switch between terse and conversational response modes
- support interruption and resumption
- narrate ongoing actions appropriately

Primary components:
- local-first voice orchestrator
- voice session manager
- persona formatter
- speech summarizer

## Runtime Flow

Every task should move through the same supervised lifecycle:

`understand -> plan -> risk score -> approval gate -> execute -> verify -> reflect -> remember`

This replaces the current looser loop with a consistent runtime contract.

### Task Execution Model

The runtime should support task graphs rather than only flat sequences.

Why:
- substeps can fail independently
- retries should apply to the smallest failed unit
- completed work should not be repeated unnecessarily
- alternative branches are necessary for system control and browser automation

Each task node should contain:
- objective
- tool or sub-workflow
- parameters
- expected outcome
- risk tier
- retry policy
- verification rule
- memory hooks

## Supervision Policy

Introduce a formal tiered action policy.

### Tier 0: Read-only

Examples:
- inspect files
- read memory
- analyze screen
- gather app or browser state
- run research without modifying anything

Behavior:
- auto-execute

### Tier 1: Low-risk operational

Examples:
- open apps
- open websites
- navigate browser
- search
- draft content
- create scratch output

Behavior:
- auto-execute by default

### Tier 2: State-changing but reversible

Examples:
- edit user files
- reorganize folders
- change non-critical settings
- run scripts
- close apps
- schedule reminders

Behavior:
- ask when confidence is low, scope is broad, or previous user preference requires approval
- otherwise can auto-execute if bounded and clearly reversible

### Tier 3: High-impact or sensitive

Examples:
- send messages
- installs and removals
- destructive file operations
- credentialed actions
- purchases
- system-critical changes

Behavior:
- always require approval

### Approval Learning

Approval outcomes should be stored as episodic data so the runtime learns:
- which actions the user usually approves
- which apps and workflows are routine
- which domains are sensitive

This should influence future confidence and routing, but must never downgrade a Tier 3 action into silent execution.

## Memory Design

Replace the current broad hybrid model with four explicit memory stores backed by shared retrieval infrastructure.

### Semantic Profile Memory

Purpose:
- stable facts about the user
- preferences
- recurring projects
- contacts
- devices
- tool habits

Examples:
- preferred browser
- usual work folders
- favorite messaging platform
- recurring coding stack

### Episodic Memory

Purpose:
- records of task requests, attempts, failures, approvals, and outcomes

Examples:
- which file workflow succeeded yesterday
- which browser automation path failed
- what approval was given for a recurring task

### Workflow Memory

Purpose:
- reusable action recipes distilled from repeated successful tasks

Examples:
- update game launchers
- collect research and save a summary
- open the normal coding workspace
- prep a browser-based task flow

### Environment Memory

Purpose:
- state and capability model of the local Windows machine

Examples:
- installed apps
- common directories
- preferred browser
- local model availability
- device and audio assumptions

### Memory Metadata

Each stored memory item should carry:
- `source`
- `confidence`
- `sensitivity`
- `last_used`
- `times_confirmed`
- `decay_score`
- `category`

### Memory Policy

The system should use aggressive long-term memory by default.

That means it should automatically save:
- preferences
- projects
- recurring workflows
- environment patterns
- repeated approval behavior

But it must also:
- mark sensitive facts explicitly
- avoid blindly promoting low-confidence observations
- decay stale entries over time
- prefer reconfirmed memories over one-off guesses

## Execution Design

The current planner and executor should evolve into a supervised task runtime.

### Planner Upgrade

The new planner should:
- support hierarchical goals and subgoals
- emit task graphs instead of only linear steps
- attach expected outcomes and verification rules
- include risk tiering per step
- consume memory context selectively

### Executor Upgrade

The executor should:
- execute typed actions instead of relying on loosely structured strings
- run verification after each step
- attempt bounded recovery on failure
- replan only for remaining work
- write structured execution events to an execution journal

### Tool Adapter Contract

Action modules should return structured results such as:
- `status`
- `summary`
- `artifacts`
- `observations`
- `changed_state`
- `needs_approval`
- `retryable`

This is necessary to support verification, recovery, and memory extraction.

### Verification Layer

The runtime should not assume a tool worked just because it returned text.

Verification can include:
- checking a file exists after write
- confirming a window or app opened
- confirming browser location or page content
- validating a reminder was scheduled
- checking screen state changed as expected

## Windows-First System Control

The system should optimize for Windows-native operator power rather than portability.

### Control Priorities

Strengthen:
- browser automation
- screen-grounded clicks and typing
- app launch and focus handling
- file operations
- desktop and window management
- local code and script execution under policy
- reminders and scheduling

### Required Reliability Improvements

The operator stack should add:
- precondition checks before actions
- better fallback from semantic actions to screen-grounded actions
- app presence detection
- file path normalization
- safer destructive action handling
- richer execution traces for recovery

### Non-goal

Do not add a portability abstraction that weakens Windows behavior during this upgrade. If future cross-platform support is needed, it should be layered later on top of a stable Windows runtime.

## Voice Design

Move from a single live conversational path to a dedicated voice orchestration layer.

### Voice Goals

The voice system should feel:
- fast for short commands
- conversational for longer sessions
- interruptible
- aware of ongoing execution state
- local-first where possible

### Voice Pipeline

Primary path:
- local wake and listening
- local VAD
- local short-command interpretation when feasible
- cloud escalation for richer dialogue and deep reasoning

The system should support:
- barge-in interruption
- resumable conversations
- concise status narration during task execution
- automatic conversation summarization for long sessions

### Persona Target

The target persona is `companion-operator`.

That means:
- warmer and more natural than a terse command assistant
- still direct and operationally useful
- aware of execution state and supervision boundaries
- able to say what it is doing, what it found, and what approval it needs next

## Module Refactor Plan

This design is intended to keep existing code where possible and refactor around it.

### `main.py`

Reduce to:
- bootstrap
- UI startup
- runtime wiring
- event loop handoff

Move agent orchestration logic out of this file.

### `agent/`

Expand into:
- runtime coordinator
- planner
- policy engine
- verifier
- journal
- workflow promotion logic

### `memory/`

Refactor into:
- store abstractions
- memory policy
- retrieval ranking
- episodic recording
- workflow promotion

### `actions/`

Retain actions, but standardize their outputs and risk classification.

### `ui.py`

Expose runtime status clearly:
- current plan
- current step
- approvals pending
- last action
- voice/listening state

## Error Handling

The upgraded runtime should distinguish:
- transient execution failures
- environment mismatches
- policy blocks
- missing capabilities
- user-denied approvals

Recovery behavior should differ by class:
- retry transient issues
- inspect and adapt for environment mismatches
- stop and request approval for blocked actions
- degrade gracefully when capability is unavailable

## Testing Strategy

The implementation plan should cover:
- planner unit tests
- policy engine tests
- memory policy tests
- action adapter contract tests
- execution verification tests
- voice orchestration tests for interruption and fallback

High-value integration tests should simulate:
- multi-step supervised tasks
- repeated tasks that become workflow memories
- approval-required tasks
- file and browser workflows with recovery

## Success Criteria

The upgrade is successful when BUDDY can:
- autonomously complete multi-step low-risk Windows tasks without constant prompting
- ask for approval only when policy requires it
- remember users, workflows, environment patterns, and prior approvals over time
- recover from common execution failures without collapsing the whole task
- maintain a responsive companion-style voice experience with local-first behavior
- surface a clear execution state to the UI

## Explicit Non-Goals

This design does not include:
- full cross-platform parity
- silent execution of sensitive actions
- replacing every existing action module at once
- a purely cloud-dependent architecture

## Recommended Next Step

The next step is to create a detailed implementation plan that decomposes this design into staged code changes, starting with:
- runtime and policy architecture
- memory refactor
- structured action contract
- voice orchestration changes

## Implementation Status

- Runtime coordinator added and routed through a supervised `AgentRuntime`
- Policy engine added with explicit approval decisions
- Structured action result contract introduced for executor/runtime integration
- Deterministic verification added for file, app, and browser flows
- Memory promotion policy added for confidence- and sensitivity-aware promotion
- Voice orchestration skeleton added with interruptible response state
