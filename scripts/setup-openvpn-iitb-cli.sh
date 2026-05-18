#!/usr/bin/env bash
set -euo pipefail

SOURCE_CONFIG="${1:-$HOME/Downloads/BigSur-IITBVPN.ovpn}"
CONFIG_DIR="$HOME/.config/openvpn"
RUNTIME_CONFIG="$CONFIG_DIR/iitb-cli.ovpn"
AUTH_FILE="$CONFIG_DIR/iitb.auth"

if [[ ! -f "$SOURCE_CONFIG" ]]; then
  echo "OpenVPN profile not found: $SOURCE_CONFIG" >&2
  exit 1
fi

mkdir -p "$CONFIG_DIR"
chmod 700 "$CONFIG_DIR"

awk -v auth_file="$AUTH_FILE" '
  /^auth-user-pass([[:space:]]|$)/ {
    print "auth-user-pass " auth_file
    next
  }
  { print }
' "$SOURCE_CONFIG" > "$RUNTIME_CONFIG"

if ! grep -q '^auth-nocache' "$RUNTIME_CONFIG"; then
  printf '\nauth-nocache\n' >> "$RUNTIME_CONFIG"
fi

chmod 600 "$RUNTIME_CONFIG"

if [[ ! -f "$AUTH_FILE" ]]; then
  cat > "$AUTH_FILE" <<'EOF'
REPLACE_WITH_LDAP_USERNAME
REPLACE_WITH_VPN_PASSWORD
EOF
fi

chmod 600 "$AUTH_FILE"

echo "Created runtime config: $RUNTIME_CONFIG"
echo "Created auth file:      $AUTH_FILE"
echo
echo "Edit $AUTH_FILE and replace both placeholders with your IITB LDAP/VPN username and password."
