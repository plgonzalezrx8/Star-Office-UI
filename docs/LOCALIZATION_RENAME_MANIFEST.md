# US Localization Rename Manifest

This manifest records the hard-cut naming and contract migration applied in this repository.

## Route mapping

- `GET /status` -> `GET /state`
- `POST /set_state` -> `POST /state`
- `POST /join-agent` -> `POST /agents/join`
- `POST /agent-push` -> `POST /agents/push`
- `POST /leave-agent` -> `POST /agents/leave`
- `POST /agent-approve` -> `POST /agents/approve`
- `POST /agent-reject` -> `POST /agents/reject`
- `GET /yesterday-memo` -> `GET /memo/yesterday`

## State enum mapping

- `idle` -> `standby`
- `writing` -> `working`
- `researching` -> `research`
- `executing` -> `running`
- `syncing` -> `sync`
- `error` -> `incident`

## Area enum mapping

- `breakroom` -> `lounge`
- `writing` -> `workzone`
- `error` -> `incident_bay`

## Filename mapping

### Font assets

- `ark-pixel-12px-proportional-zh_cn.ttf.woff2` -> `ark-pixel-12px-proportional-chinese-simplified.ttf.woff2`
- `ark-pixel-12px-proportional-zh_tw.ttf.woff2` -> `ark-pixel-12px-proportional-chinese-traditional-tw.ttf.woff2`
- `ark-pixel-12px-proportional-zh_hk.ttf.woff2` -> `ark-pixel-12px-proportional-chinese-traditional-hk.ttf.woff2`
- `ark-pixel-12px-proportional-zh_tr.ttf.woff2` -> `ark-pixel-12px-proportional-chinese-traditional-alt.ttf.woff2`
- `ark-pixel-12px-proportional-ja.ttf.woff2` -> `ark-pixel-12px-proportional-japanese.ttf.woff2`
- `ark-pixel-12px-proportional-ko.ttf.woff2` -> `ark-pixel-12px-proportional-korean.ttf.woff2`

## Terminology glossary

- "Yesterday Memo" -> "Yesterday Summary"
- "Bug area" -> "Incident Bay"
- "Breakroom" -> "Lounge"
- "Writing area" -> "Workzone"
- "Join key" remains unchanged
- "OpenClaw/lobster" remains unchanged by product decision
