# ASC IIT Bombay — Navigation, Auth, and Frames

Field-tested against `asc.iitb.ac.in` on 2026-05-18 using browser-harness + a local Chrome CDP session.
IITB internal network access and ASC login are required. VPN is only needed when the user is outside IITB internal networks.

Do not store credentials in this skill. Use the user's approved local auth source or ask the user to log in when the session is not already authenticated.

---

## Connection

ASC is reachable from IITB internal networks such as IITB-Wireless, eduroam on campus, and internal LAN. If off-network, connect to IITB VPN first.

Quick reachability check:

```bash
curl -I --max-time 10 https://asc.iitb.ac.in/acadmenu/
```

In this workspace, Chrome was connected through a DevTools endpoint:

```bash
BU_CDP_URL=http://127.0.0.1:9333 browser-harness <<'PY'
new_tab("https://asc.iitb.ac.in/acadmenu/")
wait_for_load()
print(page_info())
PY
```

If a direct page load shows `Attempt Logged! Invalid Access.`, the endpoint probably requires ASC navigation state, a frame context, a POST flow, or a click from a listing page.

---

## Login State

Main entry point:

```text
https://asc.iitb.ac.in/acadmenu/
```

The portal uses frames:

- `leftPage`: navigation tree and sign-out state
- `rightPage`: login form and content area
- `rightPage1`: sometimes present for additional content

Check login:

```python
new_tab("https://asc.iitb.ac.in/acadmenu/")
wait_for_load()
logged_in = "Sign out" in js("""
(() => {
  try { return window.frames['leftPage'].document.body.innerText; }
  catch(e) { return ''; }
})()
""")
print(logged_in)
```

Login form fields are in `rightPage`:

```python
js("""
((username, password) => {
  const f = window.frames['rightPage'];
  const d = f.document;
  d.querySelector('[name="UserName"]').value = username;
  d.querySelector('[name="UserPassword"]').value = password;
  d.querySelector('form[name="loginForm"], form').submit();
  return true;
})(USERNAME, PASSWORD)
""")
wait_for_load()
```

Use only caller-provided credentials. Never print the password.

---

## Gotchas

- Many ASC pages reject direct top-level navigation with `Attempt Logged! Invalid Access.`
- Some pages work through `fetch(..., {credentials: "include"})` but not as visible top-level tabs.
- Course-detail pages must often be reached by posting to the department course list and clicking the course code link.
- Running-courses pages include hidden restriction tables in the HTML. `innerText` can hide enough structure that parsing the raw HTML is safer.
- A visible `View` link often corresponds to hidden restriction details already present in the page.
- Use `js()` fetch calls inside the authenticated browser session; plain shell `curl` will not have the ASC session cookies.
