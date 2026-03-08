# Star Office UI — Open Source Release Checklist (Prep Only)

## 0) Goal
- This checklist is for release preparation only.
- Do not push publicly until final owner approval.

## 1) Privacy and safety scan

### Exclude high-risk runtime files
- Logs (`*.log`, `*.out`)
- Runtime state (`state.json`, `agents-state.json`)
- PID/runtime markers (`*.pid`)
- Backup files (`*.backup*`, `*.original`)
- Local virtual environments (`.venv/`, `venv/`)
- Python cache (`__pycache__/`)

### Review potential sensitive content
- Remove machine-specific absolute paths when possible.
- Keep sample domain names as placeholders only.

## 2) Required pre-release edits

### `.gitignore`
Add or verify:

```gitignore
*.log
*.out
*.pid
state.json
agents-state.json
join-keys.json
*.backup*
*.original
__pycache__/
.venv/
venv/
```

### README and LICENSE
- Ensure legal/IP notice remains in US legal English.
- Ensure non-commercial art asset restriction is explicit.

### Package cleanup
- Remove runtime and debug leftovers.
- Keep only runnable source, required assets, and docs.

## 3) Suggested release structure

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
    assets/*
  office-agent-push.py
  set_state.py
  state.sample.json
  README.md
  LICENSE
  SKILL.md
  docs/
```

## 4) Final owner confirmation
- [ ] Placeholder domain usage is acceptable
- [ ] Public asset scope is approved
- [ ] README legal wording is approved
- [ ] Script examples match current API contract

## 5) Current status
- Documentation is prepared for US-localized hard-cut contract.
- Waiting for final approval on public asset scope and release timing.
