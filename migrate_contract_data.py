#!/usr/bin/env python3
"""One-time migration utility for state.json and agents-state.json contract changes."""

from __future__ import annotations

from datetime import datetime
import json
import os
from typing import Any

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
STATE_FILE = os.path.join(ROOT_DIR, "state.json")
AGENTS_FILE = os.path.join(ROOT_DIR, "agents-state.json")

STATE_MAP = {
    "idle": "standby",
    "writing": "working",
    "researching": "research",
    "executing": "running",
    "syncing": "sync",
    "error": "incident",
    "standby": "standby",
    "working": "working",
    "research": "research",
    "running": "running",
    "sync": "sync",
    "incident": "incident",
}

AREA_MAP = {
    "breakroom": "lounge",
    "writing": "workzone",
    "error": "incident_bay",
    "lounge": "lounge",
    "workzone": "workzone",
    "incident_bay": "incident_bay",
}


def read_json(path: str, default: Any) -> Any:
    if not os.path.exists(path):
        return default
    try:
        with open(path, "r", encoding="utf-8") as handle:
            return json.load(handle)
    except Exception:
        return default


def write_json(path: str, payload: Any) -> None:
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)


def normalize_state(raw: Any) -> str:
    return STATE_MAP.get(str(raw or "").strip().lower(), "standby")


def normalize_area(raw: Any, state: str) -> str:
    value = AREA_MAP.get(str(raw or "").strip().lower())
    if value:
        return value
    if state == "incident":
        return "incident_bay"
    if state == "standby":
        return "lounge"
    return "workzone"


def migrate_state_file() -> bool:
    payload = read_json(STATE_FILE, {})
    if not isinstance(payload, dict):
        payload = {}

    old_state = payload.get("state")
    payload["state"] = normalize_state(old_state)

    if not payload.get("detail"):
        payload["detail"] = "Standing by."

    if not payload.get("updated_at"):
        payload["updated_at"] = datetime.now().isoformat()

    write_json(STATE_FILE, payload)
    return old_state != payload.get("state")


def migrate_agents_file() -> int:
    payload = read_json(AGENTS_FILE, [])
    if not isinstance(payload, list):
        payload = []

    migrated_count = 0
    out = []

    for item in payload:
        if not isinstance(item, dict):
            continue

        old_state = item.get("state")
        new_state = normalize_state(old_state)
        item["state"] = new_state
        item["area"] = normalize_area(item.get("area"), new_state)

        if old_state != new_state:
            migrated_count += 1

        if not item.get("updated_at"):
            item["updated_at"] = datetime.now().isoformat()

        out.append(item)

    write_json(AGENTS_FILE, out)
    return migrated_count


def main() -> None:
    state_changed = migrate_state_file()
    agents_changed = migrate_agents_file()

    print("Migration complete.")
    print(f"Main state updated: {state_changed}")
    print(f"Agent records updated: {agents_changed}")


if __name__ == "__main__":
    main()
