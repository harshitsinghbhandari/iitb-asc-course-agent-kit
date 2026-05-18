# ASC IIT Bombay — Running Courses and Restrictions

Use this for term course lists, instructors, slots, registration limits, and eligibility restrictions.

---

## Endpoint

```text
/academic/utility/RunningCourses.jsp?deptcd=<DEPTCODES>&year=<START_YEAR>&semester=<SEM>
```

Examples:

```text
https://asc.iitb.ac.in/academic/utility/RunningCourses.jsp?deptcd=ENT&year=2025&semester=1
https://asc.iitb.ac.in/academic/utility/RunningCourses.jsp?deptcd=CSS%2CCS&year=2025&semester=1
https://asc.iitb.ac.in/academic/utility/RunningCourses.jsp?deptcd=EE%2CEES&year=2025&semester=1
https://asc.iitb.ac.in/academic/utility/RunningCourses.jsp?deptcd=DS&year=2025&semester=1
https://asc.iitb.ac.in/academic/utility/RunningCourses.jsp?deptcd=IES%2CIE&year=2025&semester=1
https://asc.iitb.ac.in/academic/utility/RunningCourses.jsp?deptcd=ID%2CDE%2CDEP&year=2025&semester=1
```

Semester values:

- `1`: Autumn
- `2`: Spring
- `3`: Summer

`year=2025&semester=1` means Autumn 2025-26.

---

## Fetch HTML in Authenticated Browser Session

```python
from urllib.parse import urlencode

def running_courses_url(deptcd, year, semester):
    return "/academic/utility/RunningCourses.jsp?" + urlencode({
        "deptcd": deptcd,
        "year": str(year),
        "semester": str(semester),
    })

html = js(f"""
(async () => {{
  const r = await fetch({running_courses_url('CSS,CS', 2025, 1)!r}, {{credentials: 'include'}});
  return await r.text();
}})()
""")
```

For visual inspection, direct navigation to the full URL generally works after login:

```python
new_tab("https://asc.iitb.ac.in/academic/utility/RunningCourses.jsp?deptcd=CSS%2CCS&year=2025&semester=1")
wait_for_load()
```

---

## Parse Course Rows

Rows can have variable columns depending on whether "Course content category" is populated.
Prefer parsing table rows from DOM or BeautifulSoup and then normalizing.

```python
rows = js("""
(() => Array.from(document.querySelectorAll('tr')).map(tr =>
  Array.from(tr.cells || []).map(td =>
    td.innerText.replace(/\\s+/g, ' ').trim()
  ).filter(Boolean)
).filter(r => r.length))()
""")
```

Course rows usually start with a serial number and include:

- type/timetable marker
- course code
- course name
- course type
- course content category
- instructor(s)
- venue
- slot
- division
- biometric flag
- registration limit
- restrictions link / hidden restrictions

---

## Hidden Restriction Tables

The visible page often shows only `View`, but the restriction rows are already present in the HTML.
Extract them from hidden tables/divs rather than clicking each `View`.

Restriction row shape observed:

```text
Course Code / Batch / Department / Programme / Allowed-or-Deny / Overridable
```

Examples:

```text
CS 635 / 2024 / ALL / B.Tech. / Allowed / Non-Overridable
CS 635 / ALL / ALL / ALL / Deny / Non-Overridable
ENT620 / 2024 / ALL / B.Tech. / Allowed / Non-Overridable
ENT620 / ALL / ALL / ALL / Deny / Non-Overridable
DS 603 / ALL / Centre for Machine Intelligence and Data Science / ALL / Allowed / Non-Overridable
DS 603 / ALL / ALL / ALL / Deny / Non-Overridable
```

Eligibility heuristic for a 2024 B.Tech. IEOR student:

1. If there is a specific allow row matching `2024 / ALL / B.Tech.`, treat as eligible unless a more specific IEOR deny exists.
2. If there are no restriction rows, treat as likely eligible, but verify during registration.
3. If only another department is allowed and there is a global `ALL / ALL / ALL / Deny`, treat as blocked.
4. If a course is project/seminar/BTP/DDP, don't recommend it as a normal elective even if the heuristic says eligible.

---

## Autumn 2026-27 Caveat

As of 2026-05-18, ASC Autumn 2026-27 running-course pages for ENT/CS/EE/DS/IE/DE had headers but no course rows.
For next-semester planning before ASC is populated, use Autumn 2025-26 as a proxy and clearly label it as such.
