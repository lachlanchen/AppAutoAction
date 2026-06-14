#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUTPUT_DIR="${LABCANVAS_OUTPUT_DIR:-${APPAUTOACTION_OUTPUT_DIR:-$ROOT_DIR/output/blender}}"
mkdir -p "$OUTPUT_DIR"

ENVELOPE_FILE="$(mktemp "${TMPDIR:-/tmp}/labcanvas-envelope.XXXXXX.json")"
RESULT_FILE="$(mktemp "${TMPDIR:-/tmp}/labcanvas-result.XXXXXX.json")"
LOG_FILE="$OUTPUT_DIR/blender-wrapper.log"
cat > "$ENVELOPE_FILE"

if [[ -n "${BLENDER_BIN:-}" ]]; then
  BLENDER="$BLENDER_BIN"
elif command -v blender >/dev/null 2>&1; then
  BLENDER="$(command -v blender)"
else
  PORTABLE="$HOME/.local/share/labcanvas/blender/blender-4.0.2-linux-x64/blender"
  LEGACY_PORTABLE="$HOME/.local/share/appautoaction/blender/blender-4.0.2-linux-x64/blender"
  if [[ -x "$PORTABLE" ]]; then
    BLENDER="$PORTABLE"
  else
    BLENDER="$LEGACY_PORTABLE"
  fi
fi

if [[ ! -x "$BLENDER" ]]; then
  python3 - "$BLENDER" "$ENVELOPE_FILE" <<'PY'
import json
import sys

print(json.dumps({
    "ok": False,
    "error": "Blender executable not found or not executable",
    "expected": sys.argv[1],
    "envelope_file": sys.argv[2],
}))
PY
  exit 127
fi

set +e
LABCANVAS_ENVELOPE_FILE="$ENVELOPE_FILE" \
LABCANVAS_RESULT_FILE="$RESULT_FILE" \
LABCANVAS_OUTPUT_DIR="$OUTPUT_DIR" \
APPAUTOACTION_ENVELOPE_FILE="$ENVELOPE_FILE" \
APPAUTOACTION_RESULT_FILE="$RESULT_FILE" \
APPAUTOACTION_OUTPUT_DIR="$OUTPUT_DIR" \
"$BLENDER" -b --python "$ROOT_DIR/bridges/blender_building_bridge.py" > "$LOG_FILE" 2>&1
STATUS=$?
set -e

if [[ -s "$RESULT_FILE" ]]; then
  cat "$RESULT_FILE"
else
  python3 - "$STATUS" "$LOG_FILE" <<'PY'
import json
import sys

print(json.dumps({
    "ok": False,
    "returncode": int(sys.argv[1]),
    "error": "Blender did not write a result file",
    "log_file": sys.argv[2],
}))
PY
fi

rm -f "$ENVELOPE_FILE" "$RESULT_FILE"
exit "$STATUS"
