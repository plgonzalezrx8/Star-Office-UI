#!/usr/bin/env python3
"""Simple state update helper for Star Office UI."""

from __future__ import annotations

from datetime import datetime
import json
import os
import sys

STATE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "state.json")

VALID_STATES = [
    "standby",
    "working",
    "research",
    "running",
    "sync",
    "incident",
]


def load_state() -> dict:
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r", encoding="utf-8") as handle:
            payload = json.load(handle)
            if isinstance(payload, dict):
                return payload

    return {
        "state": "standby",
        "detail": "Standing by.",
        "progress": 0,
        "updated_at": datetime.now().isoformat(),
    }


def save_state(state: dict) -> None:
    with open(STATE_FILE, "w", encoding="utf-8") as handle:
        json.dump(state, handle, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 set_state.py <state> [detail]")
        print(f"Valid states: {', '.join(VALID_STATES)}")
        print("\nExamples:")
        print('  python3 set_state.py standby "Ready for next task"')
        print('  python3 set_state.py research "Investigating API behavior"')
        print('  python3 set_state.py incident "Triage in progress"')
        sys.exit(1)

    state_name = sys.argv[1].strip().lower()
    detail = sys.argv[2] if len(sys.argv) > 2 else ""

    if state_name not in VALID_STATES:
        print(f"Invalid state: {state_name}")
        print(f"Valid states: {', '.join(VALID_STATES)}")
        sys.exit(1)

    current = load_state()
    current["state"] = state_name
    current["detail"] = detail
    current["updated_at"] = datetime.now().isoformat()

    save_state(current)
    print(f"State updated: {state_name} - {detail}")
