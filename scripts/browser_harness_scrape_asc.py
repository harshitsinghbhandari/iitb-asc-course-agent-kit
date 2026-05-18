from __future__ import annotations

import json
import re
import time
import urllib.parse
from pathlib import Path

from bs4 import BeautifulSoup


ASC_URL = "https://asc.iitb.ac.in/acadmenu/"
AUTH_FILE = Path.home() / ".config/openvpn/iitb.auth"
OUT_DIR = Path("artifacts/asc_grade_stats")
YEAR = "2025"
SEMESTER = "2"


def read_auth() -> tuple[str, str]:
    lines = AUTH_FILE.read_text(encoding="utf-8").splitlines()
    if (
        len(lines) < 2
        or "REPLACE_WITH_LDAP_USERNAME" in lines[0]
        or "REPLACE_WITH_VPN_PASSWORD" in lines[1]
    ):
        raise SystemExit(f"Auth file is missing usable credentials: {AUTH_FILE}")
    return lines[0], lines[1]


def ensure_logged_in() -> None:
    username, password = read_auth()
    new_tab(ASC_URL)
    wait_for_load()
    time.sleep(1)
    state = js(
        """(() => {
          try { return window.frames['leftPage'].document.body.innerText; }
          catch(e) { return ''; }
        })()"""
    )
    if "Sign out" in state:
        return

    result = js(
        """((username, password) => {
          const f = window.frames['rightPage'];
          if (!f || !f.document) return {ok:false, reason:'rightPage missing'};
          const d = f.document;
          const u = d.querySelector('[name="UserName"]');
          const p = d.querySelector('[name="UserPassword"]');
          const form = d.querySelector('form[name="loginForm"], form');
          if (!u || !p || !form) return {ok:false, reason:'login controls missing'};
          u.value = username;
          p.value = password;
          form.submit();
          return {ok:true};
        })(%s, %s)"""
        % (json.dumps(username), json.dumps(password))
    )
    if not result.get("ok"):
        raise SystemExit(f"Login submit failed: {result}")

    deadline = time.time() + 90
    while time.time() < deadline:
        time.sleep(2)
        text = js(
            """(() => {
              try { return window.frames['leftPage'].document.body.innerText; }
              catch(e) { return ''; }
            })()"""
        )
        if "Sign out" in text:
            return
    raise SystemExit("Timed out waiting for ASC login")


def browser_fetch_text(url: str) -> str:
    return js(
        """(async (url) => {
          const response = await fetch(url, {credentials: 'include'});
          return await response.text();
        })(%s)"""
        % json.dumps(url)
    )


def browser_fetch_many(urls: list[str]) -> list[str]:
    return js(
        """(async (urls) => {
          const output = [];
          for (const url of urls) {
            const response = await fetch(url, {credentials: 'include'});
            output.push(await response.text());
          }
          return output;
        })(%s)"""
        % json.dumps(urls)
    )


def extract_department_links(index_html: str) -> list[str]:
    links = re.findall(r'href="([^"]*RunningCourses\.jsp[^"]*)"', index_html, flags=re.I)
    return sorted({urllib.parse.unquote(link.replace("&amp;", "&")) for link in links})


def authenticated_menu_html() -> str:
    return js(
        """(() => {
          const d = window.frames['leftPage'].document;
          return d.documentElement.outerHTML;
        })()"""
    )


def tokenized_running_courses_url() -> str:
    menu_html = authenticated_menu_html()
    match = re.search(r"href='([^']*allDept\.jsp[^']*)'", menu_html, flags=re.I)
    if not match:
        raise SystemExit("Could not find tokenized Running Courses URL in authenticated menu")
    url = match.group(1).replace("&amp;", "&")
    sep = "&" if "?" in url else "?"
    return f"{url}{sep}{urllib.parse.urlencode({'year': YEAR, 'semester': SEMESTER})}"


