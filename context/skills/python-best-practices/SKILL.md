---
name: python-best-practices
description: Python coding conventions and best practices for writing clean, maintainable code.
---

## Python Best Practices

When writing or reviewing Python code, apply the following guidelines.

### Code Style

- Line length: 120 characters maximum (unless project specifies otherwise)
- Follow PEP 8 naming: `snake_case` functions/variables, `PascalCase` classes, `UPPER_CASE` constants
- Use f-strings for string formatting (not `.format()` or `%`)
- Prefer explicit `None` checks: `if x is None` not `if not x`

### Type Hints

- Add type hints to all function arguments and return types
- Use `X | Y` union syntax (Python 3.10+) instead of `Optional[X]`
- Use `list[str]`, `dict[str, int]` (lowercase, Python 3.9+)

### Functions and Classes

- Keep functions small and single-purpose (one thing per function)
- Docstrings must include Args, Returns sections (Google style)
- Raise specific exceptions, not bare `Exception`
- Use `dataclass` or `pydantic` for data containers

### Imports

- Group: stdlib → third-party → local, separated by blank lines
- Never use wildcard imports (`from x import *`)
- Keep imports at the top of the file

### Common Pitfalls to Avoid

- Don't use mutable default arguments: `def f(x=[])` → `def f(x=None): if x is None: x = []`
- Prefer `Path` over `os.path` for filesystem operations
- Use `with` statements for file/resource management
- Avoid `global` and `nonlocal` unless absolutely necessary
