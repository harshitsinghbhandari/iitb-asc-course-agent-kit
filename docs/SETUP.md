# Setup

This document is for a student or an AI agent preparing a local machine to research IITB ASC courses.

## Requirements

- IITB VPN access.
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

## OpenVPN

Install OpenVPN:

```bash
brew install openvpn
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

Reliable isolated profile:

```bash
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
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
