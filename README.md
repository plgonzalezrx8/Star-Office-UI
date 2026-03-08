# Star Office UI

Star Office UI is a pixel-art collaboration dashboard that visualizes OpenClaw/lobster agent activity in real time. Teams can quickly see who is online, what state each agent is in, and a short memo from previous work.

![Star Office UI Preview](docs/screenshots/office-preview-20260301.jpg)

## Quick Start (60 seconds)

```bash
git clone https://github.com/ringhyacinth/Star-Office-UI.git
cd Star-Office-UI
python3 -m pip install -r backend/requirements.txt
cp state.sample.json state.json
cd backend
python3 app.py
```

Open `http://127.0.0.1:18791`.

From repo root, test state changes:

```bash
python3 set_state.py working "Drafting implementation notes"
python3 set_state.py sync "Syncing dashboard data"
python3 set_state.py incident "Investigating a production issue"
python3 set_state.py standby "Ready for the next task"
```

## What It Does

1. Visualizes OpenClaw/lobster agent states in a live office scene.
2. Supports multiple guest agents with join keys and periodic state pushes.
3. Shows a "Yesterday Summary" memo card from `memory/YYYY-MM-DD.md`.
4. Works on desktop and mobile browsers.
5. Supports public sharing via any tunnel/reverse-proxy setup.

## Canonical Contract (Hard Cut)

### States

- `standby`
- `working`
- `research`
- `running`
- `sync`
- `incident`

### Areas

- `lounge`
- `workzone`
- `incident_bay`

### API Routes

- `GET /health`
- `GET /state`
- `POST /state`
- `GET /agents`
- `POST /agents/join`
- `POST /agents/push`
- `POST /agents/leave`
- `POST /agents/approve`
- `POST /agents/reject`
- `GET /memo/yesterday`

Legacy routes are intentionally removed.

For legacy integrations, use [Migration Guide](docs/MIGRATION_GUIDE_US_LOCALIZATION.md) and run:

```bash
python3 migrate_contract_data.py
```

## Project Structure

```text
star-office-ui/
  backend/
    app.py
    requirements.txt
    run.sh
  frontend/
    index.html
    game.js
    layout.js
    join.html
    invite.html
    ...assets
  docs/
  office-agent-push.py
  set_state.py
  state.sample.json
  join-keys.json
  SKILL.md
  README.md
  LICENSE
```

## Art Assets and Licensing

### Code License

Code and logic are provided under MIT (see `LICENSE`).

### Art Asset Restrictions

All art assets in this repository are non-commercial. They are provided for learning, demos, and experimentation only. If you deploy commercially, replace all art assets with your own original work.

### Trademark/IP Notice

The main character references an existing Nintendo/Pokémon IP (Starmie) and is not original IP created by this project. Nintendo, Pokémon, and Starmie are trademarks or registered trademarks of their respective owners.

## Author Links

- Ring Hyacinth: https://x.com/ring_hyacinth
- Simon Lee: https://x.com/simonxxoo
