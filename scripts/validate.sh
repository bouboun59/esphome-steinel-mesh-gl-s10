#!/usr/bin/env bash
# Verifie le projet avant un commit / check the project before a commit:
#  - pages web embarquees a jour / embedded web pages up to date
#  - aucun fichier prive suivi par git / no private file tracked by git
#  - YAML local et YAML Device Builder valides / local and Device Builder YAML valid
set -euo pipefail
# shellcheck source=lib.sh
source "$(dirname "$0")/lib.sh"
ESPHOME_BIN="$(find_esphome)"
FAIL=0

echo "== Pages web embarquees / embedded web pages"
python3 "$ROOT_DIR/scripts/generate_pages.py" --check || FAIL=1

echo "== Fichiers prives / private files"
if git -C "$ROOT_DIR" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  BAD="$(git -C "$ROOT_DIR" ls-files | grep -E '(^|/)secrets\.yaml$|\.bin$|backup[^/]*\.json$' || true)"
  if [[ -n "$BAD" ]]; then
    echo "ERREUR : fichiers prives suivis par git / private files tracked:"; echo "$BAD"; FAIL=1
  else
    echo "OK"
  fi
fi

echo "== $CONFIG"
if (cd "$CONFIG_DIR" && "$ESPHOME_BIN" config "$CONFIG" >/dev/null); then echo "OK"; else
  echo "ERREUR : $CONFIG invalide (esphome/secrets.yaml present ?)"; FAIL=1; fi

echo "== device-builder/$CONFIG"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
cp "$CONFIG_DIR/device-builder/$CONFIG" "$TMP/"
printf 'ota_password: "validation-only"\napi_encryption_key: "%s"\n' "$(head -c 32 /dev/urandom | base64)" > "$TMP/secrets.yaml"
if (cd "$TMP" && "$ESPHOME_BIN" config "$CONFIG" >/dev/null); then echo "OK"; else
  echo "ERREUR : YAML Device Builder invalide / invalid"; FAIL=1; fi

[[ $FAIL -eq 0 ]] && echo "Tout est bon / all good." || echo "Des erreurs sont a corriger / errors to fix."
exit $FAIL
