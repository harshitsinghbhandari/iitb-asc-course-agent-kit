from __future__ import annotations

import json
import re
import time
import urllib.parse
from pathlib import Path

from bs4 import BeautifulSoup


ASC_URL = "https://asc.iitb.ac.in/acadmenu/"
AUTH_FILE = Path.home() / ".config/openvpn/iitb.auth"
OUT_DIR = Path("artifacts/ieor_de_research")

IE_TERMS = [(year, sem) for year in range(2021, 2026) for sem in (1, 2)]
DE_TERMS = [(2025, 1), (2024, 1)]
IE_DEPT = "IE,IES"
DE_DEPT = "ID,DE,DEP"

PROF_PATTERNS = {
    "Narayan Rangaraj": [r"narayan\s+rangaraj"],
    "Nandyala Hemachandra": [r"hemachandra", r"\bnh\b", r"nandyala"],
    "Saurabh Jain": [r"saurabh\s+jain"],
    "Jayendran Venkateswaran": [r"jayendran", r"venkateswaran"],
    "Vinay Kumar": [r"vinay\s+kumar"],
}


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


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text.replace("\xa0", " ")).strip()


def running_courses_url(dept: str, year: int, sem: int) -> str:
    return "https://asc.iitb.ac.in/academic/utility/RunningCourses.jsp?" + urllib.parse.urlencode(
        {"deptcd": dept, "year": str(year), "semester": str(sem)}
    )


def tokenized_all_depts_url(year: int, sem: int) -> str:
    menu_html = js("""(() => window.frames['leftPage'].document.documentElement.outerHTML)()""")
    match = re.search(r"href='([^']*allDept\.jsp[^']*)'", menu_html, flags=re.I)
    if not match:
        raise SystemExit("Could not find tokenized Running Courses menu URL")
    url = match.group(1).replace("&amp;", "&")
    if url.startswith("/"):
        url = "https://asc.iitb.ac.in" + url
    sep = "&" if "?" in url else "?"
    return f"{url}{sep}{urllib.parse.urlencode({'year': year, 'semester': sem})}"


def prepare_term(year: int, sem: int) -> None:
    js(f"window.frames['rightPage'].location.href = {json.dumps(tokenized_all_depts_url(year, sem))}")
    wait_for_load()
    time.sleep(1)


def frame_rows_for_url(url: str) -> list[list[str]]:
    js(f"window.frames['rightPage'].location.href = {json.dumps(url)}")
    wait_for_load()
    time.sleep(1)
    return js(
        """(() => {
          const d = window.frames['rightPage'].document;
          return Array.from(d.querySelectorAll('tr')).map(tr =>
            Array.from(tr.cells || []).map(td => td.innerText.replace(/\\s+/g, ' ').trim()).filter(Boolean)
          ).filter(r => r.length);
        })()"""
    )


def extract_courses_from_rows(rows: list[list[str]], year: int, sem: int, dept: str) -> list[dict]:
    courses = []
    for row in rows:
        if len(row) < 5 or not row[0].isdigit():
            continue
        code = normalize_text(row[2])
        if not re.match(r"^[A-Z]{2,4}\s+\d", code):
            continue
        has_category = len(row) >= 10 and (
            "Course." in row[5] or "Course" in row[5] or "HASMED" in row[5] or "STEM" in row[5]
        )
        instructor_idx = 6 if has_category else 5
        venue_idx = instructor_idx + 1
        slot_idx = instructor_idx + 2
        division_idx = instructor_idx + 3
        courses.append(
            {
                "year": year,
                "semester": sem,
                "dept": dept,
                "code": code,
                "name": row[3],
                "type": row[4],
                "instructors": row[instructor_idx] if len(row) > instructor_idx else "",
                "slot": row[slot_idx] if len(row) > slot_idx else "",
                "division": row[division_idx] if len(row) > division_idx else "",
                "row": row,
            }
        )
    return courses


def grade_url(course_code: str, year: int, sem: int) -> str:
    return "/academic/Grading/statistics/gradstatforcrse.jsp?" + urllib.parse.urlencode(
        {"year": str(year), "semester": str(sem), "txtcrsecode": course_code, "submit": "SUBMIT"}
    )


