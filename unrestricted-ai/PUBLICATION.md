# Published source snapshot

Operational launcher on the tested Windows host:
`F:\backup\UnrestrictedAi\Setup-and-Open.ps1`

This directory preserves the repository's existing installer and adds the separately deployed Qwen/Dolphin WebUI stack. It is a source snapshot, not a portable backup of the running installation. Credentials, chats, browser profiles, model weights, runtime disks and logs are excluded.

Validation on the original host: the prior full suite passed 26 checks; subsequent startup diagnostics passed four regression cases and live DNS/HTTPS probes. The latest launcher passed after adding official MCP persistent memory. Memory creation, readback, disk persistence and cleanup passed through the authenticated host bridge. Model-driven use of the newly added memory tool has not been tested.

The stack requires Windows/WSL prerequisites and pinned dependencies documented in README.md. A fresh-machine installation was not validated by this publication. Some scripts reference the original host paths. Four npm advisories remain in existing Desktop Commander transitive dependencies; no forced downgrade was applied.

This publication does not claim every online integration, universal failure-free operation, zero performance cost, or account services without their authentication setup.
