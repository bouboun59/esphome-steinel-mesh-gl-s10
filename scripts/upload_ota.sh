#!/usr/bin/env bash
# Compile et installe le firmware par le reseau / compile and install over the network.
# Usage : scripts/upload_ota.sh <ip|hote> [--web]
#   par defaut / default : OTA ESPHome (ota_password de / from secrets.yaml)
#   --web                : par la page web de la passerelle / through the gateway web page (/update, admin)
set -euo pipefail
# shellcheck source=lib.sh
source "$(dirname "$0")/lib.sh"
[[ $# -ge 1 ]] || { echo "Usage : $0 <ip|hote> [--web]"; exit 1; }
TARGET="$1"
MODE="${2:-}"
ESPHOME_BIN="$(find_esphome)"
cd "$CONFIG_DIR"

if [[ "$MODE" != "--web" ]]; then
  exec "$ESPHOME_BIN" run "$CONFIG" --device "$TARGET" --no-logs
fi

"$ESPHOME_BIN" compile "$CONFIG"
FIRMWARE="$(find .esphome/build -type f -name firmware.ota.bin -print -quit)"
[[ -n "$FIRMWARE" && -f "$FIRMWARE" ]] || { echo "firmware.ota.bin introuvable / not found"; exit 1; }
TARGET="${TARGET#http://}"
BASE_URL="http://${TARGET%/}"
echo "curl va demander le mot de passe admin / curl will ask for the admin password:"
curl --fail --show-error --digest --user admin \
  --form "update=@${FIRMWARE};type=application/octet-stream" "$BASE_URL/update"
echo
echo "Firmware envoye, la passerelle redemarre / firmware sent, the gateway restarts."
