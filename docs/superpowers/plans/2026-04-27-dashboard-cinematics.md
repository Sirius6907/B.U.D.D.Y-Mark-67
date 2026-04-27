# Dashboard Cinematics Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a scene-driven cinematic boot and shutdown flow to Dashboard V2, including startup SFX, richer boot visuals, graceful shutdown choreography, and delayed close until farewell TTS finishes.

**Architecture:** Extend the websocket bridge and Electron shell with explicit shutdown orchestration while keeping Python runtime logic responsible for farewell timing. On the frontend, add boot and shutdown cinematic scene layers above the existing live dashboard and drive them from a small client-side scene state machine.

**Tech Stack:** Python, Next.js 14, React 18, Framer Motion, Electron, websocket bridge, existing dashboard V2 components

---

### Task 1: Lock The Shutdown Contract

**Files:**
- Modify: `C:\Users\opcha\Downloads\SIRIUS\BUDDY-MK67-main\dashboard_v2\bridge.py`
- Modify: `C:\Users\opcha\Downloads\SIRIUS\BUDDY-MK67-main\actions\system_actions.py`
- Test: `C:\Users\opcha\Downloads\SIRIUS\BUDDY-MK67-main\tests\test_dashboard_bridge.py`

- [ ] **Step 1: Write the failing test**

Add a test that asserts the bridge can emit a `ui.shutdown.requested` event with the farewell payload.

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests\test_dashboard_bridge.py -q`
Expected: FAIL because the new shutdown event behavior is not covered yet.

- [ ] **Step 3: Write minimal implementation**

Implement `publish_shutdown_requested()` in the bridge and make shutdown use it after the farewell begins.

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests\test_dashboard_bridge.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add dashboard_v2/bridge.py actions/system_actions.py tests/test_dashboard_bridge.py
git commit -m "feat: add dashboard shutdown event contract"
```

### Task 2: Add Frontend-Controlled Window Close

**Files:**
- Modify: `C:\Users\opcha\Downloads\SIRIUS\BUDDY-MK67-main\dashboard-v2\electron\preload.js`
- Modify: `C:\Users\opcha\Downloads\SIRIUS\BUDDY-MK67-main\dashboard-v2\electron\main.js`
- Modify: `C:\Users\opcha\Downloads\SIRIUS\BUDDY-MK67-main\dashboard-v2\lib\use-dashboard-socket.ts`

- [ ] **Step 1: Write the failing test**

Add or extend a protocol-level test to assert the frontend accepts the shutdown event without corrupting snapshot state.

- [ ] **Step 2: Run test to verify it fails**

Run: `npm test`
Expected: local test environment may still hit `spawn EPERM`; if so, record that limitation and use lint plus code inspection as the verification ceiling in this environment.

- [ ] **Step 3: Write minimal implementation**

Expose `closeWindow()` from preload, listen in Electron main, and invoke it from the socket hook when `ui.shutdown.requested` arrives.

- [ ] **Step 4: Run verification**

Run: `npm run lint`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add dashboard-v2/electron/preload.js dashboard-v2/electron/main.js dashboard-v2/lib/use-dashboard-socket.ts
git commit -m "feat: let dashboard close itself during shutdown"
```

### Task 3: Replace The Basic Boot Overlay With A Cinematic Boot Scene

**Files:**
- Modify: `C:\Users\opcha\Downloads\SIRIUS\BUDDY-MK67-main\dashboard-v2\components\boot-sequence.tsx`
- Modify: `C:\Users\opcha\Downloads\SIRIUS\BUDDY-MK67-main\dashboard-v2\app\page.tsx`
- Modify: `C:\Users\opcha\Downloads\SIRIUS\BUDDY-MK67-main\dashboard-v2\components\core-orb.tsx`

- [ ] **Step 1: Write the failing test**

Define the expected boot scene behavior in a small protocol/component-oriented way, or document the test gap if runtime visual testing is the practical verification path here.

- [ ] **Step 2: Run verification to establish baseline**

Run: `npm run lint`
Expected: PASS before UI changes.

- [ ] **Step 3: Write minimal implementation**

Refactor boot into a 7-second scene with layered reveal, richer diagnostics, orb ignition, and controlled handoff into the live dashboard.

- [ ] **Step 4: Run verification**

Run: `npm run lint`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add dashboard-v2/components/boot-sequence.tsx dashboard-v2/app/page.tsx dashboard-v2/components/core-orb.tsx
git commit -m "feat: add cinematic dashboard boot sequence"
```

### Task 4: Add Startup Sound Effect Playback

