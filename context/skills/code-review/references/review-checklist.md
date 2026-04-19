# Code Review Checklist

Load this reference when doing a thorough review of a change.

## Correctness
- [ ] Does the code do what the task/ticket requires?
- [ ] Are all edge cases handled (empty input, None, zero, large values)?
- [ ] Is error handling present and specific (no bare `except Exception`)?
- [ ] Are external calls (DB, API, filesystem) guarded for failures?

## Design
- [ ] Is the change minimal — does it avoid unrelated refactors?
- [ ] Is there duplicated logic that could be consolidated?
- [ ] Does it introduce new abstractions only when justified?
- [ ] Are interfaces (function signatures, class APIs) backward-compatible?

## Readability
- [ ] Are function and variable names self-describing?
- [ ] Is complex logic explained with a comment?
- [ ] Are docstrings present on public functions/classes?
- [ ] Is the code style consistent with the surrounding code?

## Tests
- [ ] Is there a test for the happy path?
- [ ] Is there a test for the key failure/edge case?
- [ ] Do existing tests still pass?
- [ ] Is test coverage maintained or improved?

## Security (OWASP-aware)
- [ ] No secrets or credentials in code or comments
- [ ] User input is validated before use
- [ ] File paths are not constructed from untrusted input without sanitisation
- [ ] SQL/shell commands don't use string interpolation with user data

## Performance
- [ ] No N+1 query patterns introduced
- [ ] No unnecessary in-memory copies of large data
- [ ] I/O operations are not inside tight loops
