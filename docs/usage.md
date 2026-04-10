# Usage

## Installation

```bash
git clone https://github.com/your-org/code-assistant
cd code-assistant
uv sync
```

## Running

```bash
# Use current directory as the project
uv run myassistant

# Specify a project directory
uv run myassistant --project /path/to/your/project

# Choose a model
uv run myassistant --model anthropic/claude-opus-4-5
uv run myassistant --model openai/gpt-4o
```

### Environment variables

Set your API key before running:

```bash
export ANTHROPIC_API_KEY=sk-ant-...   # Anthropic models
export OPENAI_API_KEY=sk-...          # OpenAI models
```

## Interacting

Type your message and press **Enter**. The agent reads and writes files, runs shell commands, and searches code.

### Slash commands

| Command | Description |
|---|---|
| `/help` | Show available slash commands |
| `/clear` | Clear the conversation history |
| `/memory` | Show the agent's stored user memories |
| `/model` | Switch the active model mid-session |
| `/exit` or `/quit` | Exit the assistant |

Commands are configured in `context/commands.json` — see [configuration.md](configuration.md).

## Human-in-the-loop approvals

When the agent wants to run a destructive command (e.g. `rm`, `git reset --hard`), a confirmation dialog appears. You can:

- **Approve** — the command runs
- **Reject** — the agent is told why and can suggest an alternative

Safe read-only commands (e.g. `cat`, `ls`, `grep`) run automatically without prompting.

This behaviour is configurable; see [configuration.md](configuration.md#agent_settingsjson).
