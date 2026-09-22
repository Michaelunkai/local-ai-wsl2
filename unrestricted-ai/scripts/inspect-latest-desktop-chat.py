"""Print redacted diagnostics for the newest model desktop verification chat."""

import json

import requests


BASE = "http://open-webui:8080"
session = requests.Session()
token = session.post(
    BASE + "/api/v1/auths/signin",
    json={"email": "admin@localhost", "password": "admin"},
    timeout=30,
).json()["token"]
session.headers["Authorization"] = "Bearer " + token

chats = session.get(BASE + "/api/v1/chats/?page=1", timeout=30).json()
for summary in chats:
    chat_id = summary.get("id")
    if not chat_id:
        continue
    record = session.get(BASE + "/api/v1/chats/" + chat_id, timeout=30).json()
    serialized = json.dumps(record)
    if "DOLPHIN-DESKTOP-MODEL-VERIFIED-6842" not in serialized:
        continue
    messages = record.get("chat", {}).get("history", {}).get("messages", {})
    assistant = [m for m in messages.values() if m.get("role") == "assistant"]
    latest = assistant[-1] if assistant else {}
    tool_events = []
    for source in latest.get("sources", []):
        metadata = (source.get("metadata") or [{}])[0]
        document = "\n".join(source.get("document") or [])
        tool_events.append(
            {
                "source": source.get("source", {}).get("name"),
                "parameters": metadata.get("parameters"),
                "result_excerpt": document[:800],
            }
        )
    print(
        json.dumps(
            {
                "chat_id": chat_id,
                "model": latest.get("model"),
                "done": latest.get("done"),
                "error": latest.get("error"),
                "content": latest.get("content"),
                "tool_names": [
                    name
                    for name in (
                        "inspect_windows_desktop",
                        "interact_windows_desktop",
                    )
                    if name in json.dumps(latest)
                ],
                "tool_events": tool_events,
            },
            indent=2,
        )
    )
    break
else:
    raise SystemExit("No Dolphin desktop-verification chat found")
