# Local AI Agent for Windows (WSL2) — One-Script Installer

A single, self-contained shell script that turns **any Windows PC with WSL2** into a fully autonomous, **100% local** AI agent — no cloud, no API keys, no subscriptions. It installs everything from scratch, downloads the **best open-weight model that fits your exact hardware at the moment you run it**, and gives you an interactive CLI agent that can execute commands, manage files, automate Windows, and do almost anything you can type.

> **Model selection is dynamic.** Every time you run the installer it queries HuggingFace *right now*, ranks the current best agentic models (trending + curated 2026 families), checks their real file sizes against your GPU VRAM and RAM, and downloads the single best model that fits. What you get today may be even better tomorrow — the script always picks what's best *at that moment*.

---

## ✨ What it does

- **One script, zero manual steps.** Detect hardware → install packages → install CUDA → build llama.cpp with GPU support → download the best model → configure passwordless sudo → install Windows automation tools → install the agent brain → run end-to-end tests.
- **Fully local & private.** Everything runs on your machine. No data leaves your PC.
- **A real agent, not a chatbot.** The agent narrates in plain English what it's doing, then **executes commands itself** — shell, Python, files, package installs, Chrome automation, and Windows operations — up to 30 tool rounds per request, with error recovery.
- **Windows superpowers from WSL2.** Scans drives, lists startup programs ranked by CPU/RAM, searches files, reads the clipboard, sends notifications, screenshots + OCR, automates GUI keystrokes, manages Chrome with your real profile.
- **Vision & speed.** If the chosen model supports it, the script auto-downloads its vision encoder (image understanding) and its speculative-decoding draft head (~1.5× faster generation). Flash attention + batch 2048 + prompt caching are enabled automatically.
- **Persistent memory.** The agent remembers facts and decisions across sessions.
- **Re-runnable.** Run it again any time — it resumes, re-verifies, and upgrades to whatever the best model is *that day*.

---

## 📋 Requirements

| Requirement | Detail |
|---|---|
| **Windows 10/11** (64-bit) | Any version with WSL2 support |
| **WSL2 with Ubuntu** | If you don't have it, the guide below installs it |
| **Disk space** | ~15–30 GB free (packages + CUDA + model) |
| **RAM** | 8 GB minimum; 16 GB+ recommended |
| **GPU (optional but recommended)** | NVIDIA GPU with updated drivers → CUDA acceleration, far faster |
| **Internet** | Needed once during install (downloads packages + model) |

Works with or without an NVIDIA GPU. Without one it builds a CPU-only engine and picks a smaller model that still gives a fully working agent.

---

## 🚀 Quick start (any Windows device)

### 1. Install WSL2 + Ubuntu (if you don't have them yet)

Open **PowerShell as Administrator** and run:

```powershell
wsl --install -d Ubuntu
```

Reboot when prompted. After the reboot, Ubuntu finishes installing and asks you to create a Linux username/password. Then verify:

```powershell
wsl -d Ubuntu -- bash -c "echo WSL2 ready"
```

### 2. Run the installer

Inside your WSL2 Ubuntu terminal:

```bash
cd /mnt/c/Users/<YourWindowsUsername>/Downloads
wget -qO local-ai-setup.sh https://raw.githubusercontent.com/Michaelunkai/local-ai-wsl2/main/local-ai-setup.sh
chmod +x local-ai-setup.sh
./local-ai-setup.sh
```

> 💡 The script prints real-time progress for every step. A large model download (~10–13 GB) can take a while — grab a coffee. The CUDA toolkit (~4 GB) is also a large download on first install.

### 3. Start your AI agent

After the install finishes, run:

```bash
source ~/.bashrc && llama
```

You'll see the agent banner, then just **type what you want** in plain English:

```
> list everything that runs at Windows boot, ranked by CPU and RAM
> scan my C drive and show the 10 heaviest folders
> open YouTube in my Chrome browser
> create a python script that renames all files in Downloads by date
```

The agent explains what it's doing in English, runs the commands itself, and gives you a structured answer.

---

## 🛠️ Commands & tools

### Agent commands

| Command | What it does |
|---|---|
| `llama` | Start the interactive agent (REPL) |
| `chat` | Same as `llama` |
| `llama "task"` | Single-shot mode: do one task and exit |
| `llama-agent --server` | Run as an HTTP API server (OpenAI-compatible) |
| `models` | List downloaded models |
| `win-tools <action>` | Run a Windows operation directly |

