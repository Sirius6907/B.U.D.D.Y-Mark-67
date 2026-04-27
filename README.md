# 🤖 B.U.D.D.Y Mark 67

**Autonomous Desktop AI Assistant for Windows**

[![Python 3.12+](https://img.shields.io/badge/Python-3.12%2B-blue.svg)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/Platform-Windows%2010%2F11-0078D6.svg)]()
[![License](https://img.shields.io/badge/License-Proprietary-red.svg)](LICENSE)

B.U.D.D.Y (**B**iometric **U**tility & **D**igital **D**esktop **Y**ield) Mark 67 is a vision-aware autonomous agent that operates natively on Windows. It sees your screen, understands context, plans multi-step tasks, and executes them — with real-time voice interaction and self-correcting verification.

---

## Core Architecture

### OPEV Loop — Observe · Plan · Execute · Verify

Every task runs through a self-correcting execution loop:

```
User Command
    → OBSERVE: Capture screen + context
    → PLAN: Break into steps via LLM (Gemini 2.5 / OpenRouter)
    → EXECUTE: Dispatch tools (70+ actions)
    → VERIFY: Rule-based + Vision-confirmed (VLM screenshot analysis)
    → Loop or Complete
```

The Verify stage uses a **hybrid engine**: rule-based checks for fast confirmation, and optional VLM screenshot analysis (Gemini Flash) for critical UI actions like app launches and browser navigation. Vision verification runs async with an 8-second timeout — it never blocks the pipeline.

### LLM Routing

| Layer | Model | Purpose |
|---|---|---|
| Primary | OpenRouter (configurable) | Fast reasoning, planning |
| Fallback | Gemini 2.5 Flash / Pro | Deep reasoning, vision analysis |
| Embeddings | `all-MiniLM-L6-v2` (local) | RAG document retrieval |

Routing is handled by `agent/llm_gateway.py` with automatic failover.

---

## Features

### 🖥️ Desktop Automation (70+ Tools)
Full native control over Windows — apps, files, windows, mouse, keyboard, clipboard, volume, wallpaper, power management, and system settings. All tools are registry-dispatched with lazy loading.

### 👁️ Vision Intelligence
Screen capture via `mss` → VLM analysis via Gemini → semantic understanding of UI state. Used for both autonomous navigation and verification of completed actions.

### 🎙️ Voice Interface
Dual-provider voice routing:
- **Sarvam AI** (primary) — low-latency Indian-English STT/TTS
- **Gemini** (fallback) — broad language support

Push-to-talk and continuous listening modes. Audio playback synced with UI animations.

### 🧠 Memory & RAG
Three-tier memory architecture:

| Layer | Backend | Use |
|---|---|---|
| Transient | In-memory buffer | Current conversation |
| Structured | SQLite | User preferences, logs |
| Semantic | ChromaDB (HNSW) | Local document search |

RAG indexes local files (`.pdf`, `.docx`, `.py`, `.md`) incrementally — only re-processes files whose MD5 hash has changed.

### 🌐 Browser Automation
Playwright-based autonomous browsing with self-healing selectors, session persistence, and context stripping (ads/navigation noise removed before LLM processing).

### 💻 Developer Engine
Code writing, execution, and debugging in isolated subprocesses. Reads stderr on failure and re-plans automatically.

### 📱 Telegram Bridge
Remote OS control via encrypted Telegram bot. Locked to a single `TELEGRAM_USER_ID`.

### 🛡️ Security
- API keys stored in encrypted vault (`config/api_keys.json`)
- Policy engine with risk-tiered approval gates
- Process shielding against unauthorized termination
- Sandboxed code execution

---

## Project Structure

```
BUDDY-MK67-main/
├── main.py                 # Entry point — boots kernel + UI
├── ui.py                   # PyQt6 dashboard with glassmorphic design
├── buddy_logging.py        # Centralized logging
├── agent/
│   ├── kernel.py           # KernelOS — top-level orchestrator
│   ├── planner.py          # LLM-driven multi-step task planning
│   ├── executor.py         # Tool registry + dispatch engine
│   ├── runtime.py          # OPEV loop (sync + async)
│   ├── verifier.py         # Hybrid rule + vision verification
│   ├── llm_gateway.py      # Model routing (OpenRouter → Gemini)
│   ├── openrouter_client.py# OpenRouter API client
│   ├── policy.py           # Risk-tier approval gates
│   ├── models.py           # TaskNode, ActionResult, RiskTier
│   ├── personality.py      # Voice personality + boot greetings
│   ├── voice.py            # Voice orchestration layer
│   ├── telegram_bot.py     # Telegram remote control
│   ├── journal.py          # Execution audit trail
│   ├── workflow_memory.py  # Persistent workflow state
│   ├── workflow_recipes.py # Pre-built task templates
│   ├── error_handler.py    # LLM-assisted error recovery
│   └── task_queue.py       # Background task scheduling
├── actions/                # 70+ tool modules (see below)
├── memory/
│   ├── memory_manager.py   # SQLite-backed structured memory
│   ├── rag_indexer.py      # ChromaDB vector indexing
│   ├── embeddings.py       # Local sentence-transformer embeddings
│   └── schema.py           # Database schema definitions
├── voice/
│   ├── router.py           # Provider failover routing
│   ├── config.py           # Voice provider configuration
│   └── providers/          # Sarvam, Gemini, pyttsx3 backends
├── config/
│   ├── runtime.py          # Runtime configuration constants
│   └── api_keys.json       # Encrypted API key storage
├── core/                   # Shared utilities
├── scripts/                # Maintenance & deployment scripts
├── tests/                  # Test suite
├── pyproject.toml          # Project metadata & dependencies
└── requirements.txt        # Pip-compatible dependency list
```

### Tool Categories (`actions/`)

| Category | Tools |
|---|---|
| **Desktop** | `open_app`, `desktop`, `window_manager`, `wallpaper_changer` |
| **Input** | `mouse_controller`, `keyboard_controller`, `clipboard_manager` |
| **Files** | `file_controller`, `file_searcher`, `zip_manager`, `pdf_manager` |
| **System** | `system_info`, `system_actions`, `system_diagnostics`, `power_manager` |
| **Settings** | `computer_settings`, `volume_controller`, `wifi_manager`, `bluetooth_manager` |
| **Security** | `firewall_manager`, `antivirus_manager`, `privacy_manager`, `process_shield`, `vault_manager` |
| **Browser** | `browser_control`, `web_search`, `youtube_video` |
| **Dev** | `code_helper`, `dev_agent`, `ide_tracker` |
| **Vision** | `screen_processor`, `screen_recorder`, `camera_capture`, `image_editor` |
| **Comms** | `send_message`, `email_client`, `notification_sender`, `reminder` |
| **System Mgmt** | `process_manager`, `service_controller`, `startup_manager`, `registry_manager` |
| **Maintenance** | `backup_manager`, `disk_analyzer`, `system_optimizer`, `recovery_manager` |
| **Media** | `media_player`, `audio_recorder`, `text_to_speech` |
| **Misc** | `weather_report`, `password_generator`, `notes_manager`, `timer_manager`, `flight_finder` |

---

## Setup

### Prerequisites
- **Python 3.12+**
- **Windows 10/11**
- **Node.js** (for Playwright)

### Installation

```powershell
# Clone
git clone https://github.com/Sirius6907/B.U.D.D.Y-Mark-67.git
cd B.U.D.D.Y-Mark-67

# Virtual environment
python -m venv venv
.\venv\Scripts\activate

# Dependencies
pip install -r requirements.txt

# Playwright browsers
playwright install chromium

# Configure keys
copy .env.example .env
# Edit .env with your API keys
```

### Required API Keys

| Key | Provider | Purpose |
|---|---|---|
| `BUDDY_GEMINI_API_KEY` | [Google AI Studio](https://aistudio.google.com/) | Vision, planning, fallback LLM |
| `OPENROUTER_API_KEY` | [OpenRouter](https://openrouter.ai/) | Primary LLM routing |
| `SARVAM_API_KEY` | [Sarvam AI](https://sarvam.ai/) | Voice STT/TTS |
| `TELEGRAM_BOT_TOKEN` | [BotFather](https://t.me/BotFather) | Remote control (optional) |
| `TELEGRAM_USER_ID` | Telegram | Access lock (optional) |

### Run

```powershell
python main.py
```

### Troubleshooting

| Issue | Fix |
|---|---|
| `DLL load failed` (PyQt6) | Install [VC++ Redistributable](https://aka.ms/vs/17/release/vc_redist.x64.exe) |
| Playwright not found | Run `playwright install` |
| Microphone not detected | Windows Settings → Privacy → Microphone → Allow desktop apps |

---

## System Requirements

| Component | Minimum | Recommended |
|---|---|---|
| CPU | 4-core 2.5GHz | 8-core 3.5GHz+ |
| RAM | 8 GB | 16 GB+ |
| GPU | Integrated | NVIDIA 4GB+ VRAM |
| Storage | 2 GB | 10 GB+ (for RAG) |
| OS | Windows 10 | Windows 11 23H2+ |

---

## Dependencies

| Library | Purpose |
|---|---|
| `google-genai` | LLM planning + vision |
| `chromadb` | Vector database for RAG |
| `sentence-transformers` | Local embeddings |
| `playwright` | Browser automation |
| `pywinauto` / `pyautogui` | Desktop control |
| `PyQt6` | Dashboard UI |
| `sounddevice` / `pyaudio` | Audio capture |
| `opencv-python` | Vision processing |
| `mss` | Screen capture |
| `python-telegram-bot` | Telegram bridge |
| `cryptography` | Key encryption |

---

## License

Proprietary — Sirius Personal Use License. See [LICENSE](LICENSE).

---

## Privacy

BUDDY operates **local-first**. Documents are indexed on-device and never leave your machine in full. Only relevant snippets are sent to LLM endpoints for context processing. All telemetry is opt-in.