def parse_grade_stats(course: dict, html: str) -> dict:
    soup = BeautifulSoup(html, "lxml")
    text = soup.get_text("\n", strip=True)
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    current = None
    sections = []
    for line in lines:
        if line.startswith("Total Grades Given for"):
            current = {"label": normalize_text(line), "grades": {}, "total": None}
            sections.append(current)
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
    for section in sections:
        section.pop("_pending", None)
    totals = {}
    for section in sections:
        for grade, count in section["grades"].items():
            totals[grade] = totals.get(grade, 0) + count
    points = {"AA": 10, "AB": 9, "BB": 8, "BC": 7, "CC": 6, "CD": 5, "DD": 4, "FF": 0, "FR": 0}
    denom = sum(count for grade, count in totals.items() if grade in points)
    weighted = sum(points[grade] * count for grade, count in totals.items() if grade in points)
    return {
        "course": course,
        "sections": sections,
        "grade_totals": totals,
        "graded_total": sum(totals.values()),
        "weighted_avg_excluding_nonpoints": round(weighted / denom, 3) if denom else None,
        "raw_text": text,
    }


def matches_prof(course: dict) -> list[str]:
    hay = course.get("instructors", "").lower()
    matched = []
    for prof, patterns in PROF_PATTERNS.items():
        if any(re.search(pattern, hay, flags=re.I) for pattern in patterns):
            matched.append(prof)
    return matched


def dedupe_courses(courses: list[dict]) -> list[dict]:
    seen = set()
    deduped = []
    for course in courses:
        key = (course["year"], course["semester"], course["code"], course["name"], course["instructors"])
        if key in seen:
            continue
        seen.add(key)
        deduped.append(course)
    return deduped


def attach_stats(courses: list[dict], partial_path: Path) -> list[dict]:
    out = []
    batch_size = 8
    for start in range(0, len(courses), batch_size):
        batch = courses[start : start + batch_size]
        html_pages = browser_fetch_many([grade_url(c["code"], c["year"], c["semester"]) for c in batch])
        for course, html in zip(batch, html_pages):
            out.append(parse_grade_stats(course, html))
        partial_path.write_text(json.dumps(out, indent=2), encoding="utf-8")
        print(f"{partial_path.name}: {len(out)}/{len(courses)}")
    return out


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    ensure_logged_in()

    ie_courses = []
    for year, sem in IE_TERMS:
        prepare_term(year, sem)
        rows = frame_rows_for_url(running_courses_url(IE_DEPT, year, sem))
        ie_courses.extend(extract_courses_from_rows(rows, year, sem, IE_DEPT))
    ie_courses = dedupe_courses(ie_courses)
    prof_courses = []
    for course in ie_courses:
        matched = matches_prof(course)
        if matched:
            course["matched_professors"] = matched
            prof_courses.append(course)
    (OUT_DIR / "ie_all_courses.json").write_text(json.dumps(ie_courses, indent=2), encoding="utf-8")
    (OUT_DIR / "professor_matched_course_list.json").write_text(json.dumps(prof_courses, indent=2), encoding="utf-8")

    de_courses = []
    for year, sem in DE_TERMS:
        prepare_term(year, sem)
        rows = frame_rows_for_url(running_courses_url(DE_DEPT, year, sem))
        de_courses.extend(extract_courses_from_rows(rows, year, sem, DE_DEPT))
    de_courses = dedupe_courses([c for c in de_courses if c["code"].startswith("DE ") and c["code"] != "DE 250"])
    (OUT_DIR / "de_autumn_course_list.json").write_text(json.dumps(de_courses, indent=2), encoding="utf-8")

    prof_stats = attach_stats(prof_courses, OUT_DIR / "professor_matched_courses.partial.json")
    de_stats = attach_stats(de_courses, OUT_DIR / "de_autumn_courses.partial.json")

    (OUT_DIR / "professor_matched_courses.json").write_text(json.dumps(prof_stats, indent=2), encoding="utf-8")
    (OUT_DIR / "de_autumn_courses.json").write_text(json.dumps(de_stats, indent=2), encoding="utf-8")
    print(json.dumps({"ie_courses": len(ie_courses), "professor_matches": len(prof_stats), "de_courses": len(de_stats)}, indent=2))


main()
