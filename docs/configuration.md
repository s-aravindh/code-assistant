# Configuration

myassistant reads configuration from a `context/` folder. It checks two locations, using the first match:

1. `<your-project>/context/` — project-level config (checked first)
2. `<repo>/context/` — repo-level defaults (fallback)

Create a `context/` folder in your project to override any default without touching the source.

---

## context/system_prompt.md

The agent's base persona and behavioural guidelines. Loaded on every session.

```markdown
You are an expert coding assistant. You write clean, minimal, readable code.
Always explain what you changed and why.
```

If absent, the repo default is used.

---

## context/project_context.md

Describes the project the agent is working in. Included in every session's context.

```markdown
# My API Service

- Python 3.12, FastAPI, PostgreSQL 15
- Tests are in tests/ and run with `pytest`
- All endpoints require JWT authentication
```

Also supports a legacy `AGENT.md` in your project root — if present it is merged with `project_context.md`.

---

## context/memory.md

Persistent notes the agent reads at startup. Add facts, decisions, and conventions here.

```markdown
# Project Memory

- Use `ruff` for linting, not flake8
- The main branch is protected — always branch from `main`
- Database migrations are managed with Alembic
```

---

## context/commands.json

Classifies shell commands as **safe** (auto-approved) or **destructive** (requires HITL confirmation).
Also defines **ignored_paths** — glob patterns the file tool will refuse to read or write.

```json
{
  "safe": ["ls", "cat", "pytest", "git status", "git diff"],
  "destructive": ["rm", "rmdir", "git reset", "git clean", "pip install"],
  "ignored_paths": [".git/**", "**/.venv/**", ".env", "**/*.key"]
}
```

**Matching rules:**
- Single-word entries match as whole words (`rm` matches `rm -rf` but not `chmod`).
- Phrase entries (containing spaces) match as literal substrings (`git reset` matches `git reset --hard`).

---

## context/agent_settings.json

Controls agent behaviour, HITL settings, and storage paths.

```json
{
  "num_history_runs": 15,
  "add_history_to_context": true,
  "read_chat_history": true,
  "read_tool_call_history": true,
  "markdown": true,
  "temperature": 0.7,
  "max_tokens": 4096,
  "confirmation_tools": ["run_shell"],
  "unknown_command_behavior": "auto_approve",
  "logs_dir": "myassistant_logs",
  "db_path": null
}
```

| Key | Default | Description |
|---|---|---|
| `num_history_runs` | `15` | Number of past runs included in context |
| `add_history_to_context` | `true` | Include run history in agent context |
| `read_chat_history` | `true` | Allow agent to read past chat messages |
| `read_tool_call_history` | `true` | Allow agent to read past tool call results |
| `markdown` | `true` | Render agent responses as markdown |
| `temperature` | `0.7` | Model sampling temperature (0.0–2.0) |
| `max_tokens` | `4096` | Maximum tokens per response |
| `confirmation_tools` | `["run_shell"]` | Tools that trigger HITL approval checks |
| `unknown_command_behavior` | `"auto_approve"` | What to do for commands not in safe/destructive lists: `"auto_approve"` or `"show_dialog"` |
| `logs_dir` | `"myassistant_logs"` | Log folder name, relative to project path |
| `db_path` | `null` | Override the SQLite DB path. `null` uses the global default (`~/.local/share/myassistant/myassistant.db`). Set to a relative path (e.g. `"context/history.db"`) for project-scoped history |

---

## context/skills/

Skills extend the agent with domain-specific knowledge. Each skill is a subdirectory containing a `SKILL.md` file.

```
context/skills/
├── code-review/
│   ├── SKILL.md
│   └── references/
│       └── review-checklist.md
├── python-best-practices/
│   ├── SKILL.md
│   └── references/
│       └── style-guide.md
└── git-workflow/
    ├── SKILL.md
    └── references/
        └── commit-conventions.md
```

`SKILL.md` requires a YAML frontmatter block with `name` and `description`:

```markdown
---
name: my-skill
description: What this skill does (shown in the agent's system prompt)
---

# My Skill

Use this skill when...
```

Skills use **lazy loading** — the agent sees skill names and descriptions upfront, then calls `get_skill_instructions` / `get_skill_reference` only when relevant, keeping the context window lean.

Project-level skills (under `<project>/context/skills/`) override repo defaults when names collide.

---

## Environment Variables

Settings that are machine/deployment-specific are set via environment variables (prefix: `MA_`). These can also be placed in a `.env` file.

| Variable | Default | Description |
|---|---|---|
| `MA_PROVIDER` | `anthropic` | Default LLM provider |
| `MA_MODEL` | `anthropic:claude-sonnet-4-20250514` | Default model string |
| `MA_TEMPERATURE` | `0.7` | Model temperature |
| `MA_MAX_TOKENS` | `4096` | Max tokens per response |
| `MA_LOG_LEVEL` | `info` | Log level (`debug`, `info`, `warning`, `error`) |
| `MA_LOG_FILE` | — | Absolute log directory path (overrides `logs_dir`) |
| `MA_LOG_MAX_SIZE_MB` | `10` | Max log file size before rotation |
| `MA_LOG_BACKUP_COUNT` | `5` | Number of rotated log files to keep |

API keys are passed directly to each provider's standard environment variable:

```bash
export ANTHROPIC_API_KEY="your-key"
export OPENAI_API_KEY="your-key"
export GROQ_API_KEY="your-key"
export OPENROUTER_API_KEY="your-key"
```

