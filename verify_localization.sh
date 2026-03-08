#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

echo "[1/4] Checking for Chinese characters in tracked text..."
if rg -n --pcre2 "\p{Han}" . \
  --glob '!**/*.png' \
  --glob '!**/*.jpg' \
  --glob '!**/*.webp' \
  --glob '!**/*.gif' \
  --glob '!**/*.woff2' \
  --glob '!**/*.zip' >/tmp/localization_han_check.txt; then
  cat /tmp/localization_han_check.txt
  echo "Found non-English Han characters."
  exit 1
fi

echo "[2/4] Checking for legacy routes outside manifest..."
if rg -n "(/status|/set_state|/join-agent|/agent-push|/leave-agent|/agent-approve|/agent-reject|/yesterday-memo)" . \
  --glob '!docs/LOCALIZATION_RENAME_MANIFEST.md' \
  --glob '!docs/MIGRATION_GUIDE_US_LOCALIZATION.md' \
  --glob '!verify_localization.sh' >/tmp/localization_route_check.txt; then
  cat /tmp/localization_route_check.txt
  echo "Found legacy routes outside manifest."
  exit 1
fi

echo "[3/4] Validating Python syntax..."
python3 -m compileall backend migrate_contract_data.py office-agent-push.py set_state.py convert_to_webp.py >/tmp/localization_compile.log

echo "[4/4] Quick static asset reference check..."
for token in \
  "ark-pixel-12px-proportional-latin.ttf.woff2" \
  "desk-v2.png" \
  "office_bg_small" \
  "star-working-spritesheet-grid"; do
  if ! rg -n "$token" frontend >/dev/null; then
    echo "Expected frontend reference missing: $token"
    exit 1
  fi
done

echo "Localization verification passed."
