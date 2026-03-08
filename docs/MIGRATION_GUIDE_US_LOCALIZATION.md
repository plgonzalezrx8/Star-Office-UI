# Contract Migration Guide: Legacy -> US Canonical

This release is a hard cut. Legacy routes are removed and canonical routes are required.

## Route migration

| Legacy | Canonical |
|---|---|
| `GET /status` | `GET /state` |
| `POST /set_state` | `POST /state` |
| `POST /join-agent` | `POST /agents/join` |
| `POST /agent-push` | `POST /agents/push` |
| `POST /leave-agent` | `POST /agents/leave` |
| `POST /agent-approve` | `POST /agents/approve` |
| `POST /agent-reject` | `POST /agents/reject` |
| `GET /yesterday-memo` | `GET /memo/yesterday` |

## State migration

| Legacy | Canonical |
|---|---|
| `idle` | `standby` |
| `writing` | `working` |
| `researching` | `research` |
| `executing` | `running` |
| `syncing` | `sync` |
| `error` | `incident` |

## Area migration

| Legacy | Canonical |
|---|---|
| `breakroom` | `lounge` |
| `writing` | `workzone` |
| `error` | `incident_bay` |

## Persisted data migration

Run:

```bash
python3 migrate_contract_data.py
```

This rewrites local `state.json` and `agents-state.json` into canonical values.
