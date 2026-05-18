# ASC IIT Bombay — Course Grading Statistics

Use this for historical grade distributions by course, year, and semester.

---

## Endpoint

```text
/academic/Grading/statistics/gradstatforcrse.jsp?year=<START_YEAR>&semester=<SEM>&txtcrsecode=<COURSE_CODE>&submit=SUBMIT
```

Example:

```text
/academic/Grading/statistics/gradstatforcrse.jsp?year=2025&semester=1&txtcrsecode=CS6007&submit=SUBMIT
```

`year=2025&semester=1` means Autumn 2025-26.

---

## Important Access Behavior

Opening the grading URL as a top-level tab can show:

```text
Attempt Logged! Invalid Access.
```

Fetching it inside the authenticated browser session usually works:

```python
from urllib.parse import urlencode

def grade_url(course_code, year, semester):
    return "/academic/Grading/statistics/gradstatforcrse.jsp?" + urlencode({
        "year": str(year),
        "semester": str(semester),
        "txtcrsecode": course_code,
        "submit": "SUBMIT",
    })

html = js(f"""
(async () => {{
  const r = await fetch({grade_url('CS6007', 2025, 1)!r}, {{credentials: 'include'}});
  return await r.text();
}})()
""")
```

If the user wants to see it in Chrome, write a local HTML wrapper and open the `file://` URL.

---

## Parse Grade Tables

The page text contains sections like:

```text
Total Grades Given for ...
AA
16
AB
11
...
Total
44
```

Parser:

```python
import re
from bs4 import BeautifulSoup

def normalize_text(text):
    return re.sub(r"\\s+", " ", text.replace("\\xa0", " ")).strip()

def parse_grade_stats(html):
    soup = BeautifulSoup(html, "lxml")
    text = soup.get_text("\\n", strip=True)
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
        "sections": sections,
        "grade_totals": totals,
        "graded_total": sum(totals.values()),
        "weighted_avg_excluding_nonpoints": round(weighted / denom, 3) if denom else None,
        "aa_ab_percent": round(100 * (totals.get("AA", 0) + totals.get("AB", 0)) / denom, 1) if denom else None,
        "fail_percent": round(100 * (totals.get("FF", 0) + totals.get("FR", 0)) / denom, 1) if denom else None,
        "raw_text": text,
    }
```

Non-point grades such as `AP`, `AU`, `II`, and `DR` should be excluded from GPA-style weighted averages.

---

## Bulk Fetch Pattern

Use browser-session `fetch` in small batches.

```python
def browser_fetch_many(urls):
    return js(
        """(async (urls) => {
          const output = [];
          for (const url of urls) {
            const response = await fetch(url, {credentials: 'include'});
            output.push(await response.text());
          }
          return output;
        })(%s)""" % json.dumps(urls)
    )
```

Batch size `8-12` was stable on ASC.

---

## Confirmed Example: CS6007

Autumn 2025-26 grading stats for `CS6007` showed:

- Course: Multi-Agent Machine Learning (MAML)
- Instructor in running courses: Avishek Ghosh
- Weighted average excluding non-point grades: `9.0`
- Graded total counted by parser: `44`
- AA/AB percent: `71.1`
- Fail percent: `0.0`
