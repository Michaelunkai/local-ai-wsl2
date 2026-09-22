# Current integration coverage

Launcher: `F:\backup\UnrestrictedAi\Setup-and-Open.ps1`
Web UI: `http://localhost:3080`

| Capability | Current implementation | Authoritative evidence or dependency |
| --- | --- | --- |
| Both requested model families | Published Qwen Huihui abliterated and Dolphin variants with 8K/32K aliases | Both 32K variants passed long saved chats and final model-driven desktop workflows |
| Windows files and commands | Typed Windows tools, Desktop Commander 0.2.51 and Windows MCP 0.8.5 | Real F: listings, file write/read and PowerShell execution passed for both models |
| Windows desktop actions | Accessibility/screenshot inspection, low-level actions and high-level focus/typing helpers | `logs/desktop-action-live-check.json`, `data/indexer/high-level-desktop-tools.json`, `data/indexer/model-desktop-qwen.json`, `data/indexer/model-desktop-dolphin.json` |
| Existing browser profile 2 | Official Playwright extension through the authenticated host bridge | Both models read the connected page; navigation, snapshot and click passed; hidden-tab interaction regression passed |
| Independent browser | Separate public-research Playwright profile | Navigation, snapshot and link click passed |
| Live web research | SearXNG, Crawl4AI, parallel queries, balanced ranks, varied domains and source URLs | Final full suite passed live search, WebUI search/embedding, JavaScript crawl/render and a sourced search-crawl-model answer |
| Python and data analysis | Isolated Jupyter with NumPy, pandas, matplotlib and Pillow | Both model chats used Python; nine concurrent executions and exact WebUI repeat passed |
| Word, spreadsheets, slides and PDF | python-docx, openpyxl, python-pptx, ReportLab and pypdf | All four formats were created, reopened and downloaded byte-identically |
| GitHub | Existing authenticated GitHub CLI reachable through Windows commands | Authenticated API returned the configured account; credentials remain in the CLI keyring |
| Windows app/process/document catalog | Selected-tool schema discovery through Desktop Commander and Windows MCP | Catalog/schema discovery and direct wrappers passed; consequential actions still depend on the user's requested scope |
| Additional MCP/OpenAPI services | WebUI supports separately configured servers | Each service still needs a real endpoint and any required authorization |
| Email, calendars and cloud drives | Existing browser sessions, or independently configured provider APIs | No provider credentials are fabricated or copied from Codex sessions |
| Image/audio provider services | Local file/image generation and optional provider integration points | Proprietary hosted image, voice or account services require their own model/provider and credentials |
| Codex task/app controls | Codex-specific APIs | These APIs are not transferable standalone integrations for local models |

## Runtime resilience

- WSL uses the host's successful VirtioProxy mode directly instead of first attempting the failing NAT mode.
- Every web-facing container has redundant explicit IPv4 DNS upstreams, avoiding this host's unreachable VirtioProxy-generated IPv6 resolver addresses.
- `UnrestrictedAi-WSL-Anchor` keeps the VM alive across ordinary client exits.
- `unrestricted-ai-network-reconcile.timer` repairs project bridge rules without recreating containers or weakening the internal sandbox network; its live fault test also verifies DNS and external HTTPS.
- `UnrestrictedAi-Health` supervises Windows processes and service health under system Windows PowerShell.
- Image builds are content-addressed; unchanged launches do not contact the base-image registry or rebuild.

## Current limits

No finite test can establish error-free behavior for every future PC state, website, account or third-party UI. Every online tool and every relevant resource are unbounded sets, while enabling all work concurrently would consume measurable CPU, memory, GPU time and network bandwidth. The verified capability families above are enabled by default; account-specific native APIs remain dependent on endpoints, credentials and consent.
