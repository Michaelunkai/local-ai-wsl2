"""Exercise the model-facing high-level desktop helpers and clean up safely."""

import json
import pathlib
import re
import time

import requests


BASE = "http://workspace-api:8000"
MARKER = "HIGHLEVEL-DESKTOP-TOOLS-VERIFIED-4481"


def post(path, body):
    response = requests.post(BASE + path, json=body, timeout=90)
    response.raise_for_status()
    return response.json()


def snapshot():
    result = post(
        "/host/desktop/inspect",
        {"include_image": False, "include_browser_dom": False},
    )
    decoded = json.loads(result["content"][0]["text"])
    return decoded[0] if isinstance(decoded, list) else decoded


def coordinates(line):
    match = re.search(r"\((\d+),(\d+)\)", line or "")
    if not match:
        raise AssertionError(f"Coordinates missing from line: {line!r}")
    return [int(match.group(1)), int(match.group(2))]


started = time.monotonic()
post("/host/desktop/open", {"name": "Notepad"})
before = snapshot()
preexisting_tabs = [
    line for line in before.splitlines() if 'tab item "' in line
]
post("/host/desktop/shortcut", {"shortcut": "ctrl+n"})
typed = post(
    "/host/desktop/type-focused",
    {"text": MARKER, "expected_app": "Notepad", "clear": False},
)
assert typed["structuredContent"]["visibleInFollowUpSnapshot"] is True, typed
state = snapshot()
assert MARKER in state

marker_tab = next(
    (
        line
        for line in state.splitlines()
        if 'tab item "' in line and MARKER[:35] in line
    ),
    None,
)
post("/host/desktop/action", {"action": "click", "loc": coordinates(marker_tab)})
post("/host/desktop/shortcut", {"shortcut": "ctrl+w"})
state = snapshot()
discard = next(
    (
        line
        for line in state.splitlines()
        if re.search(r'button "(Don.t save|Don.t Save|Discard)"', line)
    ),
    None,
)
if discard:
    post("/host/desktop/action", {"action": "click", "loc": coordinates(discard)})
    state = snapshot()

assert MARKER not in state
for tab in preexisting_tabs:
    name = re.search(r'tab item "([^"]+)', tab)
    if name and MARKER not in name.group(1):
        assert name.group(1).replace('. Selected.','')[:25] in state

report = {
    "passed": True,
    "seconds": time.monotonic() - started,
    "marker": MARKER,
    "focusWait": True,
    "freshFocusedControlDiscovery": True,
    "directReadback": True,
    "cleanup": {"markerAbsent": True, "preexistingTabsPreserved": True},
}
path = pathlib.Path("/state/high-level-desktop-tools.json")
path.write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps(report, indent=2))
