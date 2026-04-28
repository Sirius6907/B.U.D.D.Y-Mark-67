<div align="center">

# 🤖 B.U.D.D.Y — Mark 67

### Autonomous AI Desktop Operator for Windows

B.U.D.D.Y is an AI agent that can **see your screen, understand context, plan tasks, control apps, automate workflows, use voice, and verify results**.

<p>
  <img src="https://img.shields.io/badge/Python-3.12+-3776AB?style=for-the-badge&logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/Windows-10%2F11-0078D6?style=for-the-badge&logo=windows&logoColor=white" />
  <img src="https://img.shields.io/badge/Tests-309_Passing-2EA043?style=for-the-badge&logo=pytest&logoColor=white" />
  <img src="https://img.shields.io/badge/Tools-95+-FF6F00?style=for-the-badge&logo=gear&logoColor=white" />
</p>

**Built by [Sirius](https://github.com/Sirius6907)**  
*AI should do real work — not just chat.*

</div>

---

# 🚀 Why B.U.D.D.Y?

Most AI tools stop at text generation.

B.U.D.D.Y goes further.

It can:

- 🖥️ Control your desktop
- 👁️ Understand UI state from your screen
- 🧠 Break goals into multi-step plans
- ⚡ Execute actions automatically
- 🔁 Verify outcomes and self-correct
- 🎙️ Accept voice commands and speak back
- 🔐 Enforce permissions, approvals, and safety checks
- 💾 Remember preferences and use local knowledge
- 🌐 Automate the browser
- 💻 Write and run code
- 🛡️ Use governed security tools through Kali Linux

---

# 🎬 Quick Examples

```text
"Open Chrome and summarize today's AI news"

"Find all PDFs larger than 20MB on my PC"

"Create a Python chart from this CSV and save it"

"Set volume to 50% and enable dark mode"

"Scan localhost for open ports"

"Backup my Documents folder to D drive"
```

---

# 🏗 Core Runtime — The OPEV Loop

B.U.D.D.Y uses a self-correcting execution loop called **OPEV**:

**Observe → Plan → Execute → Verify**

```
┌─────────────────────────────────────────────────────────┐
│                    User Command                          │
│               (voice, text, or Telegram)                 │
└──────────────────────────┬──────────────────────────────┘
                           ▼
                  ┌─────────────────┐
                  │    OBSERVE      │  Screen capture + context
                  │  (Vision + RAG) │  gathering via VLM
                  └────────┬────────┘
                           ▼
                  ┌─────────────────┐
                  │      PLAN       │  LLM breaks task into
                  │  (Gemini / OR)  │  ordered TaskNodes
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
                │  NO  → re-plan     │
                └─────────────────────┘
```

### What This Means

- Understands messy prompts via intent compilation
- Selects the right tools from 95+ registered actions
- Blocks unsafe actions through policy + safety scanning
- Tracks execution budget (time, steps, API calls)
- Retries failures intelligently with re-planning
- Confirms results before finishing (rule-based + vision)

### LLM Routing

B.U.D.D.Y doesn't depend on a single model — it routes across providers with automatic failover:

| Layer | Model | Purpose |
|---|---|---|
| **Primary** | OpenRouter (configurable) | Fast reasoning, task planning |
| **Fallback** | Gemini 2.5 Flash / Pro | Deep reasoning, vision analysis |
| **Embeddings** | `all-MiniLM-L6-v2` (local) | RAG document retrieval — runs offline |

---

# ✨ Core Features

## 🖥️ Desktop Automation — 70+ Native Tools

Full native control over Windows — apps, files, windows, mouse, keyboard, clipboard, power settings, audio, networking, and system tools.

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

## 👁️ Vision Intelligence

Reads screen state using screenshots + vision models (Gemini Flash) for UI understanding and verification. Vision verification runs async with an 8-second timeout — it never blocks the pipeline.

## 🌐 Browser Automation

Uses Playwright for browsing, search, scraping, navigation, and workflow automation. Self-healing selectors, session persistence, and context stripping (ads/navigation noise removed before LLM processing).

## 🎙️ Voice Assistant

Dual-provider voice routing with push-to-talk or continuous listening:

| Provider | Role | Strength |
|---|---|---|
| **Sarvam AI** | Primary STT/TTS | Low-latency, Indian English optimized |
| **Gemini** | Fallback | Broad multilingual support |
| **pyttsx3** | Offline fallback | Works without internet |

## 🧠 Memory + RAG

Stores preferences, task context, and searchable local documents. RAG indexes local files (`.pdf`, `.docx`, `.py`, `.md`) incrementally — only re-processes files whose MD5 hash has changed. Embeddings run locally via `all-MiniLM-L6-v2` — **your documents never leave your machine**.

## 💻 Developer Mode

Write code, run scripts, debug failures, generate reports, automate workflows. Code executes in isolated subprocesses with timeout limits. On failure, reads stderr and re-plans automatically.

## 📊 Telemetry + Benchmarks

Tracks execution quality, failures, latency, and test performance with a built-in ring buffer, per-tool analytics, and query API.

---

# 🛡️ Kali Linux Integration — 25 Governed Security Tools

B.U.D.D.Y bridges to a WSL Kali Linux environment for real ethical hacking, bug bounty, and penetration testing — all governed by target allowlisting and permission scopes.

```
┌──────────────────────────────────────────────────┐
│                  OPEV Runtime                     │
│                                                   │
│  ┌─────────────┐    ┌──────────────────────────┐ │
│  │ PolicyEngine │───▶│ ContentSafetyScanner     │ │
│  │ (scope check)│    │ (Kali danger patterns)   │ │
│  └─────────────┘    └──────────┬───────────────┘ │
│                                 ▼                 │
│                     ┌──────────────────────────┐ │
│                     │    KaliAdapter            │ │
│                     │ ┌──────────────────────┐  │ │
│                     │ │ TargetScopeValidator  │  │ │
│                     │ │ (allowlist check)     │  │ │
│                     │ └──────────┬───────────┘  │ │
│                     └────────────┼──────────────┘ │
└──────────────────────────────────┼────────────────┘
                                   ▼
                        ┌──────────────────┐
                        │   WSL Subprocess  │
                        │  (kali-linux)     │
                        │  Output ≤ 1 MB    │
                        └──────────────────┘
```

### Tool Registry by Risk Tier

| Tier | Tools | Risk Level |
|---|---|---|
| **Tier 1** — Passive Recon | nmap, whois, searchsploit, subfinder, amass, whatweb, dnsrecon | Low |
| **Tier 2** — Active Scanning | nikto, gobuster, ffuf, nuclei, wpscan, masscan, dirb, enum4linux | Medium |
| **Tier 3** — Exploitation | hydra, john, hashcat, sqlmap, msfconsole, evil-winrm, crackmapexec | High |

### Safety Controls

| Control | What It Does |
|---|---|
| **Target Allowlist** | Only scans IPs/domains listed in `~/.buddy/kali_targets.json` |
| **Pre-authorized** | `localhost`, `127.0.0.1`, `::1` always allowed |
| **Permission Scopes** | `CAN_RECON`, `CAN_VULN_SCAN`, `CAN_BRUTEFORCE`, `CAN_EXPLOIT` |
| **Danger Patterns** | Blocks wildcard scans, reverse shells, mass exploitation |
| **Output Cap** | All output truncated at 1 MB to prevent memory overload |
| **Tier Classification** | TIER_1 → TIER_3 with escalating approval requirements |
| **Parallel Execution** | Fans out independent scans when safe; sequential when uncertain |

---

# 🔐 Security Model

B.U.D.D.Y has real system access, so security is built into the runtime — not bolted on.

### Risk-Tiered Approval

| Risk Tier | Examples | Approval |
|---|---|---|
| **TIER 0** | Read system info, check weather | Auto-approved |
| **TIER 1** | Open apps, manage files | Logged only |
| **TIER 2** | Change settings, install software | User confirmation |
| **TIER 3** | Exploits, registry edits, data deletion | Explicit approval + explanation |

### Protection Layers

- Permission scopes (12 scopes, 4 Kali-specific dangerous scopes)
- Risk-based approval system (TIER 0–3)
- Content safety scanner (5 threat categories, 30+ patterns)
- Rollback / undo support with state snapshots
- Execution budgets (time, steps, API calls per task)
- Sandboxed subprocesses with timeout limits
- Allowlisted security targets
- Encrypted credentials at rest
- Audit logs and telemetry

### It Will NOT

- ❌ Run dangerous actions silently
- ❌ Scan unauthorized targets
- ❌ Auto-approve destructive tasks
- ❌ Trust prompt injection from files/web pages
- ❌ Expose secrets by default
- ❌ Send your full documents to LLM endpoints — only relevant snippets

---

# 🧠 Memory Architecture

| Layer | Backend | Purpose |
|---|---|---|
| **Transient** | In-memory buffer | Current conversation context |
| **Structured** | SQLite | User preferences, execution logs, profiles |
| **Semantic** | ChromaDB (HNSW) | Local document search via vector embeddings |
| **Ephemeral** | Encrypted temp store | Short-lived secrets, session tokens |

---

# 🛠 Tech Stack

### Core

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
| **sentence-transformers** | Local embedding generation |
| **ChromaDB** | Vector database for semantic search |

### Desktop & System

| Technology | Purpose |
|---|---|
| **pywinauto** | Windows UI automation |
| **pyautogui** | Mouse/keyboard simulation |
| **mss** | High-performance screen capture |
| **opencv-python** | Image processing and vision pipeline |
| **psutil** | System monitoring and process management |
| **Playwright** | Browser automation with Chromium |

### Voice & Security

| Technology | Purpose |
|---|---|
| **Sarvam AI API** | Primary STT/TTS |
| **pyttsx3** | Offline TTS fallback |
| **cryptography** | API key encryption at rest |
| **python-telegram-bot** | Remote control via Telegram |
| **WSL** (Kali Linux) | Governed security tool execution |

---

# 📁 Project Structure

```
B.U.D.D.Y-Mark-67/
├── main.py                    # Entry point — boots kernel + UI
├── ui.py                      # PyQt6 dashboard
├── app_bootstrap.py           # First-run setup wizard
│
├── agent/                     # 🧠 Core Intelligence (31 modules)
│   ├── kernel.py              #   Top-level orchestrator
│   ├── runtime.py             #   OPEV execution loop
│   ├── planner.py             #   LLM-driven multi-step planning
│   ├── executor.py            #   Tool registry + dispatch
│   ├── verifier.py            #   Hybrid rule + vision verification
│   ├── llm_gateway.py         #   Model routing with failover
│   ├── policy.py              #   Risk-tier approval gates
│   ├── safety.py              #   Content scanner
│   ├── models.py              #   Core data models + enums
│   ├── budget.py              #   Execution budget tracking
│   ├── rollback.py            #   Action undo registry
│   ├── journal.py             #   Execution audit trail
│   ├── metrics.py             #   Telemetry tracking
│   └── ...                    #   + 18 more modules
│
├── actions/                   # 🔧 70 Desktop Tool Modules
├── tools/                     # 🔐 External Tool Adapters (Kali)
├── memory/                    # 💾 Memory + RAG (12 modules)
├── voice/                     # 🎙️ Voice System
├── career/                    # 💼 Career Automation
├── benchmarks/                # 📊 Testing Framework
├── tests/                     # ✅ 49 test files, 309 tests
└── docs/                      # 📖 Documentation
```

**By the numbers:** 136 source files · 70 action modules · 25 Kali tools · 31 agent modules · 49 test files · 309 passing tests

---

# ⚡ Quick Start

### 1. Clone Repository

```bash
git clone https://github.com/Sirius6907/B.U.D.D.Y-Mark-67.git
cd B.U.D.D.Y-Mark-67
```

### 2. Create Environment

```bash
python -m venv venv
venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
playwright install chromium
```

### 4. Configure Environment

Create `.env` and add your keys:

| Key | Provider | Required? | Purpose |
|---|---|---|---|
| `BUDDY_GEMINI_API_KEY` | [Google AI Studio](https://aistudio.google.com/) | **Yes** | Vision, planning, fallback LLM |
| `OPENROUTER_API_KEY` | [OpenRouter](https://openrouter.ai/) | **Yes** | Primary LLM routing |
| `SARVAM_API_KEY` | [Sarvam AI](https://sarvam.ai/) | Optional | Voice STT/TTS |
| `TELEGRAM_BOT_TOKEN` | [BotFather](https://t.me/BotFather) | Optional | Remote control via Telegram |
| `TELEGRAM_USER_ID` | Telegram | Optional | Access lock for Telegram bridge |

### 5. Run

```bash
python main.py
```

### 6. Optional: Kali Linux

```bash
wsl --install -d kali-linux
wsl -d kali-linux -- echo "Kali connected"
# Target allowlist auto-created at ~/.buddy/kali_targets.json
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

# 📈 Validation

### Current Stats

- ✅ **309** Passing Tests across **49** test files
- ✅ **95+** Registered Tools (70 desktop + 25 Kali)
- ✅ **12** Permission Scopes with 4-tier approval system
- ✅ **5** Threat Categories with 30+ safety patterns
- ✅ **3** Memory Tiers with local RAG indexing
- ✅ Rollback support with state snapshots
- ✅ Adversarial content safety scanner

---

# 🧪 Example Use Cases

### Productivity
- Open apps, organize files, summarize research
- Create reports, schedule reminders, manage clipboard

### Developer
- Generate scripts, debug code, analyze logs
- Build dashboards, automate dev workflows

### Power User
- System diagnostics, cleanup, backup automation
- Multi-step workflows, browser scraping, batch operations

### Security Lab
- Localhost port scans, DNS recon, directory brute-forcing
- CVE detection with Nuclei, WordPress auditing with WPScan
- Governed pentest automation with full audit trail

---

# 🗺 Roadmap

### ✅ Current

- [x] Autonomous desktop control (70+ tools)
- [x] Voice assistant (dual-provider)
- [x] Browser automation (Playwright)
- [x] Vision verification (Gemini VLM)
- [x] Memory system (3-tier + RAG)
- [x] Security governance (scopes + policy engine)
- [x] Kali Linux integration (25 governed tools)
- [x] Benchmark harness (309 tests)
- [x] Career orchestrator
- [x] Telemetry + metrics

### 🔜 Next

- [ ] Plugin system for custom tools
- [ ] Multi-monitor support
- [ ] Dashboard v2 (React)
- [ ] Local LLM mode (Ollama)
- [ ] Mobile companion app
- [ ] Cross-platform support

### 🔮 Future

- [ ] Multi-agent orchestration
- [ ] Self-improving workflows
- [ ] Natural language recipe recording
- [ ] IoT / smart device control
- [ ] Team / enterprise mode

---

# 👨‍💻 About the Builder

Built solo by **Sirius**.

This project represents work across:

- AI engineering — multi-model routing, RAG, vision-language integration
- Systems architecture — autonomous runtime with self-correcting execution
- Desktop automation — 70+ native Windows tools
- Security engineering — policy engines, permission scopes, governed Kali tooling
- Runtime governance — budget tracking, rollback, adversarial scanning
- Testing discipline — 309 tests across 49 files, 100% pass rate

---

# 🤝 Contributing

Currently under a proprietary personal-use license.

If you'd like to collaborate or discuss the project, reach out through [GitHub](https://github.com/Sirius6907).

---

# 🔒 Privacy

B.U.D.D.Y is designed with a **local-first** mindset:

- Local embeddings — `all-MiniLM-L6-v2` runs on your machine
- Local indexing — documents never leave your device
- Local telemetry — no external analytics
- Encrypted keys — API credentials stored with `cryptography`
- Minimal data sharing — only relevant snippets reach LLM endpoints

---

# 📜 License

Proprietary — Sirius Personal Use License. See [LICENSE](LICENSE).

---

<div align="center">

**B.U.D.D.Y — Mark 67**

*An AI assistant that acts, verifies, and gets real work done.*

</div>
