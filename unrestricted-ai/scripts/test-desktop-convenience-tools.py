"""Regression checks for reliable high-level desktop tools exposed to models."""

from pathlib import Path

import requests


schema = requests.get(
    "http://workspace-api:8000/openapi/windows.json", timeout=20
).json()
operation_ids = {
    operation["operationId"]
    for methods in schema["paths"].values()
    for operation in methods.values()
    if isinstance(operation, dict) and "operationId" in operation
}
required = {
    "open_windows_app",
    "send_windows_shortcut",
    "type_in_focused_windows_control",
}
assert required.issubset(operation_ids), required - operation_ids

configuration = Path("/project/scripts/configure-webui.py").read_text(encoding="utf-8")
for name in required:
    assert name in configuration, name

print("PASS reliable high-level desktop tools are exposed and persisted")
