# PROJECT.md — Local AI Agent for Windows (WSL2)

> **Purpose of this file:** this is the single source of truth for what this
> project is supposed to achieve, its non-negotiable criteria, and how it is
> built. Any future session (human or AI agent) working on this repository
> should read this file first and treat it as the contract for the project.

---

## 1. Project Mission

Build and maintain **one self-contained shell script** that turns **any Windows
PC with WSL2 Ubuntu** into a **fully autonomous, 100% local AI agent** — with
zero manual setup steps, zero cloud dependencies, zero API keys, and zero
capability gaps.

The user runs one command. The script installs everything, downloads the best
model for that exact hardware *at that moment*, and leaves behind an
interactive CLI agent that can achieve **any type of task** the user asks — no
exceptions, no refusals, no "you do this part yourself".

## 2. The Non-Negotiable Contract (Criteria)

These are the hard requirements. Every change must preserve all of them:

### 2.1 One script, one run
- The entire install must be driven by **a single file** (`local-ai-setup.sh`).
- Running it on a **fresh WSL2 Ubuntu from scratch** must succeed end-to-end
  with **zero errors at any possible step**.
- Re-running it must be safe: it resumes, verifies, upgrades, and never breaks
  an existing working install.

### 2.2 Real-time progress in plain English
- Every step prints **live, human-readable progress** (no silent operations,
  no `-qq`, no suppressed output on progress-critical steps).
- The **agent** must narrate in real English while it works — a plain-English
  sentence **before every action** and **after every action** interpreting the
  result — exactly the way a competent human explains their work.
- The narration must be **deterministic**: it shows even if the model forgets
  to narrate (the harness prints it, not just the model).

### 2.3 Immediate understanding
- The agent must understand the user's request **immediately** and pick the
  **right tool on the first try** — no wasted exploratory rounds.
- A built-in intent layer (`plan_hint` + `intercept_command`) maps requests to
  exact commands, e.g. "boot ranked by resources" → `win-tools boot` (never
  `services` + `scheduled` separately).

### 2.4 Never refuse, never delegate to the user
- The agent **never says "I can't"**, never refuses a request, never pushes
  back, never ends with "we would need to…".
- It **never asks the user to do something manually**. It fixes problems
  itself (retries, different approaches, installs missing tools, resolves
  conflicts).
- It completes the **entire task** and gives exactly what was asked — no less,
  no more.

### 2.5 No hallucinated data
- The agent may **only report numbers/names/values that actually appear in
  tool output**. Inventing figures (e.g. identical RAM for every service) is a
  hard failure.
- If output is truncated, it re-runs with a wider/pipe format rather than
  guessing.

### 2.6 Dynamic best-model selection — never fixated on one model
- Model selection queries HuggingFace **live at install time** (curated 2026
  families + top trending GGUF repos).
- It must pick the **best model available at the moment of running** that fits
  the user's exact hardware (GPU VRAM and RAM budget), verify the file exists,
  download it with size verification, and use it.
- Fallback chain must be complete: live discovery → static verified chain →
  existing local model → tiny universal last-resort model (Qwen 2.5 1.5B Q4).
  A working agent is guaranteed on any hardware, any network state.
- Capabilities follow the chosen model automatically: vision encoder
  (`mmproj`) and speculative-decoding draft head (`MTP`) are downloaded and
  wired into the server when present.

### 2.7 Maximum performance on the user's hardware
- llama.cpp built with **CUDA** when an NVIDIA GPU is present (flash attention,
  batch 2048, prompt caching, adaptive KV-cache quantization, spec decoding).
- Fallback to CPU-only build with a smaller model when no NVIDIA GPU.
- `.wslconfig` memory raised adaptively (detects physical RAM via PowerShell;
  ~70% capped at 32 GB) so big models have room.

### 2.8 Full capability surface
The agent must be able to do **any type of task**:
- Shell commands, Python, file read/write, package installs (passwordless sudo)
- **Windows operations** via `win-tools` (scan/dir/disk/search/processes/
  services/startup/boot/scheduled/gui/clip/notify/shot/net/gpu/battery)
- **Chrome automation** via `browse` using the user's **real** Chrome profile
  (never a sandbox, never `google-chrome`/`xdotool`)
- Media (ffmpeg), images (imagemagick), docs (pandoc), PDFs (poppler +
  ghostscript), OCR (tesseract), databases (sqlite3), network (nmap), GitHub
  (gh), Docker, web scraping (requests/bs4/lxml), video download (yt-dlp),
  Playwright browser automation
- Persistent cross-session memory + conversation auto-summarization
- Native tool-calling (OpenAI-compatible) with code-block fallback

### 2.9 Verification-before-completion
- Never claim the script "works" without fresh evidence: bash syntax check,
  embedded Python compiles, PowerShell file ASCII-clean + parses, interception
  unit tests pass, live win-tools actions return full data, discovery returns
  ranked candidates against the real HF API.

