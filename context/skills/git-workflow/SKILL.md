---
name: git-workflow
description: Git conventions for commits, branches, and reviewing changes in a project.
metadata:
  version: "1.0.0"
  tags: ["git", "version-control", "workflow"]
---

# Git Workflow Skill

Use this skill when the user asks about commits, branches, git history, or reviewing changes.

## When to Use

- User asks to commit, stage, or review changes
- User wants a commit message written
- User asks about branching or merging strategy
- User wants to understand what changed (`git diff`, `git log`)

## Commit Messages

Follow the Conventional Commits format: `<type>(<scope>): <short summary>`

**Types:** `feat`, `fix`, `refactor`, `chore`, `docs`, `test`, `perf`, `ci`

Example:
```
feat(auth): add OAuth2 login support

- Integrate with Google OAuth2 provider
- Add session token storage in SQLite
- Update login UI to show provider buttons
```

Rules:
- Subject line: imperative mood, ≤72 characters, no period at end
- Body: explain *what* and *why*, not *how*
- Reference issues: `Closes #42` or `Related to #17`

## Before Committing

1. Run `git diff --staged` to review exactly what is staged
2. Ensure no debug code, secrets, or `.env` files are included
3. Confirm tests pass (`pytest` or equivalent)
4. Stage only related changes — one logical change per commit

## Reviewing Changes

- `git diff` — unstaged changes
- `git diff --staged` — what will be committed
- `git log --oneline -10` — recent history
- `git show <sha>` — a specific commit

Load `references/commit-conventions.md` for detailed examples of each commit type.