### Inside the agent (slash commands)

| Command | What it does |
|---|---|
| `/quit` | Exit |
| `/clear` | Clear the conversation |
| `/reset` | Restart server + fresh conversation |
| `/history` | Show conversation history |
| `/memory` | Show persistent memory |

### win-tools (Windows bridge)

| Command | What it does |
|---|---|
| `win-tools scan C` | Heaviest folders on a drive |
| `win-tools dir F:` | List top-level folders & files on a drive |
| `win-tools disk C` | Disk space used/free/total |
| `win-tools search C name` | Search files by name |
| `win-tools processes` | Top memory-consuming processes |
| `win-tools services` | Running services |
| `win-tools startup` | Programs that run at boot + top CPU users |
| `win-tools boot` | **Everything** at boot (registry + startup folder + scheduled tasks + auto services), ranked by CPU/RAM |
| `win-tools scheduled` | Enabled scheduled tasks |
| `win-tools gui <title> <keys>` | Activate a Windows window and send keystrokes |
| `win-tools clip [set <text>]` | Read or set the Windows clipboard |
| `win-tools notify [title] [msg]` | Show a Windows notification |
| `win-tools shot` | Screenshot + OCR of the Windows screen |
| `win-tools net` | Network adapters / IPs / Wi-Fi |
| `win-tools gpu` | GPU info |
| `win-tools battery` | Battery status |

### Chrome automation

```bash
browse open https://www.youtube.com   # opens in your EXISTING Chrome profile
browse newwindow https://example.com  # new Chrome window
browse newtab                         # new blank tab
```

---

## 🔧 What gets installed (full capability map)

| Category | Tools |
|---|---|
| **Build** | build-essential, cmake, git, CUDA toolkit, llama.cpp (GPU build) |
| **Model** | Best-fitting open GGUF model auto-selected at run time (+ vision encoder & spec-decoding draft when available) |
| **Files & shell** | ripgrep, fd, bat, fzf, tree, rsync, htop, tmux, screen, xclip |
| **Media** | ffmpeg (audio/video), imagemagick (images) |
| **Documents** | pandoc (conversion), poppler-utils + ghostscript (PDFs), tesseract (OCR) |
| **Data** | sqlite3, python3 + requests/bs4/lxml (web scraping) |
| **Network** | nmap, netcat, dnsutils, curl, wget |
| **Dev** | nodejs, npm, GitHub CLI (gh), Docker, docker-compose |
| **Media download** | yt-dlp |
| **Browser automation** | Playwright + Chromium |
| **Windows bridge** | win-tools (PowerShell), browse (Chrome with your real profile) |

---

## 🧠 How the agent works

1. You type a request in English.
2. The agent **restates what it understood** and picks the single best tool for the job (a built-in intent engine also nudges it toward the right command — e.g. "boot ranked by resources" always maps to `win-tools boot`).
3. It **narrates in real time**, runs the tool, and **interprets the result in English** after every step.
4. It loops until the task is done (up to 30 rounds), then gives you a complete structured answer.
5. **It never asks you to do things manually.** If a tool fails, it tries a different approach. It never invents numbers — every figure in an answer comes from real tool output.

**Safety note:** the agent has full control of your machine by design (including passwordless sudo). It is an assistant, not a sandbox — use it on machines you trust.

---

## ❓ Troubleshooting

| Problem | Fix |
|---|---|
| `WSL has no installed distributions` | Run `wsl --install -d Ubuntu` (Admin PowerShell), reboot |
| Install was interrupted | Just re-run the script — it resumes and finishes the remaining steps |
| Model download fails | The script automatically tries the next-best model; also check your internet connection |
| Agent says "Server failed to start" | Check the log: `cat ~/.local/share/llama-agent/server.log`, then run `/reset` |
| WSL memory seems low | The installer raises `.wslconfig` memory automatically; run `wsl --shutdown` once and reopen the terminal to apply |
| CUDA not detected | Install the latest NVIDIA driver from nvidia.com and restart; the installer falls back gracefully to CPU-only |
| Docker install conflict | The installer resolves `containerd`/`containerd.io` conflicts automatically (non-fatal either way) |

---

## 📄 License

MIT — free to use, modify, and share.

---

*Local AI Agent for Windows — run a genuinely capable, private AI on your own hardware.*
