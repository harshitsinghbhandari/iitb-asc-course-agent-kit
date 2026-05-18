# Security and Privacy

This repo is designed to keep secrets and private ASC data out of Git.

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
