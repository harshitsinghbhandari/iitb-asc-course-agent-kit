# Setup

This document is for a student or an AI agent preparing a local machine to research IITB ASC courses.

## Requirements

- IITB network access: campus network or IITB VPN.
- An IITB ASC account.
- Python 3.11+.
- Chrome or Chromium.
- browser-harness.

## Python Environment

```bash
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
```

## Network Access

ASC is available from IITB internal networks. If the user is on IITB-Wireless, eduroam on campus, or internal LAN, VPN may not be required.

Test first:

```bash
curl -I --max-time 10 https://asc.iitb.ac.in/acadmenu/
```

If this succeeds, skip OpenVPN and continue to browser-harness setup. If it fails or times out, use VPN.

## OpenVPN

Install OpenVPN on macOS:

```bash
brew install openvpn
```

Install OpenVPN on Debian/Ubuntu Linux:

```bash
sudo apt update
sudo apt install -y openvpn
```

If your distro packages Chromium separately, also install one browser:

```bash
sudo apt install -y chromium-browser
# or:
sudo apt install -y chromium
```

Create a runtime config from the IITB `.ovpn` profile:

```bash
scripts/setup-openvpn-iitb-cli.sh /path/to/IITBVPN.ovpn
```

Edit:

```text
~/.config/openvpn/iitb.auth
```

Expected format:

```text
LDAP_USERNAME
VPN_OR_ASC_PASSWORD
```

Permissions:

```bash
chmod 600 ~/.config/openvpn/iitb.auth
```

Connect:

```bash
scripts/openvpn-iitb.sh
```

That command uses `sudo openvpn --config ~/.config/openvpn/iitb-cli.ovpn`, so it works on both macOS and Linux if `openvpn` is on `PATH`.

The LaunchDaemon helper is macOS-only:

```bash
scripts/install-openvpn-iitb-launchdaemon.sh
```

On Linux, prefer your distro's NetworkManager/OpenVPN integration or a systemd unit if you need unattended startup.

## browser-harness

Clone browser-harness in this repo or elsewhere:

```bash
git clone --depth=1 https://github.com/browser-use/browser-harness.git
pip install -e ./browser-harness
```

Expose the ASC domain skills:

```bash
mkdir -p browser-harness/agent-workspace/domain-skills
ln -s ../../../domain-skills/asc.iitb.ac.in \
  browser-harness/agent-workspace/domain-skills/asc.iitb.ac.in
```

## Chrome Remote Debugging

Reliable isolated profile on macOS:

```bash
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
  --remote-debugging-port=9333 \
  --user-data-dir="$HOME/chrome-debug-asc"
```

Reliable isolated profile on Linux:

```bash
google-chrome \
  --remote-debugging-port=9333 \
  --user-data-dir="$HOME/chrome-debug-asc"
```

If the binary is named `chromium` or `chromium-browser`:

```bash
chromium \
  --remote-debugging-port=9333 \
  --user-data-dir="$HOME/chrome-debug-asc"
```

```bash
chromium-browser \
  --remote-debugging-port=9333 \
  --user-data-dir="$HOME/chrome-debug-asc"
```

Attach:

```bash
BU_CDP_URL=http://127.0.0.1:9333 BH_DOMAIN_SKILLS=1 browser-harness <<'PY'
new_tab("https://asc.iitb.ac.in/acadmenu/")
wait_for_load()
print(page_info())
PY
```
