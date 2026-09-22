# Local AI stack

Project: `F:\backup\UnrestrictedAi` · Open WebUI: **http://localhost:3080**

Windows and browser integration work is tracked in `CAPABILITIES.md`. The same launcher now starts an authenticated Windows-side MCP bridge. Both model presets receive the workspace tool connection with direct Windows directory listing, on-demand desktop/UI/browser tool discovery and multi-source online research. Existing-tab control requires the official Playwright extension connection; schema discovery alone does not verify browser control.

For Windows files use `list_windows_directory` or the `desktop` integration, rather than sandbox Python. Other integration names are `windows_ui`, `browser` and `research_browser`. Tool discovery returns a compact catalog; provide `tool_name` to obtain one tool's full argument schema. The separate research browser does not inherit your logged-in browser sessions. Windows tools run with the current user's permissions, while sandbox Python remains isolated.

Both requested published models are installed with their original weights and templates. Qwen includes its vision projector. Model file SHA-256 values and upstream commits are recorded in `models.lock.json`; Ollama blobs use hardlinks to the verified downloads instead of duplicating the large files.

## Use

Run `F:\backup\UnrestrictedAi\Setup-and-Open.ps1` to prepare the stack, provision missing models, configure the presets, check readiness and open your default browser. This launcher supports Windows PowerShell 5.1. Add `-FullVerification` to run the complete inference/tool integration suite before opening; normal startup does not repeat that lengthy suite.

Open http://localhost:3080 and choose Qwen or Dolphin. Qwen 32K is the chat default; both models also have optional 8K fast presets. The launcher verifies that all four presets reference the pinned published model blobs and warms up Qwen before opening the browser. Switching to another model displays loading progress; a cold load from the external drive can take a few minutes. Wait for the response rather than resubmitting during loading.

Workspace tools are enabled on both models. Qwen uses the built-in code interpreter; Dolphin uses the workspace `execute_python` tool through the same isolated Python sandbox, avoiding its repeated legacy interpreter instructions. Use the Integrations menu to select the optional MCP connection or enable web search. Code and tool-created files persist in `workspace/`.

Long chats automatically summarize older turns at an estimated 18,000 tokens for 32K presets (4,000 for 8K presets), retaining recent messages in the active context and the full original conversation in storage. Summaries preserve important facts but are lossy: restate critical details if needed. Both models passed twelve consecutive saved-chat turns including recall, file reading and Python execution. The regression deliberately lowers the threshold to 600 tokens after four turns to exercise repeated compaction; it is not a full-32K accuracy benchmark. See `logs/chat-repair-verification.json` and `data/indexer/long-chat-*.json`.

The WebUI image includes a local context-compaction repair for tool-heavy branches: when a single earlier assistant turn fills the context before a third user turn, it compacts that branch before generating the next tool call. The summarizer input is bounded and has a local fallback, while the complete conversation stays in the saved chat. `scripts/verify-tool-call-budget.py` exercises this exact 32K `execute_python` continuation.

```powershell
& F:\backup\UnrestrictedAi\run_ai_stack.ps1 start
& F:\backup\UnrestrictedAi\run_ai_stack.ps1 status
& F:\backup\UnrestrictedAi\run_ai_stack.ps1 verify
& F:\backup\UnrestrictedAi\run_ai_stack.ps1 update
```

The verifier runs real inference, vision, model switching, live search/crawl, vector retrieval, MCP/OpenAPI tool calls, generated Python execution, and sandbox boundary tests. Its latest authoritative result is `data/indexer/verification.json`. The rolling operational status is `logs/supervisor-status.json`; `healthy` describes services and `fullyReady` also requires models and a working index.

Normal startup also checks public DNS and HTTPS against two independent sites in parallel, with an eight-second process limit per probe. The current result is saved to `data/indexer/startup-internet.json`. An outage prints a warning while allowing local chats to open. This checks outbound connectivity; it does not assert that every search provider or authenticated browser connection is available.

## Models and measured settings

| Ollama name | Purpose | Context |
| --- | --- | --- |
| `local-qwen:27b` | Qwen 3.8 27B, IQ4_XS, vision and native tools | 8,192 |
| `local-dolphin:24b` | Dolphin 3.0 Mistral 24B, Q4_K_M, text and coding | 8,192 |
| `local-qwen:27b-32k` | Qwen extended context | 32,768 |
| `local-dolphin:24b-32k` | Dolphin extended context | 32,768 |
| `nomic-embed-text:latest` | Local 768-dimensional embeddings | 2,048 |

The RTX 5080 has 16,303 MiB VRAM. The host has 16 logical processors and about 94 GiB RAM. Four context sizes were measured. At 8K, the coding benchmark measured approximately **24.4 tokens/sec for Qwen** and **33.0 tokens/sec for Dolphin**. The selection rule chooses the largest tested context within 10% of the fastest measured decoding rate. Raw results are in `logs/benchmark.json`; selected settings are in `tuning.json`.

Settings: eight CPU threads, automatic VRAM-based GPU offload, Flash Attention enabled, Q8 KV cache, one chat sequence, one resident large model, and indefinite keep-alive. Both 32K settings also generated successfully. Generation speed and model-loading time vary with prompt size, disk cache, and other applications. Two models this size do not fit together in 16 GB VRAM: switching loads the other model and is not instantaneous. Qwen thinking is initially off for responsive interaction and can be enabled in model controls.

