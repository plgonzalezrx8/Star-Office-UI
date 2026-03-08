# Star Office UI — Feature Additions (Current Phase)

## 1) Multi-guest agent support
- Multiple remote OpenClaw agents can join one office.
- Each guest has independent identity, name, state, area, and bubble copy.
- Join/leave updates render in near real time.

## 2) Join key model update
- Moved from one-time keys to reusable keys.
- Default keys: `ocj_starteam01` to `ocj_starteam08`.
- Per-key online concurrency limit remains configurable (`maxConcurrent`, default `3`).

## 3) Concurrency race fix
- Fixed race conditions in join flow.
- The 4th simultaneous join now correctly returns `HTTP 429` when limit is `3`.

## 4) Canonical state-to-area mapping
- `standby -> lounge`
- `working/research/running/sync -> workzone`
- `incident -> incident_bay`

## 5) Guest animation optimization
- Guests render as animated sprites instead of static icons.
- WebP variants reduce asset size and load time.

## 6) Name and bubble clarity improvements
- Guest name/bubble positioning avoids overlap.
- Bubble anchoring now remains visually stable above labels.

## 7) Mobile display support
- Dashboard is directly viewable on mobile browsers.
- Responsive layout pass improves presentation for demos.

## 8) Remote push script improvements
- Agent push script can read from local state files.
- Source diagnostics improved for easier troubleshooting.
- Environment-variable overrides are resolved consistently.
