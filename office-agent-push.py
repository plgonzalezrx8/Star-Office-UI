#!/usr/bin/env python3
"""
Star Lobster Office - OpenClaw agent status pusher.

Usage:
1) Fill JOIN_KEY and AGENT_NAME below.
2) Run: python3 office-agent-push.py
3) The script joins once, then pushes local status every interval.
"""

from __future__ import annotations

import json
import os
import sys
import time
from datetime import datetime

# Required setup values.
JOIN_KEY = ""
AGENT_NAME = ""
OFFICE_URL = "https://office.example.com"

# Push configuration.
PUSH_INTERVAL_SECONDS = 15
JOIN_ENDPOINT = "/agents/join"
PUSH_ENDPOINT = "/agents/push"
LOCAL_STATE_CACHE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "office-agent-state.json")

# Local status discovery candidates.
DEFAULT_STATE_CANDIDATES = [
    "/root/.openclaw/workspace/star-office-ui/state.json",
    "/root/.openclaw/workspace/state.json",
    os.path.join(os.getcwd(), "state.json"),
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "state.json"),
]

LOCAL_STATUS_TOKEN = os.environ.get("OFFICE_LOCAL_STATUS_TOKEN", "")
LOCAL_STATUS_URL = os.environ.get("OFFICE_LOCAL_STATUS_URL", "http://127.0.0.1:18791/state")
LOCAL_STATE_FILE = os.environ.get("OFFICE_LOCAL_STATE_FILE", "")
VERBOSE = os.environ.get("OFFICE_VERBOSE", "0") in {"1", "true", "TRUE", "yes", "YES"}

CANONICAL_STATES = {"standby", "working", "research", "running", "sync", "incident"}
LEGACY_TO_CANONICAL = {
    "idle": "standby",
    "writing": "working",
    "researching": "research",
    "executing": "running",
    "syncing": "sync",
    "error": "incident",
}


def load_local_cache() -> dict:
    if os.path.exists(LOCAL_STATE_CACHE_FILE):
        try:
            with open(LOCAL_STATE_CACHE_FILE, "r", encoding="utf-8") as handle:
                payload = json.load(handle)
                if isinstance(payload, dict):
                    return payload
        except Exception:
            pass

    return {
        "agentId": None,
        "joined": False,
        "joinKey": JOIN_KEY,
        "agentName": AGENT_NAME,
        "updatedAt": datetime.now().isoformat(),
    }


def save_local_cache(payload: dict) -> None:
    payload["updatedAt"] = datetime.now().isoformat()
    with open(LOCAL_STATE_CACHE_FILE, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)


def normalize_state(raw: str | None) -> str:
    token = (raw or "").strip().lower()
    if token in CANONICAL_STATES:
        return token
    if token in LEGACY_TO_CANONICAL:
        return LEGACY_TO_CANONICAL[token]
    if token in {"busy", "work"}:
        return "working"
    if token in {"run", "execute", "exec"}:
        return "running"
    if token in {"researching", "search"}:
        return "research"
    if token in {"syncing", "backup"}:
        return "sync"
    if token in {"bug", "alert", "failure"}:
        return "incident"
    return "standby"


def infer_state_from_detail(detail: str, fallback_state: str = "standby") -> str:
    """Infer canonical state from English detail text only."""
    text = (detail or "").strip().lower()

    incident_words = ["incident", "error", "bug", "alert", "failure", "outage"]
    sync_words = ["sync", "backup", "replicate"]
    research_words = ["research", "investigate", "analyze", "validate"]
    running_words = ["run", "execute", "pipeline", "deploy", "processing"]
    working_words = ["work", "draft", "build", "implement", "coding"]
    standby_words = ["standby", "idle", "waiting", "ready", "complete", "done"]

    if any(word in text for word in incident_words):
        return "incident"
    if any(word in text for word in sync_words):
        return "sync"
    if any(word in text for word in research_words):
        return "research"
    if any(word in text for word in running_words):
        return "running"
    if any(word in text for word in working_words):
        return "working"
    if any(word in text for word in standby_words):
        return "standby"

    return fallback_state


