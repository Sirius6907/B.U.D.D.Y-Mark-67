# BUDDY Dashboard Cinematic Boot And Shutdown Design

## Goal

Upgrade Dashboard V2 so startup and shutdown feel like a premium sci-fi command system instead of a standard app lifecycle.

The dashboard should:

- open into a stronger cinematic boot experience
- use a roughly 7 second startup sequence
- play an alien-core robotic startup sound effect before the welcome TTS
- keep the existing welcome greeting behavior after the boot sequence finishes
- perform a graceful cinematic shutdown sequence
- write the farewell message to the dashboard log
- send the exact same farewell text to Telegram
- speak the same farewell with TTS
- wait for farewell TTS to fully finish
- only then close the frontend window and the backend process

## Scope

This design covers:

- dashboard scene orchestration for boot, live, and shutdown
- startup sound-effect timing
- shutdown sequencing across UI, Telegram, and TTS
- Electron close behavior
- Next.js client rendering safety for animated HUD elements

This design does not cover:

- a full visual redesign of the entire steady-state dashboard layout
- replacing the current rendering stack
- new voice providers or LLM routing changes

## Recommended Approach

Use a scene-driven cinematic state machine inside the existing Dashboard V2 app.

Why this approach:

- It delivers a much larger quality jump than tweaking the current boot overlay.
- It is more robust than a single giant imperative animation timeline.
- It gives boot and shutdown first-class lifecycle states instead of layering more special cases onto normal runtime panels.

## User Experience

### Startup

On launch, the window opens at the current 80% centered size and enters a dedicated cinematic boot scene.

The boot experience should feel like an alien-core activation sequence:

- near-black background with slowly emerging reactor glow
- delayed reveal of the grid and HUD structure
- concentric orbital rings with staggered ignition
- glyph sweeps, scan pulses, and soft energy arcs
- telemetry awakening progressively rather than appearing instantly
- short robotic sound effect that feels synthetic, deep, and reactor-driven

Timing:

- Total cinematic boot duration: about 7 seconds
- Startup sound begins near the start of boot
- Welcome TTS begins only after boot completes
- Main dashboard becomes interactive only after boot resolves

### Shutdown

When shutdown is approved, the system enters a dedicated shutdown scene rather than closing immediately.

The shutdown experience should feel like a core-collapse sequence:

- the orb contracts inward
- outer rings destabilize and drift out of sync
- glow intensity drops in stages
- panel brightness fades down
- background grid loses energy and recedes
- final blackout pulse occurs only after farewell TTS completes

Shutdown ordering must be:

1. Write farewell text to the dashboard log
2. Send the exact same farewell text to Telegram
3. Speak the same farewell text with TTS
4. Wait until TTS finishes
5. Trigger final frontend collapse and blackout
6. Close Electron window
7. Stop websocket bridge and backend process

## Architecture

### 1. Cinematic Scene State

Introduce a frontend cinematic state layer separate from normal runtime state.

Proposed states:

- `boot_intro`
- `boot_sync`
- `boot_ready`
- `live`
- `shutdown_pending`
- `shutdown_collapse`
- `shutdown_blackout`

This layer should be driven by websocket events and local animation timing, not derived only from existing `phase`.

### 2. Shutdown Event Contract

Add a dedicated bridge event for shutdown orchestration.

Proposed event:

- `ui.shutdown.requested`

Payload:

- `farewell`: exact text that appears in dashboard log, Telegram, and TTS
- optional future extension:
  - `closeDelayMs`
  - `style`

Frontend behavior on receipt:

- enter shutdown scene
- begin collapse animation
- close only after local collapse sequence finishes

Backend behavior:

- send event after farewell pipeline starts
- do not hard-exit immediately
- only terminate after TTS completion and a short UI close grace period

### 3. Startup Audio Cue

Boot sound should be a deterministic local asset, not synthesized on the fly.

Reasoning:

- lower latency
- consistent timing
- more cinematic control
- not dependent on network or provider availability

