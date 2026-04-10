---
name: code-review
description: Guidelines for reviewing code changes and explaining modifications to the user.
---

## Code Review Guidelines

When reviewing or explaining code changes, follow this approach.

### Before Making Changes

- Read the file first to understand the existing structure
- Identify the minimal change needed — avoid unrelated refactors
- Check how the code is used (callers, tests) before modifying

### When Explaining Changes

- State what changed and why (purpose/reason)
- Point out any side effects or related areas that may need updating
- Highlight any breaking changes to interfaces or APIs

### Code Quality Checks

- Ensure tests cover the new/changed behaviour
- Check for duplicated logic that could be consolidated
- Verify error cases are handled
- Confirm resource cleanup (files, connections) is correct

### Review Checklist

1. Does the change solve the stated problem?
2. Are edge cases handled?
3. Is existing test coverage maintained or improved?
4. Are function/variable names clear and consistent with the codebase?
5. Is there any new technical debt introduced?
