"""Ensure ordinary starts rebuild local images only when build inputs change."""

from pathlib import Path


script = Path("/project/run_ai_stack.sh").read_text(encoding="utf-8")
required = (
    "docker-build.fingerprint",
    "workspace.Dockerfile",
    "workspace.requirements.lock",
    "workspace_api.py",
    "sandbox.Dockerfile",
    "sandbox.requirements.lock",
    "up -d --no-build",
)
for phrase in required:
    assert phrase in script, phrase

assert 'start) "${compose[@]}" up -d --build' not in script
print("PASS ordinary startup uses a content-addressed local-image build cache")
