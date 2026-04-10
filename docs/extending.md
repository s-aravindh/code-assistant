# Extending myassistant

## Overriding the system prompt

Create `context/system_prompt.md` in your project. The file completely replaces the default.

```markdown
You are a senior Go engineer helping with a microservices backend.
Always write table-driven tests.
```

---

## Adding project-specific context

Put facts about your project in `context/project_context.md`. This is merged with any existing `AGENT.md` and appended to the system prompt.

---

## Adding a custom tool

Tools are implemented as `Toolkit` subclasses using [Agno](https://docs.agno.com/tools/toolkit).

```python
from agno.tools import Toolkit

class MyTool(Toolkit):
    def __init__(self):
        super().__init__(name="my_tool")
        self.register(self.do_something)

    def do_something(self, query: str) -> str:
        """Explain to the agent what this does.

        Args:
            query (str): The input.
        Returns:
            str: The result.
        """
        return f"Result for {query}"
```

Wire it into the agent in `coding_agent.py`:

```python
tools=[CodingTool(...), MyTool()]
```

---

## Extending CodingTool

`CodingTool` lives in `src/myassistant/tools/coding_tool.py`. Add a method and register it:

```python
def my_custom_tool(self, path: str) -> str:
    """Description the agent sees."""
    ...

# Inside __init__, after existing registers:
self.register(self.my_custom_tool)
```

---

## Changing confirmation behaviour

In `context/agent_settings.json`:

```json
{
  "confirmation_tools": ["run_shell", "write_file"],
  "unknown_command_behavior": "reject"
}
```

- `confirmation_tools` — which tool names trigger HITL approval checks
- `unknown_command_behavior` — `"ask"` (default), `"allow"`, or `"reject"` for commands not listed in `commands.json`

---

## Adding custom commands

In `context/commands.json`, add words or phrases to `safe_commands` or `destructive_commands`.

```json
{
  "safe_commands": ["my-read-only-script"],
  "destructive_commands": ["deploy", "publish"]
}
```

Plain English strings — no regex. Single words are matched as whole words; phrases are matched as substrings.
