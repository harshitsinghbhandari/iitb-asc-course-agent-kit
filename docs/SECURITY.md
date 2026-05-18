# Security and Privacy

This repo is designed to keep secrets and private ASC data out of Git.

## Unofficial Educational Project

This project is unofficial and student-built. It is not affiliated with, endorsed by, maintained by, or approved by IIT Bombay, ASC, or any IIT Bombay academic/administrative office.

Use it only for personal educational and course-planning assistance. Do not use it to bypass authentication, access controls, authorization checks, institute policy, or network policy.

## Never Commit

- IITB LDAP/VPN passwords.
- `.ovpn` files.
- `~/.config/openvpn/iitb.auth`.
- Chrome profiles or cookies.
- `artifacts/` outputs.
- ASC screenshots.
- Exported ASC HTML.
- Grade statistics dumps.

## Why

ASC is an authenticated IITB system. Even if a course name seems harmless, scrape outputs can include personal context, session artifacts, registration data, or non-public operational data.

## Before Publishing

Run:

```bash
git status --short
git ls-files
```

Check that only source files, docs, scripts, and generic domain-skill notes are tracked.

Search for obvious accidental secrets:

```bash
rg -n "password|passwd|auth-user-pass|LDAP|REPLACE_WITH|iitb.auth|UserPassword" .
```

Placeholders are fine; real credentials are not.
