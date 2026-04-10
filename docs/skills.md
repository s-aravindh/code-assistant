# Skills

Skills give the agent reusable domain knowledge loaded from markdown files.

## How it works

The agent searches for skills in:

1. `<repo>/context/skills/` — repo-level skills (loaded first)
2. `<your-project>/context/skills/` — project skills (override repo skills by name)

Each skill is a folder containing a `SKILL.md` file.

```
context/
└── skills/
    ├── python-best-practices/
    │   └── SKILL.md
    └── data-pipeline/
        └── SKILL.md
```

---

## Adding a skill

1. Create a folder under `context/skills/` with a descriptive name.
2. Add a `SKILL.md` file inside it.

```bash
mkdir -p context/skills/my-skill
touch context/skills/my-skill/SKILL.md
```

---

## SKILL.md format

```markdown
---
name: my-skill
description: Short description so the agent knows when to apply this skill.
---

# My Skill

The detailed guidelines, patterns, or rules the agent should follow
when this skill is relevant.

## Examples

- Prefer X over Y
- Always validate inputs at the boundary
```

### Frontmatter fields

| Field | Required | Description |
|---|---|---|
| `name` | Yes | Unique skill identifier. Project skills override repo skills with the same name. |
| `description` | Yes | One-line summary. The agent uses this to decide when the skill applies. |

---

## Built-in skills (repo defaults)

| Name | Description |
|---|---|
| `python-best-practices` | PEP 8 style, type hints, docstrings, clean imports |
| `code-review` | Review checklist: correctness, readability, security, tests |

---

## Overriding a built-in skill

Create `context/skills/python-best-practices/SKILL.md` in your project. Your version takes precedence over the repo default.
