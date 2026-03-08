# Star Office UI — Overview

Star Office UI renders OpenClaw agent states as a live pixel-office dashboard viewable on desktop and mobile.

## What users see
- Pixel office background and animated scene
- Main agent + guest agents moving by state
- Status labels and bubble text
- Yesterday summary memo panel

## Core capabilities

### Main agent state rendering
- Backend reads `state.json` and serves `GET /state`
- Frontend polls `/state` and renders the canonical state
- `set_state.py` provides fast local state updates

### Multi-agent guest flow
- Guests join with `POST /agents/join`
- Guests push updates with `POST /agents/push`
- Frontend polls `GET /agents` for rendering

### Join key controls
- Reusable join keys (`ocj_starteam01` to `ocj_starteam08`)
- Per-key concurrency limits (`maxConcurrent`)
- Practical controls over who can enter and how many can be active

### Canonical mapping
- `standby -> lounge`
- `working/research/running/sync -> workzone`
- `incident -> incident_bay`

## Primary backend endpoints
- `GET /`
- `GET /state`
- `POST /state`
- `GET /agents`
- `POST /agents/join`
- `POST /agents/push`
- `POST /agents/leave`
- `POST /agents/approve`
- `POST /agents/reject`
- `GET /memo/yesterday`
- `GET /health`

## Privacy and security notes
- Do not put sensitive content in `detail` fields.
- Before open-source release, remove runtime logs and private operational files.

## Asset usage notice
- Code can be open-sourced under MIT.
- Art assets remain non-commercial unless replaced with original assets.
