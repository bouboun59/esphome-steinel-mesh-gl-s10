#!/usr/bin/env bash
# Installe ou met a jour ESPHome dans ~/esphome-steinel (macOS / Linux).
# Install or update ESPHome in ~/esphome-steinel (macOS / Linux).
# Usage : scripts/install_esphome.sh [version]      (defaut / default: derniere version / latest)
set -euo pipefail
# shellcheck source=lib.sh
source "$(dirname "$0")/lib.sh"
VERSION="${1:-}"

case "$(uname -s)" in
  Darwin)
    command -v brew >/dev/null || { echo "Installez Homebrew / install Homebrew: https://brew.sh"; exit 1; }
    brew list python@3.13 >/dev/null 2>&1 || brew install python@3.13
    PY="$(brew --prefix python@3.13)/bin/python3.13"
    ;;
  Linux)
    if command -v apt-get >/dev/null; then
      sudo apt-get update
      sudo apt-get install -y python3 python3-venv python3-pip git
    fi
    PY=python3
    if ! id -nG "$USER" | grep -qw dialout; then
      echo "Port serie / serial port: sudo usermod -aG dialout $USER (puis se reconnecter / then log in again)"
    fi
    ;;
  *)
    echo "Systeme non gere / unsupported system: $(uname -s)"; exit 1 ;;
esac

"$PY" - <<'PY'
import sys
if sys.version_info[:2] < (3, 11):
    raise SystemExit(f"Python >= 3.11 requis / required, detecte / found {sys.version.split()[0]}")
PY

[[ -x "$VENV/bin/python" ]] || "$PY" -m venv "$VENV"
"$VENV/bin/python" -m pip install --upgrade pip wheel
if [[ -n "$VERSION" ]]; then SPEC="esphome==$VERSION"; else SPEC="esphome"; fi
"$VENV/bin/python" -m pip install --upgrade "$SPEC" || {
  echo "Echec / failed. Mac Intel + cbor2 : brew install rust, puis relancer / then run again."; exit 1; }
"$VENV/bin/esphome" version
echo "Activer l'environnement / activate: source $VENV/bin/activate"
echo "Gardez la meme version que ESPHome Device Builder / keep the same version as Device Builder."
