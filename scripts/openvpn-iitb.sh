#!/usr/bin/env bash
set -euo pipefail

CONFIG="$HOME/.config/openvpn/iitb-cli.ovpn"
AUTH_FILE="$HOME/.config/openvpn/iitb.auth"

if [[ ! -f "$CONFIG" || ! -f "$AUTH_FILE" ]]; then
  echo "Missing runtime config or auth file. Run scripts/setup-openvpn-iitb-cli.sh first." >&2
  exit 1
fi

if grep -Eq 'REPLACE_WITH_(LDAP_USERNAME|VPN_PASSWORD)' "$AUTH_FILE"; then
  echo "Auth file still contains placeholder values: $AUTH_FILE" >&2
  exit 1
fi

exec sudo openvpn --config "$CONFIG"
