# Conventional Commits Reference

## Commit Types — When to Use Each

| Type       | Use when…                                                      |
|------------|----------------------------------------------------------------|
| `feat`     | Adding new user-visible functionality                          |
| `fix`      | Fixing a bug (include issue ref if applicable)                 |
| `refactor` | Restructuring code without changing behaviour                  |
| `chore`    | Tooling, dependencies, CI, build scripts                       |
| `docs`     | Documentation only changes                                     |
| `test`     | Adding or fixing tests                                         |
| `perf`     | A code change that improves performance                        |
| `ci`       | Changes to CI/CD pipeline files                                |
| `revert`   | Reverting a previous commit                                    |

## Examples by Type

### feat
```
feat(api): add pagination to /users endpoint

Adds cursor-based pagination. Clients pass `cursor` and `limit`
query params. Defaults: limit=20, max=100.

Closes #88
```

### fix
```
fix(auth): prevent session token reuse after logout

Tokens were not invalidated in the DB on logout, allowing reuse
within the token TTL window.

Fixes #102
```

### refactor
```
refactor(storage): extract get_default_db_path to its own function

No behaviour change. Improves testability by making the path
resolution independently mockable.
```

### chore
```
chore(deps): bump anthropic from 0.74 to 0.75
```

### test
```
test(auth): add edge case tests for expired tokens
```

## Breaking Changes

Add `!` after the type, and a `BREAKING CHANGE:` footer:

```
feat(api)!: rename /user to /users

BREAKING CHANGE: all existing /user endpoints are now /users.
Clients must update their base URLs.
```

## Scope Guidelines

- Use the module or feature name: `auth`, `storage`, `ui`, `agent`
- Omit scope for project-wide changes
- Keep it short (one word if possible)

## Multi-File Commits

When a commit touches many files, the body should list the key changes:

```
feat(agent): add skills lazy-loading support

- Add Skills class with LocalSkills loader
- Wire skills into create_coding_agent()
- Add context/skills/ directory structure
- Update ContextLoader.get_skills() to load from both repo and project
```
