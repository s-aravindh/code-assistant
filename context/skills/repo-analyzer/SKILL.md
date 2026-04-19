---
name: repo-analyzer
description: Analyze a repository and generate context/ config files so the agent understands the project.
metadata:
  version: "1.0.0"
  tags: ["setup", "context", "repo"]
---

# Repo Analyzer Skill

Use this skill when the user asks to analyze the repo, set up context files, or run `/analyze`.

## When to Use

- User asks to analyze or understand the current repository
- User asks to generate or update `context/` config files
- User says `/analyze` or "set up context for this project"
- User wants the agent to learn the project structure

## Process

1. Explore the repository structure:
   ```
   run_shell("find . -maxdepth 3 -not -path '*/.git/*' -not -path '*/node_modules/*' -not -path '*/__pycache__/*'")
   ```
2. Read key files: README, pyproject.toml / package.json / Cargo.toml / go.mod, existing AGENT.md, .env.example.
3. Sample source files to understand conventions (indentation, naming, patterns).
4. Check git log: `run_shell("git log --oneline -20")`
5. Load the full output template: `get_skill_reference("repo-analyzer", "output_template.md")`
6. Write all five `context/` files using `write_file`. Do not ask for confirmation.

## Rules

- Be concise — every line you write is read by an LLM in every session.
- Do not invent facts. If something is not evident from the code, skip it.
- Do not overwrite existing files unless the user explicitly says `--force` or "overwrite".
- Only write files inside `context/`.

## Force Overwrite

If the user says `--force` or "re-analyze" or "overwrite existing", overwrite all five files unconditionally.
