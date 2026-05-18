# ASC IIT Bombay — Course Information Pages

Use this when the user asks for the "Course details" / "Course information" page for a course code, e.g. `CS6007`.

---

## What Does Not Work

Direct navigation to a course detail page can fail:

```text
https://asc.iitb.ac.in/academic/CourseRegistration/Common/crsedetail.jsp?ccd=CS6007&view=
```

Typical failure:

```text
Attempt Logged! Invalid Access.
```

The reliable path is:

1. Open the department course list via the course-information form flow.
2. Click the course-code link from that list.

---

## Department List Endpoint

Course information home:

```text
/academic/CourseRegistration/Common/newallCourse.jsp
```

Department list is loaded by POST:

```text
POST /academic/CourseRegistration/Common/allCourse.jsp
view=
deptcd=CSS,CS,
deptname=Computer Science and Engineering
```

Common department codes:

| Department | `deptcd` | `deptname` |
| --- | --- | --- |
| Computer Science and Engineering | `CSS,CS,` | `Computer Science and Engineering` |
| Electrical Engineering | `EE,EES,` | `Electrical Engineering` |
| Centre for Machine Intelligence and Data Science | `DS,` | `Centre for Machine Intelligence and Data Science` |
| Desai Sethi School of Entrepreneurship | `ENT,` | `Desai Sethi School of Entrepreneurship` |
| IDC School of Design | `DEP,DE,ID,` | `IDC School of Design` |
| Industrial Engineering and Operations Research | `IES,IE,` | `Industrial Engineering and Operations Research` |

---

## Open Course Detail in Browser

This loads the department list as a real page and clicks the course code. It preserves the navigation context that ASC expects.

```python
def open_course_info(course_code, deptcd, deptname):
    new_tab("https://asc.iitb.ac.in/academic/CourseRegistration/Common/newallCourse.jsp")
    wait_for_load()
    js(f"""
    (() => {{
      const form = document.createElement('form');
      form.method = 'POST';
      form.action = '/academic/CourseRegistration/Common/allCourse.jsp';
      const fields = {{view:'', deptcd:{deptcd!r}, deptname:{deptname!r}}};
      for (const [name, value] of Object.entries(fields)) {{
        const input = document.createElement('input');
        input.type = 'hidden';
        input.name = name;
        input.value = value;
        form.appendChild(input);
      }}
      document.body.appendChild(form);
      form.submit();
    }})()
    """)
    wait_for_load()
    clicked = js(f"""
    (() => {{
      const target = {course_code!r};
      const a = Array.from(document.querySelectorAll('a'))
        .find(a => a.textContent.trim() === target);
      if (!a) return false;
      a.click();
      return true;
    }})()
    """)
    wait_for_load()
    return clicked

open_course_info("CS6007", "CSS,CS,", "Computer Science and Engineering")
print(page_info())
```

For `CS6007`, the resulting page title was:

```text
COURSE INFO for CS6007
```

and body text began:

```text
Course deails of CS6007 - Multi-Agent Machine Learning (MAML)
Fields Content
Course Name Multi-Agent Machine Learning (MAML)
Total Credits 6.0
Type Theory
Lecture 3.0
...
```

---

## Fetch Course Detail HTML

If the user wants an artifact rather than an open browser tab, click into the course first, then save `document.documentElement.outerHTML`.

```python
from pathlib import Path

open_course_info("CS6007", "CSS,CS,", "Computer Science and Engineering")
html = js("document.documentElement.outerHTML")
Path("artifacts/asc_course_info_CS6007.html").write_text(html, encoding="utf-8")
```

---

## Parse Fields

Course details render as a table with `Fields` and `Content` columns.

```python
rows = js("""
(() => Array.from(document.querySelectorAll('tr')).map(tr =>
  Array.from(tr.cells || []).map(td => td.innerText.replace(/\\s+/g, ' ').trim())
).filter(r => r.length >= 2))()
""")

fields = {}
for row in rows:
    if row[0] and row[0] not in ("Fields",):
        fields[row[0]] = row[1]
print(fields)
```
