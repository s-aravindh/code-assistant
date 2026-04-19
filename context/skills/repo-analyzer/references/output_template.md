# Output Templates for Repo Analyzer

Write each file below after completing your analysis. Replace the bracketed placeholders with real values.

---

## context/project_context.md

```markdown
# [Project Name]

[One sentence describing what the project does.]

## Stack

- Language: [e.g. Python 3.12]
- Framework: [e.g. FastAPI / Django / none]
- Database: [e.g. PostgreSQL 15 / SQLite / none]
- Test runner: [e.g. pytest / unittest / jest]
- Linter/formatter: [e.g. ruff, black / eslint, prettier]
- Package manager: [e.g. uv / pip / npm / cargo]

## Structure

[3-5 bullet points describing the key folders and what they contain.]

## Development workflow

[2-4 bullet points: how to run tests, how to start the dev server, branch strategy if evident.]
```

---

## context/memory.md

```markdown
# Project Memory

[List 3-8 key facts the agent must always remember. Examples:]
- [Database engine and version]
- [Authentication method]
- [Branch protection rules]
- [Any non-obvious conventions found in the code]
```

---

## context/system_prompt.md

```markdown
You are an expert [language] developer assisting with [Project Name].

[2-3 sentences describing the agent's role, tone, and key priorities for this project.]

Always:
- [convention 1 inferred from code]
- [convention 2 inferred from code]
```

---

## context/commands.json

```json
{
  "safe_commands": [
    "cat", "ls", "pwd", "echo", "grep", "find", "head", "tail",
    "git status", "git log", "git diff",
    "[add project-specific read-only commands here]"
  ],
  "destructive_commands": [
    "rm", "rmdir", "mv", "git reset", "git clean", "git push --force",
    "[add project-specific destructive commands here]"
  ]
}
```

---

## context/agent_settings.json

```json
{
  "markdown": true,
  "confirmation_tools": ["run_shell"],
  "unknown_command_behavior": "ask"
}
```