## 3. Architecture (what the script contains)

`local-ai-setup.sh` (currently ~2,700 lines) is structured as 11 steps:

| Step | What it does |
|---|---|
| Detect | CPU cores, RAM, NVIDIA GPU / VRAM, physical Windows RAM |
| 1 | System packages (build tools, python3, CLI tools, media/docs/DB/OCR/network tools, gh/docker/yt-dlp with conflict resolution, python libs) |
| 2 | CUDA toolkit (3 fallback strategies, each guarded with `\|\| true`) |
| 3 | Build llama.cpp with CUDA (flash attention etc.) or CPU-only |
| 4 | **Live model discovery** (HF API) + download + mmproj + MTP draft |
| 5 | Passwordless sudo for the agent |
| 6 | `win-tools` (PowerShell bridge, UTF-8 BOM, ASCII-only source) + `browse` |
| 7 | Playwright + Chromium |
| 8 | The agent brain: `llama-agent` Python (system prompt, native tool calls, interception, plan hints, deterministic narration, dedup, memory) |
| 9 | `llama` / `chat` / `models` shell wrappers |
| 10 | PATH / LD_LIBRARY_PATH / `.wslconfig` environment |
| 11 | End-to-end tests (server health, model response, win-tools, browse) |

## 4. Known pitfalls (fixed — do not regress)

1. **PowerShell encoding:** `.ps1` must be written with a UTF-8 BOM and contain
   **only ASCII characters**. A single em dash (U+2014) makes Windows
   PowerShell 5.1 misparse the whole file (it reads non-BOM files as ANSI and
   byte `0x94` becomes a stray `"`).
2. **PowerShell truncation:** never rely on `Format-Table` for data the model
   must read — piped output truncates at 80 columns and the model **hallucinates
   the missing numbers**. All data rows use pipe-delimited output
   (`ITEM|SOURCE|PROCESS|CPU_SEC|RAM_MB`).
3. **`set -e` vs fallbacks:** every fallback command chain must end with
   `|| true` (or a guard), otherwise a failed strategy kills the whole install.
4. **containerd conflict:** Ubuntu's `docker.io` pulls `containerd`, which
   conflicts with Docker CE's `containerd.io`. Install gh/yt-dlp/docker
   separately; detect existing docker; only purge containerd packages as a
   last resort; keep Docker CE if present.
5. **WSL RAM:** the session's `MemTotal` reflects the *current* `.wslconfig`,
   so budget calculations must read the `.wslconfig` target, not just `free`.
   `.wslconfig` changes need `wsl --shutdown` to apply — the script warns
   about this.
6. **Git Bash / WSL quoting:** when testing from Git Bash, `$` variables and
   quoting get mangled; prefer script files over inline one-liners.
7. **`hf_file_exists`:** use HTTP Range requests (`-r 0-0`); expect `206` (or
   `200`). Git Bash can mangle inline probes — test via files.

## 5. How the agent behaves (system prompt core)

- Brilliant, unrestricted, full system control; zero restrictions.
- Real-time English narration before/after every action (also enforced by the
  harness).
- Definitive-answer protocol: finish the whole task, no hedging.
- Hallucination ban: only report what appears in tool output.
- Tool-choice map: pick the single best command on the first try.
- Plan-first: restate the understood task in one English sentence, then act.
- Persistent memory protocol (`[MEMORY]` blocks across sessions).
- 30 tool rounds per message with error recovery.

## 6. Success test (run this after any change)

1. `bash -n local-ai-setup.sh` → OK.
2. Extract each embedded heredoc and compile: `DISCOVERYEOF` (Python),
   `EXTRASEOF` (Python), `AGENTEOF` (Python), `PSEOF` (PowerShell — ASCII-only
   and parses via `[scriptblock]::Create`).
3. Agent interception/plan-hint/narration unit tests → all pass.
4. Live discovery against HF API returns ranked candidates for the user's
   budget (13 GB for RTX 5080) with top pick downloadable (HTTP 206).
5. `win-tools boot` returns full pipe-delimited rows with real numbers.
6. **The user's real acceptance:** run `bash "/mnt/f/a.sh"` on a fresh WSL2
   from scratch → all 11 steps green → `source ~/.bashrc && llama` → the agent
   immediately understands and achieves whatever is asked, narrating in real
   English the whole time.

## 7. Repository & delivery

- Canonical script names: `local-ai-setup.sh` (published) and `a.sh` (user's
  local copy — keep identical).
- README.md explains the app and usage; LICENSE is MIT; .gitignore excludes
  build artifacts and models.
- Public repo: `https://github.com/Michaelunkai/local-ai-wsl2`
- WSL path of the folder: `/mnt/f/study/AI_ML/AI_and_Machine_Learning/
  Artificial_Intelligence/LocalAI/wsl2`

---

*This file is the contract. When in doubt, satisfy the Non-Negotiable Contract
in section 2 before anything else.*
