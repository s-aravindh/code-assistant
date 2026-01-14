# Mini-Claude-Code

A TUI-based agentic coding assistant powered by Agno, designed for personal use with any LLM provider.

## Features

- **Terminal-Native Interface**: Beautiful TUI built with Textual
- **Model Agnostic**: Works with Anthropic Claude, OpenAI GPT-4, Ollama, and more
- **Agentic Tools**: File operations, shell commands, Git integration, code search
- **Human-in-the-Loop**: Approval dialogs for file writes and command execution
- **Project Memory**: AGENT.md support for project-specific context
- **Streaming Responses**: Real-time response streaming from LLMs
- **Slash Commands**: Quick commands for common operations
- **Session Persistence**: SQLite-backed conversation history

## Installation

```bash
# Install with uv (recommended)
uv pip install -e .

# Or with pip
pip install -e .
```

## Quick Start

```bash
# Start in current directory
mcc

# Start in specific project
mcc /path/to/project

# Use a specific model
mcc -m openai:gpt-4o

# Show help
mcc --help
```

## Usage

### Interactive Mode

The main way to use Mini-Claude-Code is through the interactive TUI:

1. Launch `mcc` in your project directory
2. Type your questions or requests naturally
3. Press `Ctrl+Enter` to send your message
4. Review and approve file changes and commands when prompted

### Slash Commands

Use slash commands for quick actions:

- `/help` - Show available commands
- `/clear` - Clear conversation history
- `/model <name>` - Switch to a different model
- `/context` - Show current context
- `/init` - Create AGENT.md template
- `/commit` - Generate and create a git commit
- `/exit` - Exit the application

See full list with `/help`

### Keyboard Shortcuts

- `Ctrl+Enter` - Send message
- `Ctrl+C` - Exit
- `Ctrl+L` - Clear screen
- `Ctrl+Y` - Accept changes (in approval dialogs)
- `Ctrl+N` - Reject changes (in approval dialogs)

## Configuration

### Environment Variables

Set your API keys as environment variables:

```bash
export ANTHROPIC_API_KEY="your-key-here"
export OPENAI_API_KEY="your-key-here"
export MCC_PROVIDER="anthropic"  # Optional
export MCC_MODEL="claude-sonnet-4"  # Optional
```

### Configuration File

Create `~/.config/mcc/config.yaml`:

```yaml
# LLM Settings
provider: anthropic
model: anthropic:claude-sonnet-4-20250514
temperature: 0.7
max_tokens: 4096

# TUI Settings
theme: dark
show_token_count: true

# Behavior
confirm_before_write: true
confirm_before_execute: true

# Security
command_allowlist:
  - "npm test"
  - "pytest"
```

### Project-Level Configuration

Create `.mcc/config.yaml` in your project for project-specific settings.

## Project Memory (AGENT.md)

Create an `AGENT.md` file in your project root to provide context to the agent:

```bash
# Generate template
mcc
> /init
```

Example AGENT.md:

```markdown
# Project: MyApp

## Overview
REST API built with FastAPI

## Tech Stack
- Python 3.11
- FastAPI
- PostgreSQL

## Conventions
- Use type hints
- Follow PEP 8
- Async for I/O operations

## Common Commands
- `make dev` - Start server
- `make test` - Run tests
```

## Supported LLM Providers

- **Anthropic**: `anthropic:claude-sonnet-4-20250514`
- **OpenAI**: `openai:gpt-4o`, `openai:gpt-4-turbo`
- **Ollama**: `ollama:llama3.2`, `ollama:codellama`
- **OpenRouter**: `openrouter:anthropic/claude-3.5-sonnet`

## Development

```bash
# Install development dependencies
uv pip install -e ".[dev]"

# Run linter
ruff check .

# Run type checker
mypy src/

# Run tests
pytest
```

## Architecture

Mini-Claude-Code is built with:

- **Agno**: Agent framework with tool support
- **Textual**: Modern TUI framework
- **SQLite**: Local session storage
- **Typer**: CLI framework

### Tool System

The agent has access to:

- **FileToolkit**: Read, write, edit, delete files
- **ShellToolkit**: Execute shell commands
- **SearchToolkit**: Grep search and file finding
- **GitToolkit**: Git status, diff, commit, log

All write operations require user approval through HITL dialogs.

