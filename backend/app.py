#!/usr/bin/env python3
"""Star Office UI backend service (US-localized contract)."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from flask import Flask, jsonify, make_response, request
import json
import os
import random
import re
import string
import threading
from typing import Any

# Project paths (no absolute machine-specific paths).
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MEMORY_DIR = os.path.join(os.path.dirname(ROOT_DIR), "memory")
FRONTEND_DIR = os.path.join(ROOT_DIR, "frontend")
STATE_FILE = os.path.join(ROOT_DIR, "state.json")
AGENTS_STATE_FILE = os.path.join(ROOT_DIR, "agents-state.json")
JOIN_KEYS_FILE = os.path.join(ROOT_DIR, "join-keys.json")

# Contract constants.
CANONICAL_STATES = {"standby", "working", "research", "running", "sync", "incident"}
WORKLIKE_STATES = {"working", "research", "running"}
AREA_BY_STATE = {
    "standby": "lounge",
    "working": "workzone",
    "research": "workzone",
    "running": "workzone",
    "sync": "workzone",
    "incident": "incident_bay",
}

# Legacy compatibility for persisted data migration.
STATE_ALIASES = {
    "standby": {"standby", "idle", "ready", "waiting"},
    "working": {"working", "writing", "busy", "work"},
    "research": {"research", "researching", "search"},
    "running": {"running", "run", "executing", "execute", "exec"},
    "sync": {"sync", "syncing", "backup"},
    "incident": {"incident", "error", "bug", "alert", "failure"},
}
AREA_ALIASES = {
    "lounge": {"lounge", "breakroom", "rest_area"},
    "workzone": {"workzone", "writing", "work_area", "desk"},
    "incident_bay": {"incident_bay", "error", "bug_area"},
}

# Version stamp for cache-busting static references in HTML.
VERSION_TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")

app = Flask(__name__, static_folder=FRONTEND_DIR, static_url_path="/static")
join_lock = threading.Lock()


def _read_json(path: str, default: Any) -> Any:
    if not os.path.exists(path):
        return default
    try:
        with open(path, "r", encoding="utf-8") as handle:
            return json.load(handle)
    except Exception:
        return default


def _write_json(path: str, payload: Any) -> None:
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)


def normalize_state(raw: Any) -> str:
    text = str(raw or "").strip().lower()
    for canonical, aliases in STATE_ALIASES.items():
        if text in aliases:
            return canonical
    return "standby"


def normalize_area(raw: Any, state: str) -> str:
    text = str(raw or "").strip().lower()
    for canonical, aliases in AREA_ALIASES.items():
        if text in aliases:
            return canonical
    return AREA_BY_STATE.get(state, "lounge")


def _parse_iso(raw: str | None) -> datetime | None:
    if not raw:
        return None
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except Exception:
        return None


def _seconds_since(raw: str | None, now: datetime) -> float | None:
    parsed = _parse_iso(raw)
    if not parsed:
        return None
    if parsed.tzinfo:
        return (datetime.now(timezone.utc) - parsed.astimezone(timezone.utc)).total_seconds()
    return (now - parsed).total_seconds()


DEFAULT_MAIN_STATE = {
    "state": "standby",
    "detail": "Standing by for the next task.",
    "progress": 0,
    "ttl_seconds": 300,
    "updated_at": datetime.now().isoformat(),
}

DEFAULT_AGENTS = [
    {
        "agentId": "star",
        "name": "Star",
        "isMain": True,
        "state": "standby",
        "detail": "Standing by and ready to help.",
        "updated_at": datetime.now().isoformat(),
        "area": "lounge",
        "source": "local",
        "joinKey": None,
        "authStatus": "approved",
        "authExpiresAt": None,
        "lastPushAt": None,
    },
    {
        "agentId": "npc1",
        "name": "NPC 1",
        "isMain": False,
        "state": "working",
        "detail": "Preparing a daily trend summary.",
        "updated_at": datetime.now().isoformat(),
        "area": "workzone",
        "source": "demo",
        "joinKey": None,
        "authStatus": "approved",
        "authExpiresAt": None,
        "lastPushAt": None,
    },
]


def migrate_main_state(raw_state: dict[str, Any]) -> tuple[dict[str, Any], bool]:
    migrated = dict(DEFAULT_MAIN_STATE)
    migrated.update(raw_state or {})

    state = normalize_state(migrated.get("state"))
    changed = state != migrated.get("state")
    migrated["state"] = state

    if not migrated.get("detail"):
        migrated["detail"] = "Standing by for the next task."
        changed = True

    if not isinstance(migrated.get("progress"), int):
        migrated["progress"] = 0
        changed = True

    if not migrated.get("updated_at"):
        migrated["updated_at"] = datetime.now().isoformat()
        changed = True

    return migrated, changed


def migrate_agent_record(agent: dict[str, Any]) -> tuple[dict[str, Any], bool]:
    migrated = dict(agent or {})
    changed = False

    state = normalize_state(migrated.get("state"))
    if state != migrated.get("state"):
        migrated["state"] = state
        changed = True

    target_area = normalize_area(migrated.get("area"), state)
    if target_area != migrated.get("area"):
        migrated["area"] = target_area
        changed = True

    if not migrated.get("updated_at"):
        migrated["updated_at"] = datetime.now().isoformat()
        changed = True

    if "detail" not in migrated or migrated.get("detail") is None:
        migrated["detail"] = ""
        changed = True

    return migrated, changed


def load_main_state() -> dict[str, Any]:
    payload = _read_json(STATE_FILE, dict(DEFAULT_MAIN_STATE))
    if not isinstance(payload, dict):
        payload = dict(DEFAULT_MAIN_STATE)

    state, migrated = migrate_main_state(payload)

    # Auto-standby when stale work states no longer receive updates.
    try:
        ttl_seconds = int(state.get("ttl_seconds", 300))
        if state.get("state") in WORKLIKE_STATES:
            age = _seconds_since(state.get("updated_at"), datetime.now())
            if age is not None and age > ttl_seconds:
                state["state"] = "standby"
                state["detail"] = "Auto-reset to standby after timeout."
                state["progress"] = 0
                state["updated_at"] = datetime.now().isoformat()
                migrated = True
    except Exception:
        pass

    if migrated:
        _write_json(STATE_FILE, state)

    return state


def save_main_state(state: dict[str, Any]) -> None:
    _write_json(STATE_FILE, state)


def load_agents_state() -> list[dict[str, Any]]:
    payload = _read_json(AGENTS_STATE_FILE, list(DEFAULT_AGENTS))
    if not isinstance(payload, list):
        payload = list(DEFAULT_AGENTS)

    changed_any = False
    migrated_agents: list[dict[str, Any]] = []
    for record in payload:
        if not isinstance(record, dict):
            changed_any = True
            continue
        migrated, changed = migrate_agent_record(record)
        changed_any = changed_any or changed
        migrated_agents.append(migrated)

    if not migrated_agents:
        migrated_agents = list(DEFAULT_AGENTS)
        changed_any = True

    if changed_any:
        _write_json(AGENTS_STATE_FILE, migrated_agents)

    return migrated_agents


def save_agents_state(agents: list[dict[str, Any]]) -> None:
    _write_json(AGENTS_STATE_FILE, agents)


def load_join_keys() -> dict[str, Any]:
    payload = _read_json(JOIN_KEYS_FILE, {"keys": []})
    if not isinstance(payload, dict) or not isinstance(payload.get("keys"), list):
        return {"keys": []}
    return payload


def save_join_keys(keys_payload: dict[str, Any]) -> None:
    _write_json(JOIN_KEYS_FILE, keys_payload)


def sanitize_content(text: str) -> str:
    """Remove obvious sensitive tokens from memo snippets."""
    content = text
    content = re.sub(r"ou_[a-f0-9]+", "[USER]", content)
    content = re.sub(r'user_id="[^"]+"', 'user_id="[REDACTED]"', content)
    content = re.sub(r"/root/[^\"\s]+", "[PATH]", content)
    content = re.sub(r"\d{1,3}(?:\.\d{1,3}){3}", "[IP]", content)
    content = re.sub(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", "[EMAIL]", content)
    content = re.sub(r"\+?\d[\d\-\s()]{8,}\d", "[PHONE]", content)
    return content


def extract_memo_from_file(file_path: str) -> str:
    """Generate a short US-English memo summary from markdown content."""
    try:
        with open(file_path, "r", encoding="utf-8") as handle:
            content = handle.read()

        candidates: list[str] = []
        for line in content.splitlines():
            cleaned = line.strip()
            if not cleaned or cleaned.startswith("#"):
                continue
            if cleaned.startswith("- "):
                cleaned = cleaned[2:].strip()
            if len(cleaned) >= 8:
                candidates.append(cleaned)

        if not candidates:
            return "No notable updates from yesterday.\n\nShip small, ship often."

        summary_lines: list[str] = []
        for point in candidates[:3]:
            sanitized = sanitize_content(point)
            if len(sanitized) > 88:
                sanitized = sanitized[:85] + "..."
            summary_lines.append(f"- {sanitized}")

        workplace_lines = [
            "Ship small, ship often.",
            "Clarity beats cleverness.",
            "Fix the fire first, then the root cause.",
            "If it is not logged, it did not happen.",
            "Stability is a feature.",
        ]
        summary_lines.append("")
        summary_lines.append(random.choice(workplace_lines))
        return "\n".join(summary_lines)
    except Exception as exc:
        print(f"Memo extraction failed: {exc}")
        return "Unable to load yesterday's memo.\n\nStability is a feature."


def get_yesterday_date_str() -> str:
    return (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")


# Ensure state files exist.
if not os.path.exists(STATE_FILE):
    save_main_state(dict(DEFAULT_MAIN_STATE))
if not os.path.exists(AGENTS_STATE_FILE):
    save_agents_state(list(DEFAULT_AGENTS))
if not os.path.exists(JOIN_KEYS_FILE):
    save_join_keys({"keys": []})


@app.after_request
def add_no_cache_headers(response):
    """Disable caching so dashboards always show current state."""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response


@app.route("/", methods=["GET"])
def index():
    with open(os.path.join(FRONTEND_DIR, "index.html"), "r", encoding="utf-8") as handle:
        html = handle.read()
    html = html.replace("{{VERSION_TIMESTAMP}}", VERSION_TIMESTAMP)
    response = make_response(html)
    response.headers["Content-Type"] = "text/html; charset=utf-8"
    return response


@app.route("/join", methods=["GET"])
def join_page():
    with open(os.path.join(FRONTEND_DIR, "join.html"), "r", encoding="utf-8") as handle:
        html = handle.read()
    response = make_response(html)
    response.headers["Content-Type"] = "text/html; charset=utf-8"
    return response


@app.route("/invite", methods=["GET"])
def invite_page():
    with open(os.path.join(FRONTEND_DIR, "invite.html"), "r", encoding="utf-8") as handle:
        html = handle.read()
    response = make_response(html)
    response.headers["Content-Type"] = "text/html; charset=utf-8"
    return response


@app.route("/agents", methods=["GET"])
def get_agents():
    """Return agents list and opportunistically clean stale records."""
    agents = load_agents_state()
    keys_payload = load_join_keys()
    now = datetime.now()

    cleaned_agents: list[dict[str, Any]] = []
    for agent in agents:
        if agent.get("isMain"):
            cleaned_agents.append(agent)
            continue

        auth_status = agent.get("authStatus", "pending")
        auth_expires = _parse_iso(agent.get("authExpiresAt"))

        # Expired pending requests are dropped and their key reservation is released.
        if auth_status == "pending" and auth_expires and now > auth_expires:
            join_key = agent.get("joinKey")
            if join_key:
                key_item = next((item for item in keys_payload.get("keys", []) if item.get("key") == join_key), None)
                if key_item:
                    key_item["used"] = False
                    key_item["usedBy"] = None
                    key_item["usedByAgentId"] = None
                    key_item["usedAt"] = None
            continue

        # Agents with stale pushes are marked offline.
        if auth_status == "approved":
            age = _seconds_since(agent.get("lastPushAt"), now)
            if age is None:
                age = _seconds_since(agent.get("updated_at"), now)
            if age is not None and age > 300:
                agent["authStatus"] = "offline"

        cleaned_agents.append(agent)

    save_agents_state(cleaned_agents)
    save_join_keys(keys_payload)
    return jsonify(cleaned_agents)


@app.route("/agents/approve", methods=["POST"])
def approve_agent():
    try:
        data = request.get_json()
        agent_id = (data.get("agentId") or "").strip() if isinstance(data, dict) else ""
        if not agent_id:
            return jsonify({"ok": False, "msg": "Missing agentId."}), 400

        agents = load_agents_state()
        target = next((item for item in agents if item.get("agentId") == agent_id and not item.get("isMain")), None)
        if not target:
            return jsonify({"ok": False, "msg": "Agent not found."}), 404

        target["authStatus"] = "approved"
        target["authApprovedAt"] = datetime.now().isoformat()
        target["authExpiresAt"] = (datetime.now() + timedelta(hours=24)).isoformat()
        save_agents_state(agents)
        return jsonify({"ok": True, "agentId": agent_id, "authStatus": "approved"})
    except Exception as exc:
        return jsonify({"ok": False, "msg": str(exc)}), 500


@app.route("/agents/reject", methods=["POST"])
def reject_agent():
    try:
        data = request.get_json()
        agent_id = (data.get("agentId") or "").strip() if isinstance(data, dict) else ""
        if not agent_id:
            return jsonify({"ok": False, "msg": "Missing agentId."}), 400

        agents = load_agents_state()
        target = next((item for item in agents if item.get("agentId") == agent_id and not item.get("isMain")), None)
        if not target:
            return jsonify({"ok": False, "msg": "Agent not found."}), 404

        target["authStatus"] = "rejected"
        target["authRejectedAt"] = datetime.now().isoformat()

        join_key = target.get("joinKey")
        keys_payload = load_join_keys()
        if join_key:
            key_item = next((item for item in keys_payload.get("keys", []) if item.get("key") == join_key), None)
            if key_item:
                key_item["used"] = False
                key_item["usedBy"] = None
                key_item["usedByAgentId"] = None
                key_item["usedAt"] = None

        remaining = [item for item in agents if item.get("agentId") != agent_id or item.get("isMain")]
        save_agents_state(remaining)
        save_join_keys(keys_payload)
        return jsonify({"ok": True, "agentId": agent_id, "authStatus": "rejected"})
    except Exception as exc:
        return jsonify({"ok": False, "msg": str(exc)}), 500


@app.route("/agents/join", methods=["POST"])
def join_agent():
    """Join an agent with key-based concurrency limits."""
    try:
        data = request.get_json()
        if not isinstance(data, dict) or not data.get("name"):
            return jsonify({"ok": False, "msg": "Please provide a name."}), 400

        name = data["name"].strip()
        state = normalize_state(data.get("state", "standby"))
        detail = (data.get("detail") or "").strip()
        join_key = (data.get("joinKey") or "").strip()

        if not join_key:
            return jsonify({"ok": False, "msg": "Please provide a join key."}), 400

        keys_payload = load_join_keys()
        key_item = next((item for item in keys_payload.get("keys", []) if item.get("key") == join_key), None)
        if not key_item:
            return jsonify({"ok": False, "msg": "Invalid join key."}), 403

        with join_lock:
            keys_payload = load_join_keys()
            key_item = next((item for item in keys_payload.get("keys", []) if item.get("key") == join_key), None)
            if not key_item:
                return jsonify({"ok": False, "msg": "Invalid join key."}), 403

            agents = load_agents_state()
            now = datetime.now()

            existing = next((item for item in agents if item.get("name") == name and not item.get("isMain")), None)
            existing_id = existing.get("agentId") if existing else None

            # Mark stale approved agents offline before counting active sessions.
            for item in agents:
                if item.get("isMain"):
                    continue
                if item.get("authStatus") != "approved":
                    continue
                age = _seconds_since(item.get("lastPushAt"), now)
                if age is None:
                    age = _seconds_since(item.get("updated_at"), now)
                if age is not None and age > 300:
                    item["authStatus"] = "offline"

            max_concurrent = int(key_item.get("maxConcurrent", 3))
            active_count = 0
            for item in agents:
                if item.get("isMain"):
                    continue
                if item.get("agentId") == existing_id:
                    continue
                if item.get("joinKey") != join_key:
                    continue
                if item.get("authStatus") != "approved":
                    continue
                age = _seconds_since(item.get("lastPushAt"), now)
                if age is None:
                    age = _seconds_since(item.get("updated_at"), now)
                if age is None or age <= 300:
                    active_count += 1

            if active_count >= max_concurrent:
                save_agents_state(agents)
                return jsonify({
                    "ok": False,
                    "msg": f"This join key is at its concurrent limit ({max_concurrent}). Try again later or use another key.",
                }), 429

            if existing:
                agent_id = existing.get("agentId")
                existing["state"] = state
                existing["detail"] = detail
                existing["updated_at"] = now.isoformat()
                existing["area"] = AREA_BY_STATE.get(state, "lounge")
                existing["source"] = "remote-openclaw"
                existing["joinKey"] = join_key
                existing["authStatus"] = "approved"
                existing["authApprovedAt"] = now.isoformat()
                existing["authExpiresAt"] = (now + timedelta(hours=24)).isoformat()
                existing["lastPushAt"] = now.isoformat()
                if not existing.get("avatar"):
                    existing["avatar"] = random.choice([
                        "guest_role_1",
                        "guest_role_2",
                        "guest_role_3",
                        "guest_role_4",
                        "guest_role_5",
                        "guest_role_6",
                    ])
            else:
                agent_id = "agent_" + str(int(now.timestamp() * 1000)) + "_" + "".join(
                    random.choices(string.ascii_lowercase + string.digits, k=4)
                )
                agents.append({
                    "agentId": agent_id,
                    "name": name,
                    "isMain": False,
                    "state": state,
                    "detail": detail,
                    "updated_at": now.isoformat(),
                    "area": AREA_BY_STATE.get(state, "lounge"),
                    "source": "remote-openclaw",
                    "joinKey": join_key,
                    "authStatus": "approved",
                    "authApprovedAt": now.isoformat(),
                    "authExpiresAt": (now + timedelta(hours=24)).isoformat(),
                    "lastPushAt": now.isoformat(),
                    "avatar": random.choice([
                        "guest_role_1",
                        "guest_role_2",
                        "guest_role_3",
                        "guest_role_4",
                        "guest_role_5",
                        "guest_role_6",
                    ]),
                })

            key_item["used"] = True
            key_item["usedBy"] = name
            key_item["usedByAgentId"] = agent_id
            key_item["usedAt"] = now.isoformat()
            key_item["reusable"] = True

            save_agents_state(agents)
            save_join_keys(keys_payload)

        return jsonify({
            "ok": True,
            "agentId": agent_id,
            "authStatus": "approved",
            "nextStep": "Approved automatically. Start pushing state updates now.",
        })
    except Exception as exc:
        return jsonify({"ok": False, "msg": str(exc)}), 500


@app.route("/agents/leave", methods=["POST"])
def leave_agent():
    """Remove an agent and release its join key usage record."""
    try:
        data = request.get_json()
        if not isinstance(data, dict):
            return jsonify({"ok": False, "msg": "Invalid JSON payload."}), 400

        agent_id = (data.get("agentId") or "").strip()
        name = (data.get("name") or "").strip()
        if not agent_id and not name:
            return jsonify({"ok": False, "msg": "Please provide agentId or name."}), 400

        agents = load_agents_state()
        target = None
        if agent_id:
            target = next((item for item in agents if item.get("agentId") == agent_id and not item.get("isMain")), None)
        if (not target) and name:
            target = next((item for item in agents if item.get("name") == name and not item.get("isMain")), None)

        if not target:
            return jsonify({"ok": False, "msg": "Agent not found."}), 404

        join_key = target.get("joinKey")
        remaining = [item for item in agents if item.get("isMain") or item.get("agentId") != target.get("agentId")]

        keys_payload = load_join_keys()
        if join_key:
            key_item = next((item for item in keys_payload.get("keys", []) if item.get("key") == join_key), None)
            if key_item:
                key_item["used"] = False
                key_item["usedBy"] = None
                key_item["usedByAgentId"] = None
                key_item["usedAt"] = None

        save_agents_state(remaining)
        save_join_keys(keys_payload)
        return jsonify({"ok": True})
    except Exception as exc:
        return jsonify({"ok": False, "msg": str(exc)}), 500


@app.route("/state", methods=["GET"])
def get_state():
    return jsonify(load_main_state())


@app.route("/agents/push", methods=["POST"])
def push_agent_state():
    """Receive state updates from remote OpenClaw agents."""
    try:
        data = request.get_json()
        if not isinstance(data, dict):
            return jsonify({"ok": False, "msg": "Invalid JSON payload."}), 400

        agent_id = (data.get("agentId") or "").strip()
        join_key = (data.get("joinKey") or "").strip()
        state = normalize_state(data.get("state"))
        detail = (data.get("detail") or "").strip()
        name = (data.get("name") or "").strip()

        if not agent_id or not join_key or not data.get("state"):
            return jsonify({"ok": False, "msg": "Missing required fields: agentId, joinKey, state."}), 400

        keys_payload = load_join_keys()
        key_item = next((item for item in keys_payload.get("keys", []) if item.get("key") == join_key), None)
        if not key_item:
            return jsonify({"ok": False, "msg": "Invalid joinKey."}), 403

        agents = load_agents_state()
        target = next((item for item in agents if item.get("agentId") == agent_id and not item.get("isMain")), None)
        if not target:
            return jsonify({"ok": False, "msg": "Agent is not registered. Join first."}), 404

        auth_status = target.get("authStatus", "pending")
        if auth_status not in {"approved", "offline"}:
            return jsonify({"ok": False, "msg": "Agent is not approved."}), 403

        if auth_status == "offline":
            target["authStatus"] = "approved"
            target["authApprovedAt"] = datetime.now().isoformat()
            target["authExpiresAt"] = (datetime.now() + timedelta(hours=24)).isoformat()

        if target.get("joinKey") != join_key:
            return jsonify({"ok": False, "msg": "joinKey mismatch."}), 403

        target["state"] = state
        target["detail"] = detail
        if name:
            target["name"] = name
        target["updated_at"] = datetime.now().isoformat()
        target["area"] = AREA_BY_STATE.get(state, "lounge")
        target["source"] = "remote-openclaw"
        target["lastPushAt"] = datetime.now().isoformat()

        save_agents_state(agents)
        return jsonify({"ok": True, "agentId": agent_id, "area": target.get("area")})
    except Exception as exc:
        return jsonify({"ok": False, "msg": str(exc)}), 500


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "timestamp": datetime.now().isoformat()})


@app.route("/memo/yesterday", methods=["GET"])
def get_yesterday_memo():
    """Return yesterday's memo or nearest available historical memo."""
    try:
        yesterday = get_yesterday_date_str()
        target_file = os.path.join(MEMORY_DIR, f"{yesterday}.md")
        target_date = yesterday

        if not os.path.exists(target_file) and os.path.exists(MEMORY_DIR):
            files = [
                name
                for name in os.listdir(MEMORY_DIR)
                if name.endswith(".md") and re.match(r"\d{4}-\d{2}-\d{2}\.md", name)
            ]
            if files:
                files.sort(reverse=True)
                today = datetime.now().strftime("%Y-%m-%d")
                for name in files:
                    if name != f"{today}.md":
                        target_file = os.path.join(MEMORY_DIR, name)
                        target_date = name.replace(".md", "")
                        break

        if target_file and os.path.exists(target_file):
            memo_text = extract_memo_from_file(target_file)
            return jsonify({"success": True, "date": target_date, "memo": memo_text})

        return jsonify({"success": False, "msg": "No memo found for yesterday."})
    except Exception as exc:
        return jsonify({"success": False, "msg": str(exc)}), 500


@app.route("/state", methods=["POST"])
def set_state():
    """Update the main dashboard state from the control panel."""
    try:
        data = request.get_json()
        if not isinstance(data, dict):
            return jsonify({"status": "error", "msg": "Invalid JSON payload."}), 400

        state = load_main_state()
        if "state" in data:
            state["state"] = normalize_state(data["state"])
        if "detail" in data:
            state["detail"] = str(data["detail"])
        state["updated_at"] = datetime.now().isoformat()

        save_main_state(state)
        return jsonify({"status": "ok"})
    except Exception as exc:
        return jsonify({"status": "error", "msg": str(exc)}), 500


if __name__ == "__main__":
    print("=" * 60)
    print("Star Office UI Backend Service")
    print("=" * 60)
    print(f"State file: {STATE_FILE}")
    print("Listening on: http://0.0.0.0:18791")
    print("=" * 60)
    app.run(host="0.0.0.0", port=18791, debug=False)
