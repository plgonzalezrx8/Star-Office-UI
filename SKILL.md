---
name: star-office-ui
description: One-click style skill for launching a pixel office dashboard with multi-agent OpenClaw state visualization, mobile-friendly UI, and public sharing support.
---

# Star Office UI Skill

Use this skill to help a user bring up Star Office UI quickly with minimal friction.

## 1) What this is

Star Office UI is a multi-agent pixel office dashboard. OpenClaw/lobster agents appear in different office areas based on their state.

## 2) Quick launch

```bash
git clone https://github.com/ringhyacinth/Star-Office-UI.git
cd Star-Office-UI
python3 -m pip install -r backend/requirements.txt
cp state.sample.json state.json
cd backend
python3 app.py
```

Tell the user to open `http://127.0.0.1:18791`.

## 3) Demo state transitions

```bash
python3 set_state.py working "Drafting docs"
python3 set_state.py sync "Syncing progress"
python3 set_state.py incident "Investigating failure"
python3 set_state.py standby "Standing by"
```

## 4) Public access option

If `cloudflared` is available:

```bash
cloudflared tunnel --url http://127.0.0.1:18791
```

Share the generated `https://*.trycloudflare.com` URL.

## 5) Invite guest agents (optional)

Guest agents can use `office-agent-push.py` with:

- `POST /agents/join`
- `POST /agents/push`
- `POST /agents/leave`

Default join keys are in `join-keys.json`.

## 6) Contract reference

States:
- `standby`, `working`, `research`, `running`, `sync`, `incident`

Routes:
- `GET /state`, `POST /state`, `GET /agents`
- `POST /agents/join`, `POST /agents/push`, `POST /agents/leave`
- `POST /agents/approve`, `POST /agents/reject`, `GET /memo/yesterday`

## 7) Legal reminder

Code is MIT. Art assets are non-commercial only. Keep the trademark/IP notice in README and LICENSE.
