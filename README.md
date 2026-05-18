# IITB ASC Course Research Agent Kit

Reusable notes, scripts, and browser-harness domain skills for helping an AI assistant research IIT Bombay ASC course information: running courses, restrictions, course details, and historical grading stats.

## Disclaimer

This is an unofficial student-built project. It is not affiliated with, endorsed by, maintained by, or approved by IIT Bombay, ASC, or any IIT Bombay academic/administrative office.

Use it only for personal educational and course-planning assistance. It does not replace official ASC records, institute rules, department guidance, faculty-advisor approval, or registration decisions made through official IIT Bombay systems.

Users are responsible for complying with IIT Bombay policies, ASC terms/notices, network access rules, and privacy expectations. Do not use this project to bypass authentication, access controls, or authorization checks.

This repo is meant for a student to hand to an AI agent with a prompt like:

```text
Read AGENTS.md in this repo. I am a 2024 B.Tech student in Electrical Engineering.
Find good Autumn electives I am eligible for, especially AI/ML and HSS courses.
```

The agent should then know how to:

- Check whether ASC is already reachable from the IITB campus network, and ask for VPN setup only when needed.
- Connect to ASC through a browser session.
- Avoid ASC's `Attempt Logged! Invalid Access` traps.
- Fetch running courses and hidden restriction rows.
- Open course-information pages correctly.
- Pull historical grading statistics and rank candidate courses.

## What This Repo Contains

- `AGENTS.md`: the main operating guide for AI agents.
- `domain-skills/asc.iitb.ac.in/`: browser-harness playbooks for ASC.
- `scripts/`: helper scripts for OpenVPN and ASC scraping.
- `requirements.txt`: Python packages used by the scripts.

Generated ASC data, screenshots, local Chrome profiles, browser-harness checkouts, VPN profiles, and credentials are intentionally ignored by Git.

## Safety and Privacy

ASC is an authenticated IITB system. Treat all downloaded course tables, grade stats, screenshots, and HTML as private unless IITB explicitly publishes them publicly.

Do not commit:

- IITB LDAP/VPN credentials.
- `.ovpn` profiles.
- Chrome profiles or cookies.
- ASC screenshots, HTML exports, CSV/JSON scrape outputs, or personal registration data.

## Quick Start For A Student

1. Confirm ASC is reachable. If you are on IITB-Wireless, eduroam, or internal LAN, VPN may not be needed.
2. Install browser-harness or let your AI agent install it.
3. Launch Chrome with remote debugging or enable remote debugging for your active profile.
4. Ask your AI agent to read `AGENTS.md`.

Quick ASC-ready check:

```bash
curl -IL --max-time 15 https://asc.iitb.ac.in/acadmenu/
```

If this cannot connect, use the VPN setup below. If it redirects to `https://landing.iitb.ac.in/...`, your network can reach IITB but has not granted direct internal access to ASC yet; complete the IITB landing/SSO flow or use VPN.

For macOS with an IITB OpenVPN profile, when off the IITB network:

```bash
brew install openvpn
scripts/setup-openvpn-iitb-cli.sh ~/Downloads/BigSur-IITBVPN.ovpn
$EDITOR ~/.config/openvpn/iitb.auth
scripts/openvpn-iitb.sh
```

For Debian/Ubuntu Linux, when off the IITB network:

```bash
sudo apt update
sudo apt install -y openvpn python3-venv python3-pip chromium-browser
scripts/setup-openvpn-iitb-cli.sh ~/Downloads/IITBVPN.ovpn
$EDITOR ~/.config/openvpn/iitb.auth
scripts/openvpn-iitb.sh
```

For browser-harness:

```bash
git clone --depth=1 https://github.com/browser-use/browser-harness.git
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
pip install -e ./browser-harness
```

Then launch Chrome with a non-default debugging profile:

```bash
# macOS
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
  --remote-debugging-port=9333 \
  --user-data-dir="$HOME/chrome-debug-asc"

# Linux, depending on distro/package
google-chrome \
  --remote-debugging-port=9333 \
  --user-data-dir="$HOME/chrome-debug-asc"

chromium \
  --remote-debugging-port=9333 \
  --user-data-dir="$HOME/chrome-debug-asc"
```

Run browser-harness against that Chrome:

```bash
BU_CDP_URL=http://127.0.0.1:9333 BH_DOMAIN_SKILLS=1 browser-harness <<'PY'
new_tab("https://asc.iitb.ac.in/acadmenu/")
wait_for_load()
print(page_info())
PY
```

## Domain Skills

The reusable ASC knowledge lives in:

```text
domain-skills/asc.iitb.ac.in/
```

If you use browser-harness domain skills directly, copy or symlink this folder into:

```text
browser-harness/agent-workspace/domain-skills/asc.iitb.ac.in
```

Example:

```bash
mkdir -p browser-harness/agent-workspace/domain-skills
ln -s ../../../domain-skills/asc.iitb.ac.in \
  browser-harness/agent-workspace/domain-skills/asc.iitb.ac.in
```

## Typical Research Workflow

1. Confirm the student's batch, programme, department, and target term.
2. Fetch running courses for candidate departments and term.
3. Parse restrictions and filter for eligibility.
4. Pull historical grading stats for eligible courses.
5. Open course-information pages for promising courses.
6. Summarize recommendations with caveats: eligibility, slot conflicts, grading sample size, and course relevance.

For example, Autumn 2026-27 is `year=2026&semester=1`.

## Repository Status

This repo is a practical field guide. It is not an official IIT Bombay resource, and the ASC pages can change. When a flow breaks, update the relevant file in `domain-skills/asc.iitb.ac.in/` with the new working path.

## License

Code and documentation in this repository are released under the MIT License. See `LICENSE`.