Implementation direction:

- store a short startup sound file in dashboard assets
- expose a client-only audio player for boot
- trigger once during `boot_intro`
- keep it separate from speech output

### 4. Frontend Composition

Add a dedicated cinematic layer above the steady-state dashboard.

Suggested composition:

- `CinematicBootScene`
- `CinematicShutdownScene`
- `BootAudioController`
- `ShutdownCloseController`

The steady-state dashboard remains mounted underneath, but its visibility and energy level are controlled during boot/shutdown scenes.

### 5. Electron Close Contract

The frontend must be able to close itself after completing the shutdown animation.

Required path:

- preload exposes `closeWindow()`
- Electron main listens for dashboard close request
- close request shuts the BrowserWindow
- backend still keeps a final hard-exit fallback in case Electron hangs

## Visual Direction

### Boot

The existing boot overlay is too linear and text-heavy. Replace it with a layered reveal:

- pulse flash in the core
- orbital rings fade in at different radii
- telemetry widgets materialize as ghost wireframes before solidifying
- boot text appears in clustered bursts instead of one-line-at-a-time only
- a final lock-on sweep transitions into the live dashboard

### Shutdown

Shutdown should not feel like a browser close. It should feel like energy withdrawal:

- orb radius shrinks
- label transitions from live phase to `POWERING DOWN`
- horizontal energy line collapses inward
- ring rotation desynchronizes briefly
- ambient particles reduce rapidly
- one final core flash collapses to black

## Timing Model

### Startup Timeline

Approximate target:

- `0.0s - 1.2s`: blackout, reactor hum, first glow
- `1.2s - 3.0s`: orbital ring ignition, HUD scaffold reveal
- `3.0s - 5.2s`: diagnostics sweep, telemetry wake-up, text clusters
- `5.2s - 7.0s`: final sync pulse, lock-on sweep, transition to live dashboard
- `7.0s+`: welcome TTS starts

### Shutdown Timeline

Approximate target after farewell starts:

- `0.0s`: farewell already visible in log and sent to Telegram
- `0.0s - TTS end`: UI enters shutdown collapse state while speech plays
- `TTS end + 0.0s - 0.8s`: blackout pulse and frontend close
- `TTS end + 0.8s - 2.0s`: backend fallback exit window

## Reliability Requirements

- If TTS fails, Telegram and dashboard log must still receive the farewell.
- If Telegram fails, dashboard log and TTS must still proceed.
- If frontend close event fails, backend must still terminate after the fallback timeout.
- If frontend crashes during shutdown, backend must still exit cleanly.
- The clock and other time-based HUD elements must remain client-safe to avoid hydration mismatch.

## Testing

### Python

- shutdown action sends farewell through log path before quit
- Telegram text send is attempted before TTS synthesis
- backend shutdown fallback still exits if root close fails

### Frontend

- boot scene renders without hydration mismatch
- shutdown event drives cinematic shutdown state
- `closeWindow()` is only invoked after the shutdown scene completes

### Integration

- `python main.py` boot completes, then welcome TTS starts
- `shutdown` from Telegram produces identical farewell text in:
  - dashboard log
  - Telegram text
  - TTS speech
- Electron window closes after TTS completes
- backend exits after frontend close

## Risks

- Overly long boot timing can frustrate repeated local development loops
- Sound playback can race with TTS if not isolated cleanly
- Frontend-close timing can feel abrupt if blackout timing is too short

## Mitigations

- keep boot duration fixed around 7 seconds for now
- use a local static startup sound asset
- keep shutdown close timing configurable in code constants
- preserve a backend hard-exit fallback

## Implementation Order

1. Add cinematic state handling and shutdown event contract
2. Fix frontend-safe timing and close controls
3. Implement new boot scene visuals and timing
4. Add startup SFX playback
5. Implement shutdown collapse scene
6. Bind shutdown completion to Electron close
7. Verify TTS, Telegram, dashboard log, frontend close, backend exit sequence end to end
