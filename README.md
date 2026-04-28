<div align="center">

# 🤖 B.U.D.D.Y — Mark 67

### **B**iometric **U**tility & **D**igital **D**esktop **Y**ield

**An autonomous AI agent that sees your screen, understands context, plans multi-step tasks, and executes them — with voice interaction, self-correcting verification, and governed security tooling.**

[![Python 3.12+](https://img.shields.io/badge/Python-3.12+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Windows](https://img.shields.io/badge/Windows-10%2F11-0078D6?style=for-the-badge&logo=windows&logoColor=white)]()
[![Tests](https://img.shields.io/badge/Tests-309%20Passing-2EA043?style=for-the-badge&logo=pytest&logoColor=white)]()
[![Tools](https://img.shields.io/badge/Tools-95+-FF6F00?style=for-the-badge&logo=gear&logoColor=white)]()
[![License](https://img.shields.io/badge/License-Proprietary-E53935?style=for-the-badge)](LICENSE)

---

*Built by [Sirius](https://github.com/Sirius6907) — a solo developer who believes AI assistants should do real work, not just chat.*

</div>

---

## What Is B.U.D.D.Y?

B.U.D.D.Y is a **Windows-native autonomous AI agent** that operates directly on your desktop. Unlike chatbots that only generate text, B.U.D.D.Y can:

- **See your screen** — captures and understands UI state through vision models
- **Control your computer** — opens apps, manages files, adjusts settings, automates browsers
- **Plan and execute** — breaks complex requests into multi-step task plans
- **Self-correct** — verifies each action and retries or re-plans on failure
- **Talk to you** — real-time voice input/output with push-to-talk or continuous listening
- **Run security tools** — governed Kali Linux integration for ethical hacking and pentesting
- **Learn from you** — remembers preferences, indexes your documents, builds context over time

This is not a wrapper around a Chatbot. This is a **supervised autonomous runtime** with 95+ native tools, a policy engine, rollback capabilities, and a real execution loop.

---

## Table of Contents

- [Core Architecture](#core-architecture)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Installation](#installation)
- [Usage](#usage)
- [Kali Linux Integration](#kali-linux-integration)
- [Benchmarks](#benchmarks)
- [Security Model](#security-model)
- [System Requirements](#system-requirements)
- [Roadmap](#roadmap)
- [Contributing](#contributing)
- [License](#license)

---

## Core Architecture

### The OPEV Loop — Observe · Plan · Execute · Verify

Every task B.U.D.D.Y runs follows a self-correcting execution loop:

```
┌─────────────────────────────────────────────────────────────────┐
│                        User Command                             │
│                    (voice, text, or Telegram)                    │
└────────────────────────────┬────────────────────────────────────┘
                             ▼
                    ┌─────────────────┐
                    │    OBSERVE      │  Screen capture + context
                    │  (Vision + RAG) │  gathering via VLM
                    └────────┬────────┘
                             ▼
                    ┌─────────────────┐
                    │      PLAN       │  LLM breaks task into
                    │  (Gemini/OR)    │  ordered TaskNodes
                    └────────┬────────┘
                             ▼
                    ┌─────────────────┐
                    │    EXECUTE      │  Dispatch tools from
                    │  (95+ tools)    │  registry with policy gates
                    └────────┬────────┘
                             ▼
                    ┌─────────────────┐
                    │     VERIFY      │  Rule-based + optional
                    │  (Hybrid)       │  VLM screenshot check
                    └────────┬────────┘
                             ▼
                  ┌──────────┴──────────┐
                  │  Pass?              │
                  │  YES → next step    │
                  │  NO  → re-plan/retry│
                  └─────────────────────┘
```

The Verify stage uses a **hybrid engine**: rule-based checks for fast confirmation, and VLM screenshot analysis (Gemini Flash) for critical UI actions. Vision verification runs async with an 8-second timeout — it never blocks the pipeline.

### LLM Routing

B.U.D.D.Y doesn't depend on a single model. It routes intelligently across providers:

| Layer | Model | Purpose |
|---|---|---|
| **Primary** | OpenRouter (configurable) | Fast reasoning, task planning |
| **Fallback** | Gemini 2.5 Flash / Pro | Deep reasoning, vision analysis |
| **Embeddings** | `all-MiniLM-L6-v2` (local) | RAG document retrieval — runs offline |

Routing is handled by `agent/llm_gateway.py` with automatic failover. If OpenRouter is down, B.U.D.D.Y switches to Gemini seamlessly. If both fail, it queues the task and tells you.

### Policy Engine

Every action passes through a risk-tiered approval system:

| Risk Tier | Examples | Approval Required? |
|---|---|---|
| **TIER 0** | Read system info, check weather | No — auto-approved |
| **TIER 1** | Open apps, manage files, web search | No — logged only |
| **TIER 2** | Change settings, install software | Yes — user confirmation |
| **TIER 3** | Run exploits, modify registry, delete data | Yes — explicit approval with explanation |

---

## Features

### 🖥️ Desktop Automation — 70+ Native Tools

Full native control over Windows — apps, files, windows, mouse, keyboard, clipboard, volume, wallpaper, power management, system settings, and more. All tools are registry-dispatched with lazy loading for fast startup.

| Category | Tools | What They Do |
|---|---|---|
| **Desktop** | `open_app`, `desktop`, `window_manager`, `wallpaper_changer` | Launch apps, manage windows, change wallpaper |
| **Input** | `mouse_controller`, `keyboard_controller`, `clipboard_manager` | Simulate clicks, keystrokes, clipboard ops |
| **Files** | `file_controller`, `file_searcher`, `zip_manager`, `pdf_manager` | Create, move, search, compress, read PDFs |
| **System** | `system_info`, `system_diagnostics`, `power_manager` | Hardware info, diagnostics, sleep/shutdown |
| **Settings** | `computer_settings`, `volume_controller`, `wifi_manager` | Sound, display, network, bluetooth |
| **Security** | `firewall_manager`, `antivirus_manager`, `process_shield` | Firewall rules, AV scans, process protection |
| **Browser** | `browser_control`, `web_search`, `youtube_video` | Autonomous browsing, search, video playback |
| **Dev** | `code_helper`, `dev_agent`, `ide_tracker` | Write code, execute scripts, track IDE state |
| **Vision** | `screen_processor`, `screen_recorder`, `camera_capture` | Screenshots, recording, camera access |
| **Comms** | `send_message`, `email_client`, `reminder` | Messages, emails, scheduled reminders |
| **Maintenance** | `backup_manager`, `disk_analyzer`, `system_optimizer` | Backups, disk usage, performance tuning |

### 🔐 Kali Linux Integration — 25 Governed Security Tools

B.U.D.D.Y bridges to a WSL Kali Linux environment for real ethical hacking, bug bounty, and penetration testing — all governed by target allowlisting and permission scopes.

| Tier | Tools | Risk Level |
|---|---|---|
| **Tier 1** — Passive Recon | nmap, whois, searchsploit, subfinder, amass, whatweb, dnsrecon | Low |
| **Tier 2** — Active Scanning | nikto, gobuster, ffuf, nuclei, wpscan, masscan, dirb, enum4linux | Medium |
| **Tier 3** — Exploitation | hydra, john, hashcat, sqlmap, msfconsole, evil-winrm, crackmapexec | High |

Every Kali operation requires explicit approval. Targets must be allowlisted in `~/.buddy/kali_targets.json`. `localhost` and `127.0.0.1` are pre-authorized by default.

### 👁️ Vision Intelligence

Screen capture via `mss` → VLM analysis via Gemini → semantic understanding of UI state. Used for both autonomous navigation and verification of completed actions.

### 🎙️ Voice Interface

Dual-provider voice routing:
- **Sarvam AI** (primary) — low-latency STT/TTS optimized for Indian English
- **Gemini** (fallback) — broad multilingual support

Push-to-talk and continuous listening modes. Audio playback synced with UI animations.

### 🧠 Memory & RAG

Three-tier memory architecture:

| Layer | Backend | Purpose |
|---|---|---|
| **Transient** | In-memory buffer | Current conversation context |
| **Structured** | SQLite | User preferences, execution logs, profiles |
| **Semantic** | ChromaDB (HNSW) | Local document search via vector embeddings |

RAG indexes local files (`.pdf`, `.docx`, `.py`, `.md`) incrementally — only re-processes files whose MD5 hash has changed. Embeddings run locally via `all-MiniLM-L6-v2` — your documents never leave your machine.

### 🌐 Browser Automation

Playwright-based autonomous browsing with self-healing selectors, session persistence, and context stripping (ads/navigation noise removed before LLM processing).

### 💻 Developer Engine

Code writing, execution, and debugging in isolated subprocesses. Reads stderr on failure and re-plans automatically. Supports Python, JavaScript, PowerShell, batch scripts, and more.

### 📱 Telegram Bridge

Remote OS control via encrypted Telegram bot. Locked to a single `TELEGRAM_USER_ID` — nobody else can control your machine.

### 💼 Career Orchestrator

Automated job search pipeline: LinkedIn scraping → job matching → application drafting → referral discovery → GitHub portfolio management. All with human approval gates.

### 📊 Benchmark Harness

Built-in testing framework for measuring B.U.D.D.Y's performance across safety, accuracy, performance, and adversarial scenarios.

---

## Tech Stack

### Core Runtime

| Technology | Version | Purpose |
|---|---|---|
| **Python** | 3.12+ | Core language — async-first, type-annotated |
| **Pydantic** | 2.0+ | Data validation, model serialization |
| **PyQt6** | 6.6+ | Desktop UI with glassmorphic design |
| **asyncio** | stdlib | Async task orchestration |

### AI & LLM

| Technology | Purpose |
|---|---|
| **Google Gemini** (2.5 Flash/Pro) | Vision analysis, planning, fallback reasoning |
| **OpenRouter** | Primary LLM routing (model-agnostic) |
| **sentence-transformers** | Local embedding generation (`all-MiniLM-L6-v2`) |
| **ChromaDB** | Vector database for semantic document search |

### Desktop & System

| Technology | Purpose |
|---|---|
| **pywinauto** | Windows UI automation framework |
| **pyautogui** | Mouse/keyboard simulation |
| **mss** | High-performance screen capture |
| **opencv-python** | Image processing and vision pipeline |
| **psutil** | System monitoring and process management |
| **Playwright** | Browser automation with Chromium |

### Voice & Audio

| Technology | Purpose |
|---|---|
| **Sarvam AI API** | Primary STT/TTS provider |
| **Gemini Audio** | Fallback voice processing |
| **sounddevice / pyaudio** | Audio capture from microphone |
| **pyttsx3** | Offline TTS fallback |

### Security & Communications

| Technology | Purpose |
|---|---|
| **cryptography** | API key encryption at rest |
| **python-telegram-bot** | Telegram bridge for remote control |
| **WSL** (Kali Linux) | Governed security tool execution |

---

## Project Structure

```
BUDDY-MK67-main/
├── main.py                    # Entry point — boots kernel + UI
├── ui.py                      # PyQt6 dashboard (glassmorphic design)
├── app_bootstrap.py           # First-run setup wizard
│
├── agent/                     # 🧠 Core Intelligence (31 modules)
│   ├── kernel.py              #   Top-level orchestrator (KernelOS)
│   ├── runtime.py             #   OPEV execution loop (807 lines)
│   ├── planner.py             #   LLM-driven multi-step planning
│   ├── executor.py            #   Tool registry + dispatch engine
│   ├── verifier.py            #   Hybrid rule + vision verification
│   ├── llm_gateway.py         #   Model routing (OpenRouter → Gemini)
│   ├── policy.py              #   Risk-tier approval gates + scopes
│   ├── safety.py              #   Content scanner (injection, Kali patterns)
│   ├── models.py              #   TaskNode, ActionResult, RiskTier, Scopes
│   ├── budget.py              #   Execution budget tracking
│   ├── rollback.py            #   Action undo/rollback registry
│   ├── journal.py             #   Execution audit trail
│   ├── metrics.py             #   Telemetry event tracking
│   ├── intent_compiler.py     #   Natural language → structured intent
│   ├── dp_brain.py            #   Dynamic programming task optimizer
│   ├── personality.py         #   Voice persona + greetings
│   ├── voice.py               #   Voice orchestration layer
│   ├── telegram_bot.py        #   Telegram remote control
│   ├── workflow_recipes.py    #   Pre-built task templates
│   └── ...                    #   + 12 more modules
│
├── actions/                   # 🔧 70 Tool Modules
│   ├── browser_control.py     #   Playwright autonomous browsing
│   ├── code_helper.py         #   Code gen, execution, debugging
│   ├── file_controller.py     #   File operations (CRUD + search)
│   ├── computer_settings.py   #   System settings management
│   ├── security_auditor.py    #   Security scanning
│   └── ...                    #   + 65 more tools
│
├── tools/                     # 🔐 External Tool Adapters
│   └── kali_adapter.py        #   Kali WSL bridge (25 tools)
│
├── memory/                    # 💾 Memory & Knowledge (12 modules)
│   ├── memory_manager.py      #   SQLite-backed structured memory
│   ├── rag_indexer.py         #   ChromaDB vector indexing
│   ├── embeddings.py          #   Local sentence-transformer
│   ├── schema.py              #   Tier-aware memory schema
│   └── profiles.py            #   User profile management
│
├── voice/                     # 🎙️ Voice System
│   ├── router.py              #   Provider failover routing
│   ├── config.py              #   Voice configuration
│   └── providers/             #   Sarvam, Gemini, pyttsx3 backends
│
├── career/                    # 💼 Career Automation
│   ├── orchestrator.py        #   Job search pipeline
│   ├── linkedin_agent.py      #   LinkedIn integration
│   └── ...                    #   + 7 more modules
│
├── benchmarks/                # 📊 Testing Framework
│   ├── harness.py             #   Automated benchmark runner
│   └── scenarios.py           #   Scored test scenarios
│
├── config/                    # ⚙️ Configuration
├── tests/                     # ✅ 49 test files, 309 tests
├── dashboard-v2/              # 🎨 Next-gen dashboard (React)
└── docs/                      # 📖 Documentation
```

**By the numbers:**
- **136** Python source files across 9 packages
- **70** action modules (desktop tools)
- **25** Kali security tools (governed)
- **31** agent modules (core intelligence)
- **49** test files with **309** passing tests
- **~600KB** of pure Python logic

---

## Installation

### Prerequisites

| Requirement | Version | Notes |
|---|---|---|
| **Python** | 3.12+ | [python.org/downloads](https://www.python.org/downloads/) |
| **Windows** | 10/11 | Native Windows APIs required |
| **Node.js** | 18+ | For Playwright browser automation |
| **Git** | Any | For cloning the repository |
| **Kali Linux** | WSL2 | Optional — for security tools |

### Step 1 — Clone & Setup

```powershell
# Clone the repository
git clone https://github.com/Sirius6907/B.U.D.D.Y-Mark-67.git
cd B.U.D.D.Y-Mark-67

# Create virtual environment
python -m venv venv
.\venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium
```

### Step 2 — Configure API Keys

```powershell
# Copy the example environment file
copy .env.example .env
```

Open `.env` and add your API keys:

| Key | Provider | Required? | Purpose |
|---|---|---|---|
| `BUDDY_GEMINI_API_KEY` | [Google AI Studio](https://aistudio.google.com/) | **Yes** | Vision, planning, fallback LLM |
| `OPENROUTER_API_KEY` | [OpenRouter](https://openrouter.ai/) | **Yes** | Primary LLM routing |
| `SARVAM_API_KEY` | [Sarvam AI](https://sarvam.ai/) | Optional | Voice STT/TTS |
| `TELEGRAM_BOT_TOKEN` | [BotFather](https://t.me/BotFather) | Optional | Remote control via Telegram |
| `TELEGRAM_USER_ID` | Telegram | Optional | Access lock for Telegram bridge |

### Step 3 — Launch

```powershell
python main.py
```

B.U.D.D.Y will boot the kernel, initialize all subsystems, and open the PyQt6 dashboard.

### Step 4 — Optional: Kali Linux Setup

```powershell
# Install Kali Linux in WSL (if not already)
wsl --install -d kali-linux

# Verify B.U.D.D.Y can reach it
wsl -d kali-linux -- echo "Kali connected"

# The target allowlist is auto-created at ~/.buddy/kali_targets.json
# localhost/127.0.0.1 are pre-authorized by default
```

### Troubleshooting

| Issue | Fix |
|---|---|
| `DLL load failed` (PyQt6) | Install [VC++ Redistributable](https://aka.ms/vs/17/release/vc_redist.x64.exe) |
| Playwright not found | Run `playwright install` |
| Microphone not detected | Windows Settings → Privacy → Microphone → Allow desktop apps |
| WSL/Kali not connecting | Run `wsl --update` then `wsl -d kali-linux` |
| ChromaDB import error | `pip install chromadb --force-reinstall` |

---

## Usage

### Text Commands

Type natural language into the dashboard:

```
"Open Chrome and search for Python tutorials"
"Set my volume to 60% and enable dark mode"
"Find all PDF files larger than 10MB on my desktop"
"Write a Python script that scrapes headlines from Hacker News"
"Run a full security scan on localhost"
```

### Voice Commands

Press the push-to-talk key (configurable) or enable continuous listening:

```
"Hey Buddy, what's my CPU usage right now?"
"Buddy, backup my Documents folder to D drive"
"Buddy, schedule a reminder for 3 PM to check emails"
```

### Telegram Remote Control

Send commands from your phone via the Telegram bot:

```
/status          — Check system status
/run <command>   — Execute a task remotely
/screenshot      — Capture current screen
/speak <text>    — Make B.U.D.D.Y say something
```

### Kali Security Operations

```
"Buddy, scan localhost for open ports with nmap"
"Run nuclei against 127.0.0.1:8080 for CVE detection"
"Use gobuster to find hidden directories on my test server"
"Do a full DNS recon on my authorized test domain"
```

### Workflow Recipes

Pre-built multi-step workflows for common tasks:

```
"Run the morning briefing workflow"
"Execute the system health check recipe"
"Start the developer environment setup workflow"
```

---

## Kali Linux Integration

B.U.D.D.Y's Kali integration is not a raw shell — it's a **governed execution layer** with safety controls at every step.

### Architecture

```
┌──────────────────────────────────────────────────┐
│                  OPEV Runtime                    │
│                                                  │
│  ┌─────────────┐    ┌──────────────────────────┐ │
│  │ PolicyEngine │───▶│ ContentSafetyScanner   │ │
│  │ (scope check)│    │ (Kali danger patterns)  │ │
│  └─────────────┘    └──────────┬───────────────┘ │
│                                 ▼                │
│                     ┌──────────────────────────┐ │
│                     │    KaliAdapter           │ │
│                     │ ┌──────────────────────┐ │ │
│                     │ │ TargetScopeValidator │ │ │
│                     │ │ (allowlist check)    │ │ │
│                     │ └──────────┬───────────┘ │ │
│                     └────────────┼─────────────┘ │
└──────────────────────────────────┼───────────────┘
                                   ▼
                        ┌──────────────────┐
                        │   WSL Subprocess │
                        │  (kali-linux)    │
                        │  Output ≤ 1 MB   │
                        └──────────────────┘
```

### Safety Controls

| Control | What It Does |
|---|---|
| **Target Allowlist** | Only scans IPs/domains listed in `~/.buddy/kali_targets.json` |
| **Pre-authorized** | `localhost`, `127.0.0.1`, `::1` always allowed |
| **Permission Scopes** | `CAN_RECON`, `CAN_VULN_SCAN`, `CAN_BRUTEFORCE`, `CAN_EXPLOIT` |
| **Danger Patterns** | Blocks wildcard scans, reverse shells, mass exploitation |
| **Output Cap** | All output truncated at 1 MB to prevent memory overload |
| **Tier Classification** | TIER_1 (passive) → TIER_3 (exploitation) with escalating approval |
| **Parallel Execution** | Fans out independent scans when safe; sequential when uncertain |

---

## Benchmarks

B.U.D.D.Y ships with a built-in benchmark harness that tests across four categories:

### Test Suite Results

```
Total Test Files:     49
Total Tests:          309
Pass Rate:            100% (309/309)
Execution Time:       ~10 seconds
```

### Benchmark Categories

| Category | What It Tests | Scenario Count |
|---|---|---|
| **Safety** | Prompt injection, path traversal, command injection, Kali patterns | 45+ |
| **Accuracy** | Intent compilation, tool selection, plan generation | 20+ |
| **Performance** | Latency, throughput, memory usage under load | 10+ |
| **Adversarial** | Edge cases, malformed input, scope escalation attempts | 15+ |

### Key Metrics

| Metric | Value | Notes |
|---|---|---|
| **Content Safety Scanner** | 5 threat categories, 30+ patterns | Blocks injection, traversal, Kali abuse |
| **Policy Engine** | 4 risk tiers, 12 permission scopes | Scope-aware approval gates |
| **Tool Registry** | 95+ tools (70 desktop + 25 Kali) | Lazy-loaded, registry-dispatched |
| **Memory Tiers** | 3 layers (transient → structured → semantic) | Tier-gated with promotion rules |
| **Telemetry** | Ring buffer, per-tool analytics, query API | Operational metrics for improvement |
| **Rollback** | Action-level undo with state snapshots | Recovery from failed operations |

---

## Security Model

B.U.D.D.Y takes security seriously because it has real power over your system.

### Defense Layers

| Layer | Implementation |
|---|---|
| **API Key Encryption** | Keys stored in encrypted vault (`config/api_keys.json`) via `cryptography` |
| **Policy Engine** | Every action risk-assessed before execution (TIER 0–3) |
| **Content Safety Scanner** | Detects prompt injection, path traversal, command injection, Kali abuse |
| **Permission Scopes** | 12 scopes including 4 Kali-specific dangerous scopes |
| **Target Allowlist** | Kali tools can only scan explicitly authorized targets |
| **Process Shield** | Protects B.U.D.D.Y's own process from unauthorized termination |
| **Sandboxed Execution** | Code runs in isolated subprocesses with timeout limits |
| **Telegram Lock** | Remote control locked to a single `TELEGRAM_USER_ID` |
| **Budget Engine** | Limits total execution time, API calls, and step count per task |

### What B.U.D.D.Y Will NOT Do

- ❌ Scan targets not in your allowlist
- ❌ Run Tier 3 operations without explicit user approval
- ❌ Execute code that matches injection patterns
- ❌ Send your documents to LLM endpoints in full — only relevant snippets
- ❌ Auto-approve destructive actions (registry edits, file deletion, exploitation)

---

## System Requirements

| Component | Minimum | Recommended |
|---|---|---|
| **CPU** | 4-core 2.5 GHz | 8-core 3.5 GHz+ |
| **RAM** | 8 GB | 16 GB+ |
| **GPU** | Integrated | NVIDIA 4 GB+ VRAM |
| **Storage** | 2 GB | 10 GB+ (for RAG indexes + Kali) |
| **OS** | Windows 10 | Windows 11 23H2+ |
| **Network** | Required | For LLM API calls |

---

## Roadmap

### ✅ Delivered (Current)

- [x] OPEV runtime with self-correcting execution loop
- [x] 70+ native desktop automation tools
- [x] Vision-augmented verification (Gemini VLM)
- [x] Dual-provider voice interface (Sarvam + Gemini)
- [x] Three-tier memory with local RAG (ChromaDB)
- [x] Playwright browser automation with self-healing selectors
- [x] Policy engine with 4 risk tiers and 12 permission scopes
- [x] Content safety scanner (5 threat categories, 30+ patterns)
- [x] Kali Linux WSL integration (25 governed security tools)
- [x] Target allowlist enforcement for security operations
- [x] Telegram remote control with user-locked access
- [x] Budget engine with per-task execution limits
- [x] Rollback registry for action undo
- [x] Telemetry tracking with ring buffer and query API
- [x] Benchmark harness (309 tests, 100% pass rate)
- [x] Career orchestrator (job search + application pipeline)

### 🔜 Next Up

- [ ] **Plugin System** — Load custom tool modules at runtime
- [ ] **Multi-Monitor Support** — Vision across all connected displays
- [ ] **Workflow Marketplace** — Share and import task recipes
- [ ] **Local LLM Support** — Run with Ollama/llama.cpp for offline operation
- [ ] **MCP Integration** — Model Context Protocol for agent-to-agent communication
- [ ] **Dashboard v2** — React-based dashboard with real-time telemetry graphs
- [ ] **Mobile App** — iOS/Android companion beyond Telegram
- [ ] **Linux/macOS Port** — Cross-platform runtime adaptation

### 🔮 Future Vision

- [ ] **Multi-Agent Orchestration** — Spawn sub-agents for parallel complex tasks
- [ ] **Continuous Learning** — Improve tool selection from execution history
- [ ] **Natural Language Workflows** — "Record what I do and make it a recipe"
- [ ] **Hardware Integration** — IoT device control, smart home automation
- [ ] **Enterprise Mode** — Multi-user deployment with RBAC and audit logging

---

## Contributing

B.U.D.D.Y is currently under a proprietary license for personal use. If you're interested in contributing, reach out to [Sirius](https://github.com/Sirius6907) directly.

### For Recruiters

This project demonstrates:
- **Systems architecture** — autonomous runtime with self-correcting execution loops
- **AI engineering** — multi-model routing, RAG, vision-language integration
- **Security engineering** — policy engines, permission scopes, content scanning, governed tool execution
- **Testing discipline** — 309 tests across 49 files with 100% pass rate
- **Solo delivery** — entire system designed, built, and tested by one developer

---

## Privacy

B.U.D.D.Y operates **local-first**:
- Documents are indexed on-device and never leave your machine in full
- Only relevant snippets are sent to LLM endpoints for context processing
- Embeddings are generated locally via `all-MiniLM-L6-v2`
- All telemetry is local — no data is sent to external analytics services
- API keys are encrypted at rest

---

## License

Proprietary — Sirius Personal Use License v1.0. See [LICENSE](LICENSE).

Copyright © 2026 Sirius. All rights reserved.

---

<div align="center">

**Built with focus, coffee, and an unreasonable belief that AI should actually do things.**

*B.U.D.D.Y Mark 67 — PROTOCOL SIRIUS*

</div>
]]>