def extract_courses(course_html: str) -> list[dict]:
    soup = BeautifulSoup(course_html, "lxml")
    rows = [
        [cell.get_text(" ", strip=True) for cell in tr.find_all(["td", "th"]) if cell.get_text(" ", strip=True)]
        for tr in soup.find_all("tr")
    ]
    rows = [row for row in rows if row]
    courses: dict[str, dict] = {}
    for row in rows:
        if len(row) < 5 or not row[0].isdigit():
            continue
        code = row[2].replace("\xa0", " ").strip()
        if not re.match(r"^[A-Z]{2,4}\s+\d", code):
            continue
        courses.setdefault(
            code,
            {
                "code": code,
                "name": row[3],
                "type": row[4],
                "instructors": row[6] if len(row) > 6 else "",
                "slots": set(),
                "divisions": set(),
            },
        )
        if len(row) > 8:
            courses[code]["slots"].add(row[8])
        if len(row) > 9:
            courses[code]["divisions"].add(row[9])
    normalized = []
    for course in courses.values():
        course["slots"] = sorted(course["slots"])
        course["divisions"] = sorted(course["divisions"])
        normalized.append(course)
    return sorted(normalized, key=lambda item: item["code"])


def parse_grade_stats(course_code: str, html: str) -> dict:
    soup = BeautifulSoup(html, "lxml")
    text = soup.get_text("\n", strip=True)
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    result = {"code": course_code, "raw_text": text, "sections": []}
    current = None
    for line in lines:
        if line == "Course Name":
            continue
        if "Course Name" in line:
            result["course_name_line"] = line
        if line.startswith("Total Grades Given for"):
            current = {"label": line, "grades": {}, "total": None}
            result["sections"].append(current)
            continue
        if current and re.match(r"^(AA|AB|AP|BB|BC|CC|CD|DD|FF|FR|PP|NP|DX|II|DR|AU|Total)$", line):
            current["_pending"] = line
            continue
        if current and current.get("_pending") and line.isdigit():
            grade = current.pop("_pending")
            if grade == "Total":
                current["total"] = int(line)
            else:
                current["grades"][grade] = int(line)
    for section in result["sections"]:
        section.pop("_pending", None)
    return result


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    ensure_logged_in()
    capture_screenshot(str(OUT_DIR / "logged_in.png"))

    index_url = tokenized_running_courses_url()
    index_html = browser_fetch_text(index_url)
    (OUT_DIR / "running_courses_index.html").write_text(index_html, encoding="utf-8")

    department_links = extract_department_links(index_html)
    all_courses: dict[str, dict] = {}
    for link in department_links:
        html = browser_fetch_text(link)
        for course in extract_courses(html):
            all_courses.setdefault(course["code"], course)

    courses = sorted(all_courses.values(), key=lambda item: item["code"])
    (OUT_DIR / "running_courses.json").write_text(json.dumps(courses, indent=2), encoding="utf-8")

    stats = []
    batch_size = 25
    for start in range(0, len(courses), batch_size):
        batch = courses[start : start + batch_size]
        urls = []
        for course in batch:
            query = urllib.parse.urlencode(
                {"year": YEAR, "semester": SEMESTER, "txtcrsecode": course["code"], "submit": "SUBMIT"}
            )
            urls.append(f"/academic/Grading/statistics/gradstatforcrse.jsp?{query}")
        html_pages = browser_fetch_many(urls)
        for course, html in zip(batch, html_pages):
            parsed = parse_grade_stats(course["code"], html)
            parsed["course"] = course
            stats.append(parsed)
        (OUT_DIR / "grade_stats.partial.json").write_text(json.dumps(stats, indent=2), encoding="utf-8")
        print(f"fetched {len(stats)}/{len(courses)} grade pages")

    (OUT_DIR / "grade_stats.json").write_text(json.dumps(stats, indent=2), encoding="utf-8")
    print(json.dumps({"year": YEAR, "semester": SEMESTER, "courses": len(courses), "grade_stats": len(stats)}, indent=2))


main()