**Files:**
- Create: `C:\Users\opcha\Downloads\SIRIUS\BUDDY-MK67-main\dashboard-v2\components\boot-audio-controller.tsx`
- Create or Modify: `C:\Users\opcha\Downloads\SIRIUS\BUDDY-MK67-main\dashboard-v2\public\audio\boot-core.mp3`
- Modify: `C:\Users\opcha\Downloads\SIRIUS\BUDDY-MK67-main\dashboard-v2\app\page.tsx`

- [ ] **Step 1: Write the failing test**

Document the expected trigger contract: sound plays once during boot and never replays during normal live updates.

- [ ] **Step 2: Run baseline verification**

Run: `npm run lint`
Expected: PASS

- [ ] **Step 3: Write minimal implementation**

Add a client-only boot audio controller that plays one local startup SFX during the early boot scene.

- [ ] **Step 4: Run verification**

Run: `npm run lint`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add dashboard-v2/components/boot-audio-controller.tsx dashboard-v2/public/audio/boot-core.mp3 dashboard-v2/app/page.tsx
git commit -m "feat: add dashboard startup sound effect"
```

### Task 5: Add Cinematic Shutdown Scene

**Files:**
- Create: `C:\Users\opcha\Downloads\SIRIUS\BUDDY-MK67-main\dashboard-v2\components\shutdown-sequence.tsx`
- Modify: `C:\Users\opcha\Downloads\SIRIUS\BUDDY-MK67-main\dashboard-v2\app\page.tsx`
- Modify: `C:\Users\opcha\Downloads\SIRIUS\BUDDY-MK67-main\dashboard-v2\components\core-orb.tsx`

- [ ] **Step 1: Write the failing test**

Add a reducer/protocol test if needed for shutdown scene state handling, or explicitly rely on lint plus live flow verification if JS test execution is blocked here.

- [ ] **Step 2: Run baseline verification**

Run: `npm run lint`
Expected: PASS

- [ ] **Step 3: Write minimal implementation**

Create a core-collapse shutdown overlay that starts when `ui.shutdown.requested` is received, dims the HUD, contracts the orb, and leads into blackout before close.

- [ ] **Step 4: Run verification**

Run: `npm run lint`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add dashboard-v2/components/shutdown-sequence.tsx dashboard-v2/app/page.tsx dashboard-v2/components/core-orb.tsx
git commit -m "feat: add cinematic dashboard shutdown sequence"
```

### Task 6: Preserve Farewell Delivery Ordering

**Files:**
- Modify: `C:\Users\opcha\Downloads\SIRIUS\BUDDY-MK67-main\main.py`
- Modify: `C:\Users\opcha\Downloads\SIRIUS\BUDDY-MK67-main\actions\system_actions.py`
- Test: `C:\Users\opcha\Downloads\SIRIUS\BUDDY-MK67-main\tests\test_ui_facade.py`
- Test: `C:\Users\opcha\Downloads\SIRIUS\BUDDY-MK67-main\tests\test_personality.py`

- [ ] **Step 1: Write the failing test**

Add tests or focused assertions for shutdown ordering assumptions where practical: dashboard log first, Telegram send path available, close after speech future completion.

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests\test_ui_facade.py tests\test_personality.py -q`
Expected: FAIL if new ordering assertions are not yet implemented.

- [ ] **Step 3: Write minimal implementation**

Make shutdown wait for farewell speech completion, preserve the same farewell text across log and Telegram, then allow frontend close and backend exit.

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests\test_ui_facade.py tests\test_personality.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add main.py actions/system_actions.py tests/test_ui_facade.py tests/test_personality.py
git commit -m "fix: preserve farewell delivery before shutdown"
```

### Task 7: Full Verification

**Files:**
- Verify only

- [ ] **Step 1: Run Python verification**

Run: `python -m pytest tests\test_ui_facade.py tests\test_dashboard_bridge.py tests\test_personality.py tests\test_planner.py tests\test_tool_registry.py -q`
Expected: PASS

- [ ] **Step 2: Run frontend verification**

Run: `npm run lint`
Expected: PASS

- [ ] **Step 3: Attempt frontend tests**

Run: `npm test`
Expected: either PASS or the previously known Windows `spawn EPERM` limitation. If `EPERM` persists, record it plainly instead of claiming full JS test coverage.

- [ ] **Step 4: Manual live verification checklist**

Run manually with `python main.py`:

- confirm boot cinematic lasts about 7 seconds
- confirm startup sound plays before welcome TTS
- confirm welcome TTS starts only after boot completes
- send `shutdown`
- confirm farewell appears in dashboard log
- confirm identical farewell text appears in Telegram
- confirm TTS speaks farewell
- confirm dashboard performs cinematic collapse
- confirm Electron window closes after TTS completes
- confirm backend exits after frontend close

- [ ] **Step 5: Commit**

```bash
git add .
git commit -m "feat: complete dashboard cinematic lifecycle"
```
