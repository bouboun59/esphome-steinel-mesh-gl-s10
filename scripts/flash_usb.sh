#!/usr/bin/env bash
# Premier flash ou recuperation par cable serie (adaptateur USB-TTL 3,3 V).
# First flash or recovery over serial (3.3 V USB-TTL adapter).
# Usage : scripts/flash_usb.sh <port>   ex. /dev/cu.usbserial-14140 (macOS), /dev/ttyUSB0 (Linux)
# Mode flash : bouton pres du connecteur 9 trous maintenu a la mise sous tension.
# Flash mode: hold the button next to the 9-hole header while powering the GL-S10.
set -euo pipefail
# shellcheck source=lib.sh
source "$(dirname "$0")/lib.sh"
if [[ $# -ne 1 ]]; then
  echo "Usage : $0 <port>"
  ls /dev/cu.usb* /dev/cu.wchusb* /dev/ttyUSB* 2>/dev/null || true
  exit 1
fi
PORT="$1"
[[ -e "$PORT" ]] || { echo "Port introuvable / not found: $PORT"; exit 1; }
ESPHOME_BIN="$(find_esphome)"
PY="$(find_python)"
cd "$CONFIG_DIR"
"$ESPHOME_BIN" compile "$CONFIG"
FACTORY="$(find .esphome/build -type f -name firmware.factory.bin -print -quit)"
[[ -n "$FACTORY" && -f "$FACTORY" ]] || { echo "firmware.factory.bin introuvable / not found"; exit 1; }
"$PY" -m esptool --port "$PORT" --baud 115200 --before no-reset --after no-reset --chip esp32 \
  write-flash -z 0x0 "$FACTORY"
echo "Termine : debranchez puis rebranchez l'alimentation SANS le bouton."
echo "Done: unplug and replug the power WITHOUT the button."
