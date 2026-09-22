"""Verify a saved-chat local model can drive a reversible desktop workflow."""

import argparse
import json
import pathlib
import re
import time
import uuid

import requests


parser = argparse.ArgumentParser()
parser.add_argument(
    "--model",
    required=True,
    choices=["local-qwen:27b-32k", "local-dolphin:24b-32k"],
)
args = parser.parse_args()

webui = "http://open-webui:8080"
workspace = "http://workspace-api:8000"
session = requests.Session()


def webui_call(method, path, body=None):
    response = session.request(method, webui + path, json=body, timeout=60)
    response.raise_for_status()
    return response.json()


def workspace_call(path, body):
    response = requests.post(workspace + path, json=body, timeout=90)
    response.raise_for_status()
    return response.json()


def action(**body):
    result = workspace_call("/host/desktop/action", body)
    if result.get("isError"):
        raise RuntimeError(str(result))
    return result


def snapshot():
    result = workspace_call(
        "/host/desktop/inspect",
        {"include_image": False, "include_browser_dom": False},
    )
    encoded = result["content"][0]["text"]
    decoded = json.loads(encoded)
    return decoded[0] if isinstance(decoded, list) else decoded


def coordinates(line):
    match = re.search(r"\((\d+),(\d+)\)", line or "")
    if not match:
        raise AssertionError(f"Coordinates missing from line: {line!r}")
    return [int(match.group(1)), int(match.group(2))]


token = webui_call(
    "POST",
    "/api/v1/auths/signin",
    {"email": "admin@localhost", "password": "admin"},
)["token"]
session.headers["Authorization"] = "Bearer " + token

model = webui_call("GET", "/api/v1/models/model?id=" + args.model)
groups = model["meta"]["toolIds"]
assert "server:windows" in groups, groups

marker = (
    "QWEN-DESKTOP-MODEL-VERIFIED-3719"
    if "qwen" in args.model
    else "DOLPHIN-DESKTOP-MODEL-VERIFIED-6842"
)
prompt = f"""Use the Windows desktop tools to perform this reversible verification:
1. Inspect the desktop.
2. Call open_windows_app with name Notepad. This waits for Notepad to be focused.
3. Call send_windows_shortcut with shortcut ctrl+n to create a new empty tab.
4. Inspect again and find the focused document named Text editor.
5. Call type_in_focused_windows_control with text {marker}, expected_app Notepad, and clear false. This performs a fresh coordinate inspection for you. Do not use guessed coordinates.
6. Inspect once more and report the exact marker only after you see it.
If a tool returns an argument error, correct the arguments and retry the tool. Do not give me instructions to perform the task myself. Do not use PowerShell, do not save anything, do not close any tab, and do not modify an existing document."""

message_id = str(uuid.uuid4())
started = time.monotonic()
messages = [{"role": "user", "content": prompt}]
body = {
    "model": args.model,
    "messages": messages,
    "stream": True,
    "id": message_id,
    "parent_id": None,
    "session_id": "desktop-action-verifier",
    "tool_ids": groups,
    "features": {},
    "user_message": {
        "id": str(uuid.uuid4()),
        "parentId": None,
        "role": "user",
        "content": prompt,
        "timestamp": int(time.time()),
    },
    "params": {
        "temperature": 0,
        "num_predict": 512,
        "function_calling": "native" if "qwen" in args.model else "legacy",
    },
}
if "qwen" in args.model:
    body["params"]["think"] = False

chat_id = webui_call("POST", "/api/chat/completions", body).get("chat_id")
if not chat_id:
    raise RuntimeError("Open WebUI did not return a chat id")

while time.monotonic() - started < 900:
    message = webui_call("GET", "/api/v1/chats/" + chat_id)["chat"]["history"][
        "messages"
    ].get(message_id, {})
    if message.get("error"):
        raise RuntimeError(str(message["error"]))
    if message.get("done"):
        break
    time.sleep(2)
else:
    raise TimeoutError("Model desktop workflow timed out")

serialized = json.dumps(message)
answer = message.get("content", "")
tool_names = [
    name
    for name in (
        "inspect_windows_desktop",
        "open_windows_app",
        "send_windows_shortcut",
        "type_in_focused_windows_control",
    )
    if name in serialized
]
assert marker in answer, answer
assert tool_names == [
    "inspect_windows_desktop",
    "open_windows_app",
    "send_windows_shortcut",
    "type_in_focused_windows_control",
], tool_names

observed = snapshot()
assert marker in observed, "Marker was not visible in the direct desktop readback"

# Clean up only the disposable marker tab. Existing documents remain open.
action(action="switch_app", text="Notepad")
state = snapshot()
assert marker in state, "Marker tab was not active during cleanup"
tab_line = next(
    (
        line
        for line in state.splitlines()
        if 'tab item "' in line and marker[:35] in line
    ),
    None,
)
action(action="click", loc=coordinates(tab_line))
action(action="shortcut", text="ctrl+w")
state = snapshot()
discard_line = next(
    (
        line
        for line in state.splitlines()
        if re.search(r'button "(Don.t save|Don.t Save|Discard)"', line)
    ),
    None,
)
if discard_line:
    action(action="click", loc=coordinates(discard_line))
    state = snapshot()

assert marker not in state, "Disposable marker remained after cleanup"
assert "config.toml" in state, "Existing config tab was not preserved"

report = {
    "passed": True,
    "model": args.model,
    "chat_id": chat_id,
    "seconds": time.monotonic() - started,
    "marker": marker,
    "tools": tool_names,
    "answer": answer,
    "directReadback": True,
    "cleanup": {
        "markerAbsent": True,
        "configTabPreserved": True,
    },
}
name = "qwen" if "qwen" in args.model else "dolphin"
path = pathlib.Path("/state") / f"model-desktop-{name}.json"
path.write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps(report, indent=2))