A separate CPU-only Ollama process on port 11436 keeps embeddings available without evicting the chat model. Both processes reuse `F:\backup\ollama\ollama.exe`; Ollama was not reinstalled.

## Endpoints

| Service | Local address |
| --- | --- |
| Open WebUI | http://localhost:3080 |
| Ollama chat API | http://localhost:11434 |
| CPU embedding API | http://localhost:11436 |
| SearXNG | http://localhost:8081 |
| Crawl4AI | http://localhost:11235 (token in `docker/.env`) |
| Qdrant dashboard | http://localhost:6333/dashboard |
| Workspace OpenAPI | http://localhost:8001/docs |
| Workspace MCP | http://localhost:8001/mcp/ |

Port 3000 belongs to the existing Coder application. It is independent of this stack.

## Storage and execution

The dedicated `UnrestrictedAi` WSL2 distribution, Linux temporary files, Docker images, container writable layers, and Linux packages reside physically in `runtime/wsl/ext4.vhdx` on F:. SearXNG's named cache volume also lives inside this disk, avoiding an observed Windows bind-mount cache-directory problem. All other persistent service mounts point into this project. Windows WSL/task registrations and OS runtime metadata remain managed by Windows.

WSL swap is redirected to `runtime/wsl-swap.vhdx`; the Windows `.wslconfig` is a symlink. The original Windows `.ollama` directory is now a junction into `cache/original-user-ollama`. Managed Ollama homes, Hugging Face caches, pip caches, process logs, and downloaded model sources are project-local. See `logs/storage-inventory.json` for inspected mounts.

The indexer polls every 60 seconds and indexes source code, text, Markdown, PDF and DOCX documents, with a 2 MB per-file limit. It excludes hidden files, credentials, runtime disks, models, logs, caches, dependency trees and `data/`. Changes and deletions replace/remove stale vector chunks. Query tools read the indexed document set; write tools are confined to `workspace/`.

The Jupyter sandbox has a read-only root, no infrastructure/model mount, an internal network without internet egress, and limits of two CPUs, 2 GiB RAM and 128 processes. Its writable persistent directory is `workspace/`.

## Recovery and maintenance

The `UnrestrictedAi-Health` task starts at user logon and checks the stack every minute. It restarts failed services, reconciles this project's missing Docker forwarding rules without recreating its network or containers, and removes model runners whose project Ollama parent has exited. Web-facing containers use explicit redundant IPv4 DNS upstreams because this host's VirtioProxy-generated synthetic IPv6 resolvers are unreachable from Docker. The network fault regression verifies bridge recovery, public DNS, external HTTPS, local connectivity and continued sandbox isolation. Startup mutexes prevent concurrent launchers from racing. No repair removes persistent volumes or model files.

The `UnrestrictedAi-WSL-Anchor` task runs a host-side watchdog that keeps the dedicated WSL2 distro alive and restarts its anchor if the distro exits. This preserves the Docker and relay services needed by the browser interface across ordinary WSL termination events.

To intentionally stop automatic supervision and containers:

```powershell
Stop-ScheduledTask -TaskName UnrestrictedAi-Health
Disable-ScheduledTask -TaskName UnrestrictedAi-Health
& F:\backup\UnrestrictedAi\run_ai_stack.ps1 stop
```

Re-enable and start the task to resume. The model servers stay available when only containers are stopped.

`docker/images.lock.yml` pins service image digests; Python dependencies have lock files. `update` deliberately refreshes service images, rebuilds custom images and records new digests. Model upgrades are separate, deliberate changes to `models.lock.json`. Keep a backup of `data/`, `workspace/`, manifests and model files before a major upstream upgrade.

## Reproduction

`./run_ai_stack.sh start` and `./run_ai_stack.sh verify` run the Compose stack on Linux with Docker/Compose and NVIDIA Container Toolkit installed. Point `OLLAMA_HOST_IP` at the host running the required Ollama APIs. The Bash launcher is exercised in this project's Linux runtime.

On Windows with WSL2 enabled and the existing external Ollama on PATH, `scripts/bootstrap-windows.ps1` reuses or imports the checksummed project runtime, installs missing Linux dependencies, provisions missing models, configures WebUI and installs supervision. `scripts/provision-models.ps1` downloads pinned model revisions through the Hugging Face CLI and verifies SHA-256 before import. The checked rootfs remains in `tmp/` for reproduction. Fresh physical hardware and unrelated operating-system configurations have not been tested.

The tests establish the recorded capabilities for the supplied Huihui abliterated Qwen and Cognitive Computations Dolphin weights. They cannot establish error-free answers or zero refusals for every possible prompt, or perpetual availability independent of Windows, hardware, upstream search engines and future software updates. Dolphin failed an additional roughly 20K-token repetitive-input accuracy test; the evidence is retained in `logs/dolphin-large-repetitive-input-limitation.json`. Automatic summarization enables continued conversations, not unlimited verbatim memory.

Running Setup-and-Open.ps1 explicitly resumes the health-monitor scheduled task even if it was previously disabled. Startup fails visibly if supervision cannot start; WebUI probes use IPv4 loopback with bounded readiness waits.
