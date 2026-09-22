# Local AI stack implementation plan

Goal: A reproducible local stack with published Qwen and Dolphin models, search, scraping, workspace retrieval and sandboxed Python execution.

Architecture: Reuse the external Windows Ollama installation. Run Docker Engine in a dedicated WSL2 distribution whose entire virtual disk is inside this project. Compose provides Open WebUI, SearXNG, Crawl4AI, Qdrant, a workspace API/MCP service, and Jupyter. Persistent application data uses explicit project bind mounts. Container layers and Linux system state live in runtime/wsl/ext4.vhdx.

Alternatives considered: Existing Docker Desktop has unrelated settings and storage outside this project; modifying its global data location risks unrelated workloads. Installing packages into the existing Ubuntu distribution writes to C:. A dedicated project distribution keeps these boundaries clear.

- [x] Inspect hardware, free space, existing Ollama and Docker.
- [x] Verify published model repositories and quantization names.
- [x] Import checksummed Ubuntu runtime on F: and install Docker/NVIDIA toolkit.
- [x] Configure Ollama process caches, acquire published models, create parameter-only aliases.
- [x] Implement Compose, search, scraping, vector indexing and isolated execution.
- [x] Configure Open WebUI search, retrieval, sandbox and tools.
- [x] Verify streaming inference, switching, throughput, GPU access, search, crawl, execution and retrieval.
- [x] Implement idempotent launch/update/stop and health repair scripts.
- [x] Verify persistence, storage locations and document measured results.

Current result: both requested published models are installed and tuned. All 27 model, integration, retrieval, execution and tool-transport checks pass, alongside the automatic-watcher and embedding checks. Browser execution, project storage, persistence, GPU access, idempotent launch and controlled automatic network recovery passed. All services are healthy and the logon supervisor is running.

Tests use arithmetic, coding, search and retrieval tasks. They measure functionality, not universal output compliance. One large model is scheduled at a time on 16 GB VRAM. Four contexts were benchmarked; 8K retained at least 90% of the best measured decoding rate for both models, with 32K aliases retained. Repair retries are bounded per operation and log failures; the supervisor restarts failed services without deleting data.
