#!/usr/bin/env bash
set -euo pipefail

CONFIG="$HOME/.config/openvpn/iitb-cli.ovpn"
AUTH_FILE="$HOME/.config/openvpn/iitb.auth"
PLIST="/Library/LaunchDaemons/local.openvpn.iitb.plist"
OPENVPN_BIN="/opt/homebrew/sbin/openvpn"

if [[ ! -x "$OPENVPN_BIN" ]]; then
  echo "OpenVPN binary not found: $OPENVPN_BIN" >&2
  exit 1
fi

if [[ ! -f "$CONFIG" || ! -f "$AUTH_FILE" ]]; then
  echo "Missing runtime config or auth file. Run scripts/setup-openvpn-iitb-cli.sh first." >&2
  exit 1
fi

if grep -Eq 'REPLACE_WITH_(LDAP_USERNAME|VPN_PASSWORD)' "$AUTH_FILE"; then
  echo "Auth file still contains placeholder values: $AUTH_FILE" >&2
  exit 1
fi

TMP_PLIST="$(mktemp)"
cat > "$TMP_PLIST" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>local.openvpn.iitb</string>
  <key>ProgramArguments</key>
  <array>
    <string>$OPENVPN_BIN</string>
    <string>--config</string>
    <string>$CONFIG</string>
  </array>
  <key>RunAtLoad</key>
  <true/>
  <key>KeepAlive</key>
  <false/>
  <key>StandardOutPath</key>
  <string>/var/log/local.openvpn.iitb.log</string>
  <key>StandardErrorPath</key>
  <string>/var/log/local.openvpn.iitb.err</string>
</dict>
</plist>
EOF

sudo install -m 644 -o root -g wheel "$TMP_PLIST" "$PLIST"
rm -f "$TMP_PLIST"

sudo launchctl bootstrap system "$PLIST" 2>/dev/null || true
sudo launchctl enable system/local.openvpn.iitb
sudo launchctl kickstart -k system/local.openvpn.iitb

echo "Installed and started LaunchDaemon: local.openvpn.iitb"
echo "Logs:"
echo "  /var/log/local.openvpn.iitb.log"
echo "  /var/log/local.openvpn.iitb.err"
