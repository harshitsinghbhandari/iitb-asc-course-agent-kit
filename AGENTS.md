# AGENTS.md

This repo teaches an AI agent how to help IIT Bombay students research ASC courses.

You are operating against an authenticated IITB system. Be careful with credentials, cookies, screenshots, exported HTML, and downloaded grade statistics.

## Prime Directive

Help the student answer course-planning questions using ASC evidence:

- course information pages
- running-course tables
- hidden restriction rows
- historical grading statistics
- public department/curriculum pages when relevant

Do not republish private ASC data. Do not commit credentials, cookies, Chrome profiles, `.ovpn` files, screenshots, exported ASC HTML, or scrape outputs.

## First Read

Before touching ASC, read these files:

- `domain-skills/asc.iitb.ac.in/navigation.md`
- `domain-skills/asc.iitb.ac.in/course-info.md`
- `domain-skills/asc.iitb.ac.in/running-courses.md`
- `domain-skills/asc.iitb.ac.in/grading-stats.md`

Use browser-harness for ASC browser work when available.

## Ask The Student For Context

Get these facts before ranking courses:

- Batch year, e.g. `2024`.
- Programme, e.g. `B.Tech.`, `Dual Degree`, `B.S.`, `M.Tech.`.
- Department or academic unit, e.g. `IEOR`, `EE`, `CSE`.
- Target term, e.g. `Autumn 2026-27`.
- Course buckets needed, e.g. `Department Elective`, `Institute Elective`, `STEM`, `HSS/HASMED`, `Flexible`.
- Preferences: grading, workload, AI/ML, finance, design, no labs, no evening slots, etc.

For IITB ASC terms:

- Autumn is `semester=1`.
- Spring is `semester=2`.
- Autumn 2026-27 is `year=2026&semester=1`.

## Setup Checklist

1. Check whether ASC is reachable directly. If the user is on IITB-Wireless, eduroam, or internal LAN, VPN may not be required.
2. Confirm Chrome remote debugging is available.
3. Confirm browser-harness can attach to Chrome.
4. Open `https://asc.iitb.ac.in/acadmenu/`.
5. If not logged in, ask the student to provide credentials through their approved local method or log in manually. Never ask them to paste passwords into chat unless they explicitly accept that risk.

The scripts expect credentials at:

```text
~/.config/openvpn/iitb.auth
```

Format:

```text
LDAP_USERNAME
VPN_OR_ASC_PASSWORD
```

This file must be mode `600`.

## Network And VPN Notes

ASC is reachable from IITB internal networks such as IITB-Wireless, eduroam on campus, and internal LAN. In that case, do not require VPN; proceed directly to browser setup and ASC login.

Before asking the user to configure VPN, test reachability:

```bash
curl -I --max-time 10 https://asc.iitb.ac.in/acadmenu/
```

If this fails or times out, ask the user to connect to IITB VPN or move to an IITB internal network.

For macOS, the included scripts support OpenVPN CLI:

```bash
brew install openvpn
scripts/setup-openvpn-iitb-cli.sh /path/to/IITBVPN.ovpn
$EDITOR ~/.config/openvpn/iitb.auth
scripts/openvpn-iitb.sh
```

For unattended startup on macOS, `scripts/install-openvpn-iitb-launchdaemon.sh` installs a LaunchDaemon. Use it only if the user understands it will create a root-owned system service.

For Debian/Ubuntu Linux:

```bash
sudo apt update
sudo apt install -y openvpn python3-venv python3-pip
scripts/setup-openvpn-iitb-cli.sh /path/to/IITBVPN.ovpn
$EDITOR ~/.config/openvpn/iitb.auth
scripts/openvpn-iitb.sh
```

On Linux, do not use the LaunchDaemon script. If the user wants unattended startup, use NetworkManager/OpenVPN or a systemd service appropriate for their distro.

## Browser Setup Notes

Preferred reliable browser setup on macOS:

```bash
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
  --remote-debugging-port=9333 \
  --user-data-dir="$HOME/chrome-debug-asc"
```

Preferred reliable browser setup on Linux:

```bash
google-chrome \
  --remote-debugging-port=9333 \
  --user-data-dir="$HOME/chrome-debug-asc"
```

If `google-chrome` is not installed, try `chromium` or `chromium-browser` with the same flags.

Then run:

```bash
BU_CDP_URL=http://127.0.0.1:9333 BH_DOMAIN_SKILLS=1 browser-harness <<'PY'
new_tab("https://asc.iitb.ac.in/acadmenu/")
wait_for_load()
print(page_info())
PY
```

Alternative: use Chrome's `chrome://inspect/#remote-debugging` setting for the user's active profile. That preserves logins but may require the user to click an Allow prompt.

## ASC Access Rules

ASC often rejects direct URL navigation:

```text
Attempt Logged! Invalid Access.
```

When this happens:

- For course details, load the department course list with the form POST, then click the course code.
- For grading stats, use browser-session `fetch(..., {credentials: "include"})`.
- For running courses, direct navigation often works after login, but browser-session fetch is safer for scraping.
- For frame pages, start from `https://asc.iitb.ac.in/acadmenu/` and use `leftPage`/`rightPage`.

## Course Research Workflow

1. Fetch target-term running courses for relevant departments.
2. Parse course code, name, type, category, instructor, slot, division, registration limit, and restrictions.
3. Apply eligibility filtering from `Restrictions`.
4. Remove non-normal electives unless asked: BTP, DDP, seminar, communication skills, projects, labs if the user dislikes labs.
5. Pull historical grading statistics for eligible candidates.
6. Compute:
   - weighted average excluding `AP`, `AU`, `II`, `DR`
   - graded sample size
   - AA/AB percentage
   - fail percentage from `FF` and `FR`
7. Open course-information pages for the strongest candidates to inspect syllabus and references.
8. Summarize recommendations with explicit caveats.

## Eligibility Heuristic

For a student with `batch=2024`, `programme=B.Tech.`, and department `IEOR`:

- A row like `COURSE / 2024 / ALL / B.Tech. / Allowed / Non-Overridable` means likely eligible.
- No restriction rows means likely eligible, but verify during registration.
- A row allowing only another department plus `ALL / ALL / ALL / Deny` means blocked.
- Department-specific rows outrank broad rows.
- Always report uncertainty if restrictions are missing or ambiguous.

Adapt this to the student's actual batch, programme, and department.

## Ranking Guidance

Prefer courses that satisfy all of:

- Eligible by restrictions.
- Relevant to the student's stated goals.
- Reasonable grade history with adequate sample size.
- No obvious slot conflict with known core courses.
- Normal course type, not project/seminar/BTP.

Do not rank by average alone. A `9.8` average with `n=5` is weaker evidence than `8.8` with `n=100`.

## Output Format For Students

For each recommended course, include:

- Course code and name.
- Bucket fit: STEM, HSS/HASMED, Institute Elective, Department Elective, Flexible.
- Eligibility evidence from restrictions.
- Grading stats: average, sample size, AA/AB percentage, fail percentage.
- Why it fits the student's goals.
- Warnings: workload, advanced prerequisites, small sample size, slot uncertainty.

Keep raw data paths available, but avoid dumping large private ASC tables into chat.

## Public vs Private Sources

Use public IITB/department pages for curriculum definitions and public course context. Use ASC only for authenticated operational data.

If answering with web citations, cite public pages only. Do not create public links to private local ASC artifacts.

## Maintenance

When ASC changes:

- Update the relevant domain skill.
- Keep durable endpoint patterns and gotchas.
- Do not record personal data, cookies, tokens, or passwords.
- Keep examples generic unless the course itself is public and non-sensitive.
