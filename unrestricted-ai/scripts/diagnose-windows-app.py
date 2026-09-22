"""Time read-only stages used by windows-mcp's App launch workflow."""

import json
import time

from windows_mcp.desktop.service import Desktop
from windows_mcp import uia


def timed(name, function):
    started = time.perf_counter()
    try:
        value = function()
        return {
            "name": name,
            "seconds": time.perf_counter() - started,
            "ok": True,
            "value": value,
        }
    except Exception as error:
        return {
            "name": name,
            "seconds": time.perf_counter() - started,
            "ok": False,
            "error": f"{type(error).__name__}: {error}",
        }


desktop = Desktop()
apps_result = timed("get_apps_from_start_menu", desktop.get_apps_from_start_menu)
apps = apps_result.get("value", {}) if apps_result["ok"] else {}
notepad_id = apps.get("notepad")

checks = [
    {
        **apps_result,
        "value": {
            "count": len(apps),
            "notepad_id": notepad_id,
        }
        if apps_result["ok"]
        else None,
    }
]
print(json.dumps({"stage": "apps", "check": checks[-1]}), flush=True)

if notepad_id:
    checks.append(
        timed("check_app_exists", lambda: desktop._check_app_exists(notepad_id))
    )
    print(json.dumps({"stage": "app_id", "check": checks[-1]}), flush=True)

print(json.dumps({"stage": "uia_window", "status": "starting"}), flush=True)
checks.append(
    timed(
        "uia_regex_window_exists",
        lambda: uia.WindowControl(RegexName=r"(?i).*notepad.*").Exists(
            maxSearchSeconds=10
        ),
    )
)
print(json.dumps({"stage": "uia_window", "check": checks[-1]}), flush=True)

print(json.dumps({"checks": checks}, indent=2))
