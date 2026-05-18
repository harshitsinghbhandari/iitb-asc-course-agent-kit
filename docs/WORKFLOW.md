# Course Research Workflow

Use this when a student asks for course recommendations.

This workflow is unofficial and for personal educational/course-planning assistance only. Official ASC data, institute rules, department guidance, faculty-advisor approval, and registration decisions are authoritative.

## Inputs

Collect:

- Batch year.
- Programme.
- Department.
- Target term.
- Elective bucket needed.
- Preferences and constraints.

Example:

```text
I am a 2024 B.Tech IEOR student. Find Autumn 2026-27 STEM/Flexible electives with good grading, preferably AI/ML.
```

## Process

1. Read `AGENTS.md`.
2. Read all files under `domain-skills/asc.iitb.ac.in/`.
3. Confirm ASC is reachable directly or through IITB VPN, then log in.
4. Fetch target-term running courses.
5. Parse restrictions.
6. Filter eligible courses.
7. Fetch historical grading stats.
8. Open course-info pages for promising courses.
9. Produce a ranked shortlist with caveats.

## Common Department Codes

| Interest | ASC dept codes |
| --- | --- |
| CSE | `CSS,CS` |
| EE | `EE,EES` |
| CMINDS/Data Science | `DS` |
| Entrepreneurship | `ENT` |
| Design | `ID,DE,DEP` |
| IEOR | `IES,IE` |
| HSS | `HSS,HS` |
| Management | `MGT,MG,SOM,MGS,MNG,IWE` |

## Term Codes

| Term | Query |
| --- | --- |
| Autumn 2025-26 | `year=2025&semester=1` |
| Spring 2025-26 | `year=2025&semester=2` |
| Autumn 2026-27 | `year=2026&semester=1` |

## Recommendation Caveats

Always mention:

- Target term data may not be released yet.
- Historical grading is not a guarantee.
- Restrictions can change.
- Course buckets should be confirmed with the faculty advisor or department rules.
- ASC data is authenticated and should not be publicly redistributed.