def fetch_local_status() -> dict:
    """Read local status from state file first, then local HTTP endpoint."""
    candidate_files = []
    if LOCAL_STATE_FILE:
        candidate_files.append(LOCAL_STATE_FILE)
    for path in DEFAULT_STATE_CANDIDATES:
        if path not in candidate_files:
            candidate_files.append(path)

    for path in candidate_files:
        try:
            if path and os.path.exists(path):
                with open(path, "r", encoding="utf-8") as handle:
                    payload = json.load(handle)
                if not isinstance(payload, dict):
                    continue

                if "state" not in payload and "detail" not in payload:
                    continue

                state = normalize_state(payload.get("state"))
                detail = (payload.get("detail") or "").strip()
                state = infer_state_from_detail(detail, fallback_state=state)

                if VERBOSE:
                    print(f"[source:file] path={path} state={state} detail={detail[:80]}")
                return {"state": state, "detail": detail}
        except Exception:
            continue

    try:
        import requests

        headers = {}
        if LOCAL_STATUS_TOKEN:
            headers["Authorization"] = f"Bearer {LOCAL_STATUS_TOKEN}"

        response = requests.get(LOCAL_STATUS_URL, headers=headers, timeout=5)
        if response.status_code == 200:
            payload = response.json()
            state = normalize_state(payload.get("state"))
            detail = (payload.get("detail") or "").strip()
            state = infer_state_from_detail(detail, fallback_state=state)

            if VERBOSE:
                print(f"[source:http] url={LOCAL_STATUS_URL} state={state} detail={detail[:80]}")
            return {"state": state, "detail": detail}

        if response.status_code == 401:
            return {
                "state": "standby",
                "detail": "Local /state requires auth (401). Set OFFICE_LOCAL_STATUS_TOKEN.",
            }
    except Exception:
        pass

    if VERBOSE:
        print("[source:fallback] state=standby detail=Standing by")
    return {"state": "standby", "detail": "Standing by"}


def do_join(local_cache: dict) -> bool:
    import requests

    payload = {
        "name": local_cache.get("agentName", AGENT_NAME),
        "joinKey": local_cache.get("joinKey", JOIN_KEY),
        "state": "standby",
        "detail": "Just connected",
    }

    response = requests.post(f"{OFFICE_URL}{JOIN_ENDPOINT}", json=payload, timeout=10)
    if response.status_code in (200, 201):
        data = response.json()
        if data.get("ok"):
            local_cache["joined"] = True
            local_cache["agentId"] = data.get("agentId")
            save_local_cache(local_cache)
            print(f"Joined Star Lobster Office successfully. agentId={local_cache['agentId']}")
            return True

    print(f"Join failed: {response.text}")
    return False


def do_push(local_cache: dict, status_payload: dict) -> bool:
    import requests

    payload = {
        "agentId": local_cache.get("agentId"),
        "joinKey": local_cache.get("joinKey", JOIN_KEY),
        "state": status_payload.get("state", "standby"),
        "detail": status_payload.get("detail", ""),
        "name": local_cache.get("agentName", AGENT_NAME),
    }

    response = requests.post(f"{OFFICE_URL}{PUSH_ENDPOINT}", json=payload, timeout=10)
    if response.status_code in (200, 201):
        data = response.json()
        if data.get("ok"):
            area = data.get("area", "lounge")
            print(f"State synced successfully. area={area}")
            return True

    if response.status_code in (403, 404):
        try:
            message = (response.json() or {}).get("msg", response.text)
        except Exception:
            message = response.text

        print(f"Access denied or agent removed ({response.status_code}). Stopping push loop: {message}")
        local_cache["joined"] = False
        local_cache["agentId"] = None
        save_local_cache(local_cache)
        sys.exit(1)

    print(f"Push failed: {response.text}")
    return False


def main() -> None:
    local_cache = load_local_cache()

    if not JOIN_KEY or not AGENT_NAME:
        print("Please set JOIN_KEY and AGENT_NAME at the top of office-agent-push.py before running.")
        sys.exit(1)

    if not local_cache.get("joined") or not local_cache.get("agentId"):
        if not do_join(local_cache):
            sys.exit(1)

    print(f"Starting continuous status push loop every {PUSH_INTERVAL_SECONDS}s")
    print("State mapping: active work -> workzone, standby -> lounge, incidents -> incident_bay")
    print("If local /state returns 401, set OFFICE_LOCAL_STATUS_TOKEN or OFFICE_LOCAL_STATUS_URL.")

    try:
        while True:
            try:
                local_status = fetch_local_status()
                do_push(local_cache, local_status)
            except Exception as exc:
                print(f"Push iteration error: {exc}")
            time.sleep(PUSH_INTERVAL_SECONDS)
    except KeyboardInterrupt:
        print("Stopping status push loop.")
        sys.exit(0)


if __name__ == "__main__":
    main()
