# Configuration

myassistant reads configuration from a `context/` folder. It looks in two places, using the first it finds:

1. `<your-project>/context/` — project-level config (checked first)
2. `<repo>/context/` — repo-level defaults (fallback)

Create a `context/` folder in your project to override any default.

---

## context/system_prompt.md

The agent's base persona and behavioural guidelines.

```markdown
You are an expert coding assistant. You write clean, minimal, readable code.
Always explain what you changed and why.
```

If this file is absent, the repo default is used.

---

## context/project_context.md

Describes the project the agent is working in. The agent includes this in every session.

```markdown
# My API Service

- Python 3.12, FastAPI, PostgreSQL 15
- Tests are in tests/ and run with `pytest`
- All endpoints require JWT authentication
```

---

## context/memory.md

Persistent notes the agent reads at startup. Add facts, decisions, and conventions here so the agent always knows them.

```markdown
# Project Memory

- Use `ruff` for linting, not flake8
- The main branch is protected — always branch from `main`
- Database migrations are managed with Alembic
```

---

## context/commands.json

Classifies shell commands as **safe** (auto-approved) or **destructive** (requires confirmation).

Plain English — no regex needed.

```json
{
  "safe_commands": [
    "cat", "ls", "pwd", "echo", "grep", "find", "head", "tail",
    "git status", "git log", "git diff"
  ],
  "destructive_commands": [
    "rm", "rmdir", "mv", "git reset", "git clean",
    "drop table", "truncate"
  ]
}
```

A command matches if the listed word appears as a whole word in the command string (e.g. `rm` matches `rm -rf` but not `chmod`).

---

## context/agent_settings.json

Controls agent behaviour.

```json
{
  "markdown": true,
  "confirmation_tools": ["run_shell"],
  "unknown_command_behavior": "ask",
  "model": "anthropic/claude-opus-4-5"
}
```

| Key | Values | Description |
|---|---|---|
| `markdown` | `true` / `false` | Render responses as markdown |
| `confirmation_tools` | list of tool names | Which tools trigger HITL checks |
| `unknown_command_behavior` | `"ask"` / `"allow"` / `"reject"` | What to do if a command is neither safe nor destructive |
| `model` | `"provider/model-id"` | Default model (overridden by `--model` flag) |

---

## AGENT.md (legacy)

If your project already has an `AGENT.md` file in its root, the agent reads it automatically and merges it with `context/project_context.md`. Prefer `context/project_context.md` for new projects.
