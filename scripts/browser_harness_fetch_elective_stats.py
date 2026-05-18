from __future__ import annotations

import json
import re
import time
import urllib.parse
from pathlib import Path

from bs4 import BeautifulSoup


ASC_URL = "https://asc.iitb.ac.in/acadmenu/"
AUTH_FILE = Path.home() / ".config/openvpn/iitb.auth"
IN_PATH = Path("artifacts/elective_search/candidate_courses_without_stats.json")
OUT_DIR = Path("artifacts/elective_search")


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


def grade_url(course_code: str, year: int = 2025, sem: int = 1) -> str:
    return "/academic/Grading/statistics/gradstatforcrse.jsp?" + urllib.parse.urlencode(
        {"year": str(year), "semester": str(sem), "txtcrsecode": course_code, "submit": "SUBMIT"}
    )


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text.replace("\xa0", " ")).strip()


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
        "aa_ab_percent": round(100 * (totals.get("AA", 0) + totals.get("AB", 0)) / denom, 1) if denom else None,
        "fail_percent": round(100 * (totals.get("FF", 0) + totals.get("FR", 0)) / denom, 1) if denom else None,
        "raw_text": text,
    }


def dedupe(courses: list[dict]) -> list[dict]:
    seen = set()
    out = []
    for course in courses:
        key = (course.get("code"), course.get("name"), course.get("instructors"), course.get("category"))
        if key in seen:
            continue
        seen.add(key)
        out.append(course)
    return out


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    ensure_logged_in()
    courses = json.loads(IN_PATH.read_text(encoding="utf-8"))
    wanted = []
    for course in courses:
        code = course.get("code", "")
        name = course.get("name", "")
        if not course.get("likely_allowed_ieor_2024_btech"):
            continue
        if code.startswith(("ENT", "CS", "EE", "DS")):
            wanted.append(course)
    wanted = dedupe(wanted)
    results = []
    batch_size = 10
    for start in range(0, len(wanted), batch_size):
        batch = wanted[start : start + batch_size]
        pages = browser_fetch_many([grade_url(c["code"]) for c in batch])
        for course, html in zip(batch, pages):
            results.append(parse_grade_stats(course, html))
        (OUT_DIR / "candidate_courses_with_stats.partial.json").write_text(
            json.dumps(results, indent=2), encoding="utf-8"
        )
        print(f"candidate stats: {len(results)}/{len(wanted)}")
    (OUT_DIR / "candidate_courses_with_stats.json").write_text(json.dumps(results, indent=2), encoding="utf-8")

    rows = []
    for item in results:
        c = item["course"]
        rows.append(
            {
                "code": c.get("code"),
                "name": c.get("name"),
                "category": c.get("category"),
                "type": c.get("type"),
                "instructors": c.get("instructors"),
                "slot": c.get("slot"),
                "division": c.get("division"),
                "weighted_avg": item.get("weighted_avg_excluding_nonpoints"),
                "graded_total": item.get("graded_total"),
                "aa_ab_percent": item.get("aa_ab_percent"),
                "fail_percent": item.get("fail_percent"),
                "restriction_text": c.get("restriction_text", ""),
            }
        )
    rows.sort(key=lambda r: ((r["weighted_avg"] is not None), r["weighted_avg"] or -1, r["graded_total"] or 0), reverse=True)
    csv_lines = [
        "code,name,category,type,instructors,slot,division,weighted_avg,graded_total,aa_ab_percent,fail_percent,restriction_text"
    ]
    for r in rows:
        vals = [r[k] for k in csv_lines[0].split(",")]
        csv_lines.append(",".join('"' + str(v or "").replace('"', '""') + '"' for v in vals))
    (OUT_DIR / "candidate_ranked_summary.csv").write_text("\n".join(csv_lines) + "\n", encoding="utf-8")


main()
