# Completion audit — 2026-09-22

| Requested outcome | Evidence inspected | Conclusion |
| --- | --- | --- |
| Same script sets up and opens the system | Exact `Setup-and-Open.ps1 -FullVerification` run exited 0, opened the browser, and recorded 27 passing checks; the final unchanged warm rerun opened the browser in 13.69 seconds and skipped builds | Verified on this host |
| Both requested local models | Qwen and Dolphin aliases, saved long-chat reports and final desktop reports | Verified for both 32K presets; 8K aliases share the same weights/tools |
| See and act across the PC | Direct desktop report, high-level helper report and model reports show focus, shortcut, typing, snapshot readback and cleanup | Verified for tested workflows; universal exception-free control is not established |
| Existing browser tabs | Profile 2 reports for both models plus navigation/click regressions | Verified while the official extension remains connected |
| Broad online research with sources | One final 27-check suite passed live search, WebUI search/embedding, JavaScript crawl/render and a sourced search-crawl-model answer | Verified for supported public sources; exhaustive coverage is impossible to prove |
| Useful tools enabled by default | Four selected capability groups on all four presets and five visible connections | Verified for the documented capability families |
| Maximum useful settings and performance | Settings readback, measured presets, CPU embeddings, warm-launch fingerprint and 13.69-second rerun | Verified configuration; no universal cost-free maximum exists |
| Useful integrations | Windows, workspace/Python, browser, research, GitHub CLI and document tooling | Verified where listed; account-specific native services need independent authorization |
| Long chats | Both models passed saved multi-turn/summary tests | Verified within finite 32K context and lossy summary limits |
| Python execution reliability | Nine concurrent jobs and exact original repeat passed | Current checks pass; historical intermittent timeout cause remains unknown |
| Automatic recovery | Host-side WSL anchor watchdog, systemd bridge watchdog and Windows supervisor all active; controlled fault tests passed, including public DNS and HTTPS after bridge repair | Verified current recovery paths |

## Current authoritative evidence

- `data/indexer/model-desktop-qwen.json`
- `data/indexer/model-desktop-dolphin.json`
- `data/indexer/high-level-desktop-tools.json`
- `logs/desktop-action-live-check.json`
- `logs/browser-hidden-click-regression.json`
- `logs/independent-browser-click-test.json`
- `data/indexer/sandbox-concurrency-diagnostic.json`
- `data/indexer/document-artifact-verification.json`
- `logs/network-watchdog-test.json`
- `logs/wsl-anchor-test.json`
- `logs/final-launcher-verification.json`
- `data/indexer/verification.json` (27/27 passing in the final post-repair run, including the 32K `execute_python` continuation regression)

## Completion decision

The deployed stack is ready for the verified supported scope. The literal full objective remains unproven because it asks for zero failures across every possible action, every useful online tool and resource, no performance cost, and account integrations without supplying each provider's endpoint and authorization. Those are not finite, testable completion conditions. The launcher path and verified operational state are current; `STATUS.json` preserves the unresolved boundaries.
