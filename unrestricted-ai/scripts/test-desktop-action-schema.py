"""Regression checks for the model-facing Windows action schema."""

import requests


schema = requests.get(
    "http://workspace-api:8000/openapi/windows.json", timeout=20
).json()
action = schema["components"]["schemas"]["DesktopAction"]
properties = action["properties"]

required_descriptions = {
    "action": "operation",
    "label": "exactly one",
    "loc": "exactly one",
    "text": "switch_app",
}
for name, phrase in required_descriptions.items():
    description = properties[name].get("description", "").lower()
    assert phrase in description, (name, description)

examples = action.get("examples", [])
assert {"action": "switch_app", "text": "Notepad"} in examples, examples
assert {"action": "shortcut", "text": "ctrl+n"} in examples, examples
assert not any(example.get("action") == "type" and example.get("loc") for example in examples), examples

print("PASS model-facing desktop schema descriptions and examples")
