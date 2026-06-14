#!/usr/bin/env bash
set -euo pipefail

VERSION="${BLENDER_VERSION:-4.0.2}"
MAJOR_MINOR="${VERSION%.*}"
ARCHIVE="blender-${VERSION}-linux-x64.tar.xz"
URL="https://download.blender.org/release/Blender${MAJOR_MINOR}/${ARCHIVE}"
INSTALL_ROOT="${LABCANVAS_BLENDER_HOME:-${APPAUTOACTION_BLENDER_HOME:-$HOME/.local/share/labcanvas/blender}}"
INSTALL_DIR="$INSTALL_ROOT/blender-${VERSION}-linux-x64"
DOWNLOAD="$INSTALL_ROOT/$ARCHIVE"

mkdir -p "$INSTALL_ROOT"

if [[ -x "$INSTALL_DIR/blender" ]]; then
  echo "$INSTALL_DIR/blender"
  exit 0
fi

if [[ ! -f "$DOWNLOAD" ]]; then
  curl -L "$URL" -o "$DOWNLOAD"
fi

tar -xJf "$DOWNLOAD" -C "$INSTALL_ROOT"
chmod +x "$INSTALL_DIR/blender"
echo "$INSTALL_DIR/blender"
