# Python Style Guide Reference

Load this when you need detailed examples and patterns beyond the quick guidelines.

## Naming Conventions

| Kind         | Convention       | Example                          |
|--------------|------------------|----------------------------------|
| Variable     | `snake_case`     | `user_count`, `file_path`        |
| Function     | `snake_case`     | `get_user()`, `parse_config()`   |
| Class        | `PascalCase`     | `UserManager`, `HttpClient`      |
| Constant     | `UPPER_SNAKE`    | `MAX_RETRIES`, `DEFAULT_TIMEOUT` |
| Private      | `_leading`       | `_cache`, `_validate()`          |
| Type alias   | `PascalCase`     | `UserId = int`                   |

## Type Hints — Patterns

```python
# Prefer X | Y over Optional[X] (Python 3.10+)
def find(id: int) -> User | None: ...

# Use built-in generics (Python 3.9+)
def process(items: list[str]) -> dict[str, int]: ...

# Callable
from collections.abc import Callable
Handler = Callable[[str, int], bool]

# TypeVar for generics
from typing import TypeVar
T = TypeVar("T")
def first(items: list[T]) -> T | None:
    return items[0] if items else None
```

## Error Handling Patterns

```python
# Raise specific, informative exceptions
raise ValueError(f"Invalid timeout {timeout!r}: must be > 0")

# Use contextlib for cleanup
from contextlib import suppress
with suppress(FileNotFoundError):
    path.unlink()

# Chain exceptions to preserve context
try:
    data = json.loads(raw)
except json.JSONDecodeError as exc:
    raise ConfigError("Invalid config JSON") from exc
```

## Dataclasses vs Pydantic

```python
# Dataclass — plain data container, no validation
from dataclasses import dataclass, field

@dataclass
class Point:
    x: float
    y: float
    tags: list[str] = field(default_factory=list)

# Pydantic — when you need validation/serialisation
from pydantic import BaseModel

class Config(BaseModel):
    host: str
    port: int = 8080
    tags: list[str] = []
```

## Pathlib Over os.path

```python
# Good
from pathlib import Path
config = Path("~/.config/app.json").expanduser()
content = config.read_text(encoding="utf-8")

# Avoid
import os
config = os.path.expanduser("~/.config/app.json")
with open(config) as f:
    content = f.read()
```

## Context Managers for Resources

```python
# Files
with open(path, encoding="utf-8") as f:
    data = f.read()

# Multiple at once (Python 3.10+)
with open(src) as r, open(dst, "w") as w:
    w.write(r.read())
```

## Common Anti-Patterns to Avoid

```python
# BAD: mutable default argument
def append(item, lst=[]):  # lst is shared across all calls!
    lst.append(item)

# GOOD
def append(item, lst=None):
    if lst is None:
        lst = []
    lst.append(item)

# BAD: silent broad except
try:
    process()
except Exception:
    pass  # swallows KeyboardInterrupt, SystemExit, etc.

# GOOD
try:
    process()
except (ValueError, OSError) as exc:
    logger.warning("process failed: %s", exc)
```
