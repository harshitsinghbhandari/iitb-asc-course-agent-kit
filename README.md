# IITB ASC Course Research Agent Kit

Reusable notes, scripts, and browser-harness domain skills for helping an AI assistant research IIT Bombay ASC course information: running courses, restrictions, course details, and historical grading stats.

This repo is meant for a student to hand to an AI agent with a prompt like:

```text
Read AGENTS.md in this repo. I am a 2024 B.Tech student in Electrical Engineering.
Find good Autumn electives I am eligible for, especially AI/ML and HSS courses.
```

The agent should then know how to:

- Ask the user to set up IITB VPN access.
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

1. Install OpenVPN and connect to IITB VPN.
2. Install browser-harness or let your AI agent install it.
3. Launch Chrome with remote debugging or enable remote debugging for your active profile.
4. Ask your AI agent to read `AGENTS.md`.

For macOS with an IITB OpenVPN profile:

```bash
brew install openvpn
scripts/setup-openvpn-iitb-cli.sh ~/Downloads/BigSur-IITBVPN.ovpn
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
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
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
