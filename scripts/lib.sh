#!/usr/bin/env bash
# Fonctions communes aux scripts / shared helpers for the scripts
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CONFIG_DIR="$ROOT_DIR/esphome"
CONFIG="gl-s10-steinel.yaml"
VENV="${ESPHOME_VENV:-$HOME/esphome-steinel}"

# Trouve ESPHome : variable ESPHOME, environnement ~/esphome-steinel, puis PATH
find_esphome() {
  local candidate
  for candidate in "${ESPHOME:-}" "$VENV/bin/esphome" "$(command -v esphome 2>/dev/null || true)"; do
    if [[ -n "$candidate" && -x "$candidate" ]]; then
      printf '%s\n' "$candidate"
      return 0
    fi
  done
  echo "ERREUR / ERROR: ESPHome introuvable / not found. Lancez / run: scripts/install_esphome.sh" >&2
  return 1
}

# Python de l'environnement ESPHome (fournit esptool)
find_python() {
  local esphome_bin python_bin
  esphome_bin="$(find_esphome)" || return 1
  python_bin="$(dirname "$esphome_bin")/python"
  if [[ -x "$python_bin" ]]; then printf '%s\n' "$python_bin"; else command -v python3; fi
}
