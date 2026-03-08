# Join Star Lobster Office - Guest Agent Skill

## Description
Connect your OpenClaw agent to Star Lobster Office so your owner can see your live status on the dashboard.

## Prerequisites
- You received a join key from the office owner (`ocj_xxx` format)
- Your owner approved status syncing
- You can access `https://office.example.com`

## Steps
1. Request owner authorization:
   > "I will send my state metadata (`standby/working/research/running/sync/incident`) to the Star Lobster Office dashboard for collaboration visibility. No private content is required. You can stop this anytime. Approve?"

2. After approval:
   - Set `AGENT_NAME` to your display name
   - Set `JOIN_KEY` to the provided key
   - Download `office-agent-push.py` from:
     `https://office.example.com/static/office-agent-push.py`
   - Run the script directly (it auto-discovers local state files)
   - Optional override if needed:
     - `OFFICE_LOCAL_STATE_FILE=/path/to/state.json`
   - Optional tokenized local state API mode:
     - `OFFICE_LOCAL_STATUS_TOKEN=<token>`
     - `OFFICE_LOCAL_STATUS_URL=http://127.0.0.1:18791/state`

3. Script behavior:
   - Calls `POST /agents/join` once
   - Reads local state and normalizes to canonical states
   - Pushes updates via `POST /agents/push` every 15 seconds
   - Stops automatically if removed/denied (`403`/`404`)

4. Stop syncing:
   - Press `Ctrl+C` in the script process

## Notes
- Only short state metadata should be sent
- Default approval validity is 24h
- If you receive repeated `403`/`404`, contact your owner
