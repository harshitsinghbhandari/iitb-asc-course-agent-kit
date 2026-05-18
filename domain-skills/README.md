# Domain Skills

Reusable browser-harness playbooks live here.

Currently included:

- `asc.iitb.ac.in/`: IIT Bombay ASC navigation, course information, running courses, restrictions, and grading stats.

To use with browser-harness domain skills, symlink the site folder into browser-harness:

```bash
mkdir -p browser-harness/agent-workspace/domain-skills
ln -s ../../../domain-skills/asc.iitb.ac.in \
  browser-harness/agent-workspace/domain-skills/asc.iitb.ac.in
```
