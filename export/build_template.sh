#!/usr/bin/env bash
# Сборка лёгкого web-шаблона экспорта. Нужны: git, python3 + scons, Emscripten (emsdk) нужной для Godot версии.
# Использование:  GODOT_SRC=~/src/godot ./export/build_template.sh
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
GODOT_SRC="${GODOT_SRC:-$HOME/src/godot}"
GODOT_TAG="${GODOT_TAG:-4.7-stable}"
if [ ! -d "$GODOT_SRC" ]; then
  git clone --depth 1 --branch "$GODOT_TAG" https://github.com/godotengine/godot.git "$GODOT_SRC"
fi
command -v emcc >/dev/null || { echo "Нет emcc: выполни 'source <emsdk>/emsdk_env.sh'"; exit 1; }
EXTRA=()
if [ -f "$HERE/chalk.gdbuild" ]; then EXTRA+=("build_profile=$HERE/chalk.gdbuild"); fi
cd "$GODOT_SRC"
scons profile="$HERE/custom.py" "${EXTRA[@]}" -j"$(nproc 2>/dev/null || sysctl -n hw.ncpu)"
OUT="$(ls -t bin/godot.web.template_release*.zip | head -1)"
mkdir -p "$HERE/templates"
cp "$OUT" "$HERE/templates/web_release_slim.zip"
echo "Готово: export/templates/web_release_slim.zip"
ls -lh "$HERE/templates/web_release_slim.zip"
