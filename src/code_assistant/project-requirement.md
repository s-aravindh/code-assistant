# Mini-Claude-Code: Project Requirements

> A TUI-based agentic coding assistant inspired by Claude Code, designed for personal use with any LLM provider.

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Core Philosophy](#2-core-philosophy)
3. [Architecture Overview](#3-architecture-overview)
4. [Terminal User Interface (TUI) Requirements](#4-terminal-user-interface-tui-requirements)
5. [Interaction Model (Like Claude Code)](#5-interaction-model-like-claude-code)
6. [CLI Startup & Arguments](#6-cli-startup--arguments)
7. [Slash Commands (In-Chat)](#7-slash-commands-in-chat)
8. [Agent Capabilities](#8-agent-capabilities)
9. [Tool System](#9-tool-system)
10. [Memory & Context Management](#10-memory--context-management)
11. [Security & Permissions](#11-security--permissions)
12. [LLM Provider Integration](#12-llm-provider-integration)
13. [Development Workflow Integration](#13-development-workflow-integration)
14. [Configuration System](#14-configuration-system)
15. [Extensibility](#15-extensibility)
16. [Performance Requirements](#16-performance-requirements)
17. [Technical Stack](#17-technical-stack)
18. [Milestones & Phases](#18-milestones--phases)

---

## 1. Project Overview

**Mini-Claude-Code** is a terminal-based AI coding assistant that operates as an agentic pair programmer. Unlike traditional code completion tools, it understands entire codebases, executes commands, edits files, and integrates with development workflows—all within the terminal.

### Key Differentiators

- **Model Agnostic**: Works with any LLM (OpenAI, Anthropic, Ollama, local models, etc.)
- **Terminal Native**: Designed for developers who live in the terminal
- **Agentic**: Autonomous task execution with user approval gates
- **Lightweight**: Minimal dependencies, fast startup, low resource usage
- **Personal Use Focus**: Simplified setup, no enterprise complexity

---

## 2. Core Philosophy

### Design Principles

1. **User Control First**: Never modify files without explicit approval
2. **Transparency**: Always show what the agent intends to do before doing it
3. **Incremental Trust**: Start with more confirmations, allow users to grant broader permissions
4. **Context Awareness**: Understand the full project, not just the current file
5. **Tool Composability**: Work seamlessly with existing CLI tools and workflows
6. **Fail Gracefully**: Handle errors without crashing, provide actionable feedback

---

## 3. Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        TUI Layer (Textual)                       │
│  ┌─────────────┐  ┌──────────────┐  ┌─────────────────────────┐ │
│  │ Input Panel │  │ Output Panel │  │ Status/Context Panel    │ │
│  └─────────────┘  └──────────────┘  └─────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────────┐
│                      Agent Core Layer                            │
│  ┌─────────────┐  ┌──────────────┐  ┌─────────────────────────┐ │
│  │ Conversation│  │ Tool Router  │  │ Permission Manager      │ │
│  │ Manager     │  │              │  │                         │ │
│  └─────────────┘  └──────────────┘  └─────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────────┐
│                        Tool Layer                                │
│  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────────────┐ │
│  │  Read  │ │ Write  │ │ Bash   │ │ Search │ │ Git Operations │ │
│  │  File  │ │ File   │ │ Execute│ │ (grep) │ │                │ │
│  └────────┘ └────────┘ └────────┘ └────────┘ └────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────────┐
│                      LLM Provider Layer                          │
│  ┌─────────────┐  ┌──────────────┐  ┌─────────────────────────┐ │
│  │ OpenAI      │  │ Anthropic    │  │ Ollama / Local Models   │ │
│  └─────────────┘  └──────────────┘  └─────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────────┐
│                      Memory & Storage Layer                      │
│  ┌─────────────┐  ┌──────────────┐  ┌─────────────────────────┐ │
│  │ Conversation│  │ Project      │  │ Global User             │ │
│  │ History     │  │ Memory       │  │ Preferences             │ │
│  └─────────────┘  └──────────────┘  └─────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

---

## 4. Terminal User Interface (TUI) Requirements

### 4.1 Layout Components

| Component | Description |
|-----------|-------------|
| **Input Panel** | Multi-line input area for user prompts with syntax highlighting |
| **Output Panel** | Scrollable area displaying conversation, code diffs, and results |
| **Status Bar** | Shows current model, token usage, active permissions, working directory |
| **Context Panel** | (Optional) Shows files in context, recent tool calls |
| **Command Palette** | Quick access to slash commands and actions |

### 4.2 TUI Features

- **Rich Markdown Rendering**: Display formatted responses with syntax-highlighted code blocks
- **Diff Visualization**: Show file changes with unified diff format (additions in green, deletions in red)
- **Progress Indicators**: Spinner/progress bar for long-running operations
- **Split Views**: Option to show code preview alongside conversation
- **Scrollback Buffer**: Maintain history of the current session
- **Copy Support**: Easy copying of code blocks and responses
- **Theme Support**: Light/dark themes, customizable colors
- **Responsive Layout**: Adapt to terminal size changes

### 4.3 Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Enter` | Send message (single line mode) |
| `Ctrl+Enter` | Send message (multi-line mode) |
| `Ctrl+C` | Cancel current operation / Exit |
| `Ctrl+L` | Clear screen |
| `Ctrl+K` | Open command palette |
| `Ctrl+R` | Retry last message |
| `Ctrl+Y` | Accept proposed changes |
| `Ctrl+N` | Reject proposed changes |
| `Ctrl+D` | Toggle diff view |
| `Tab` | Autocomplete file paths / commands |
| `↑/↓` | Navigate history |
| `Esc` | Cancel current input / Close dialogs |

---

## 5. Interaction Model (Like Claude Code)

### 5.1 How It Works

Mini-Claude-Code is a **terminal-based chatbot**. You launch it, and it drops you into an interactive chat session where you can naturally converse with the AI about your code.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  mini-claude-code                                                            │
│                                                                              │
│  ╭─ Welcome to Mini-Claude-Code ─────────────────────────────────────────╮  │
│  │ Working directory: /Users/dev/my-project                              │  │
│  │ Model: claude-3-5-sonnet • Provider: anthropic                        │  │
│  │ Type your message and press Enter. Use /help for commands.            │  │
│  ╰───────────────────────────────────────────────────────────────────────╯  │
│                                                                              │
│  > what does this project do?                                                │
│                                                                              │
│  I'll analyze the codebase to understand what this project does.             │
│                                                                              │
│  ● Reading package.json...                                                   │
│  ● Reading src/index.ts...                                                   │
│  ● Reading README.md...                                                      │
│                                                                              │
│  This is a **REST API server** built with Express.js that provides:          │
│  - User authentication (JWT-based)                                           │
│  - CRUD operations for blog posts                                            │
│  - File upload handling                                                      │
│  ...                                                                         │
│                                                                              │
│  > add a health check endpoint                                               │
│                                                                              │
│  I'll add a health check endpoint to your API.                               │
│                                                                              │
│  ╭─ Proposed Changes ────────────────────────────────────────────────────╮  │
│  │ src/routes/health.ts (new file)                                       │  │
│  │ ┌────────────────────────────────────────────────────────────────────┐│  │
│  │ │ + import { Router } from 'express';                                ││  │
│  │ │ +                                                                   ││  │
│  │ │ + const router = Router();                                         ││  │
│  │ │ +                                                                   ││  │
│  │ │ + router.get('/health', (req, res) => {                            ││  │
│  │ │ +   res.json({ status: 'ok', timestamp: Date.now() });             ││  │
│  │ │ + });                                                               ││  │
│  │ │ +                                                                   ││  │
│  │ │ + export default router;                                           ││  │
│  │ └────────────────────────────────────────────────────────────────────┘│  │
│  ╰───────────────────────────────────────────────────────────────────────╯  │
│                                                                              │
│  Apply changes? [y]es / [n]o / [e]dit                                        │
│  > y                                                                         │
│                                                                              │
│  ✓ Created src/routes/health.ts                                              │
│  ✓ Updated src/index.ts                                                      │
│                                                                              │
│  > _                                                                         │
│                                                                              │
│ ─────────────────────────────────────────────────────────────────────────── │
│ claude-3-5-sonnet │ 1,234 tokens │ ~/my-project │ /help for commands        │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 5.2 Conversation Flow

The interaction is **conversational and continuous**:

1. **Launch**: Run `mcc` in your project directory
2. **Chat**: Type naturally, ask questions, give instructions
3. **Agent Acts**: The AI reads files, searches code, proposes changes
4. **Review**: You approve/reject/modify proposed changes
5. **Continue**: Keep chatting, building on context
6. **Exit**: Type `/exit` or `Ctrl+C` when done

```
$ cd my-project
$ mcc

> explain the authentication flow

[Agent reads relevant files and explains]

> there's a bug where tokens don't expire, fix it

[Agent proposes changes]

Apply changes? [y]es / [n]o / [e]dit: y

> now add tests for the fix

[Agent generates tests]

> /exit
Goodbye! Session saved.
```

### 5.3 Input Modes

| Mode | How to Use | When |
|------|------------|------|
| **Single-line** | Type and press `Enter` | Quick questions, simple commands |
| **Multi-line** | Press `Ctrl+Enter` to send, `Enter` for newlines | Code snippets, detailed instructions |
| **Paste Mode** | Auto-detected on paste | Pasting code blocks |

### 5.4 Response Handling

The agent streams responses in real-time:

```
> explain this function

● Thinking...
● Reading src/utils/parser.ts...

This function `parseConfig` does the following:
[response streams in real-time as it's generated]
```

### 5.5 Approval Workflow

When the agent wants to make changes, it shows a preview and asks for approval:

```
╭─ Proposed Changes ─────────────────────────────────────────────╮
│                                                                 │
│ 📄 src/config.ts (modified)                                     │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ @@ -15,6 +15,10 @@                                          │ │
│ │   export const config = {                                   │ │
│ │     port: process.env.PORT || 3000,                         │ │
│ │ +   timeout: process.env.TIMEOUT || 5000,                   │ │
│ │ +   retries: process.env.RETRIES || 3,                      │ │
│ │   };                                                        │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                                                                 │
│ 📄 src/api/client.ts (modified)                                 │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ @@ -8,7 +8,9 @@                                             │ │
│ │ - const response = await fetch(url);                        │ │
│ │ + const response = await fetch(url, {                       │ │
│ │ +   timeout: config.timeout,                                │ │
│ │ + });                                                       │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                                                                 │
╰─────────────────────────────────────────────────────────────────╯

Apply changes? [y]es / [n]o / [e]dit / [a]ll / [s]kip file
```

| Option | Key | Action |
|--------|-----|--------|
| Yes | `y` | Apply all proposed changes |
| No | `n` | Reject all changes, continue conversation |
| Edit | `e` | Open changes in $EDITOR for manual editing |
| All | `a` | Apply all and auto-approve future changes this session |
| Skip | `s` | Skip current file, continue with others |

### 5.6 Command Execution Approval

When the agent wants to run commands:

```
╭─ Command to Execute ───────────────────────────────────────────╮
│                                                                 │
│  $ npm test                                                     │
│                                                                 │
│  This will run the test suite to verify the changes.            │
│                                                                 │
╰─────────────────────────────────────────────────────────────────╯

Run command? [y]es / [n]o / [e]dit
```

---

## 6. CLI Startup & Arguments

### 6.1 Basic Startup

```bash
# Start in current directory (most common)
mcc

# Start in specific project
mcc /path/to/project

# Resume last conversation
mcc --continue
mcc -c

# Start with initial prompt (still interactive after)
mcc "explain this codebase"
```

### 6.2 CLI Arguments

These are **startup options**, not per-message flags:

| Argument | Short | Description |
|----------|-------|-------------|
| `[path]` | | Project directory (default: current) |
| `[prompt]` | | Initial message to send on startup |
| `--continue` | `-c` | Resume the last conversation |
| `--model` | `-m` | Use specific model |
| `--provider` | | Use specific provider |
| `--config` | | Custom config file |
| `--verbose` | `-v` | Verbose logging |
| `--version` | `-V` | Show version |
| `--help` | `-h` | Show help |

### 6.3 Non-Interactive Mode (Scripting)

For CI/CD and scripting, use `--print` mode:

```bash
# Single response, then exit
mcc --print "what files have TODO comments"

# Pipe input
cat error.log | mcc --print "explain this error"

# Use in scripts
SUMMARY=$(mcc --print "summarize recent changes" --model gpt-4)
```

| Flag | Description |
|------|-------------|
| `--print`, `-p` | Non-interactive: respond once and exit |
| `--yes`, `-y` | Auto-approve all changes (dangerous!) |
| `--dry-run` | Show what would change without applying |
| `--output` | Output format: `text`, `json`, `markdown` |

### 6.4 Examples

```bash
# Daily workflow
cd my-project
mcc                          # Start chatting

# Quick question
mcc "what does the auth middleware do"

# Resume where you left off
mcc -c

# Use a different model for complex task
mcc -m gpt-4-turbo "refactor the database layer"

# CI/CD: Generate changelog
mcc -p "generate changelog for commits since last tag" > CHANGELOG.md

# CI/CD: Code review
git diff main | mcc -p "review these changes"
```

---

## 7. Slash Commands (In-Chat)

| Command | Description |
|---------|-------------|
| `/help` | Show available commands |
| `/clear` | Clear conversation history |
| `/compact` | Summarize conversation to reduce context |
| `/context` | Show current context (files, tokens used) |
| `/model <name>` | Switch to a different model |
| `/add <file>` | Add file(s) to context |
| `/remove <file>` | Remove file(s) from context |
| `/diff` | Show pending file changes |
| `/apply` | Apply all pending changes |
| `/reject` | Reject all pending changes |
| `/undo` | Undo last applied change |
| `/save` | Save conversation to file |
| `/load <file>` | Load conversation from file |
| `/config` | Show/edit configuration |
| `/memory` | Show/manage memory entries |
| `/cost` | Show token usage and estimated cost |
| `/exit` or `/quit` | Exit the application |
| `/init` | Initialize project memory (AGENT.md) |
| `/review` | Review current changes in git |
| `/commit` | Generate commit message and commit |
| `/bug <description>` | Start debugging workflow |
| `/test` | Generate tests for recent changes |

---

## 8. Agent Capabilities

### 8.1 Codebase Understanding

- **Project Structure Analysis**: Map and understand the entire codebase
- **Dependency Detection**: Identify and understand project dependencies
- **Language Detection**: Auto-detect programming languages and frameworks
- **Pattern Recognition**: Learn coding patterns and conventions from the codebase
- **Symbol Resolution**: Understand imports, exports, and cross-file references

### 8.2 Code Operations

| Capability | Description |
|------------|-------------|
| **Read Files** | Read any file in the project |
| **Write Files** | Create or overwrite files (with approval) |
| **Edit Files** | Make targeted edits using search/replace or line-based edits |
| **Multi-file Edits** | Coordinate changes across multiple files |
| **Create Directories** | Create directory structures as needed |
| **Delete Files** | Remove files (with approval) |

### 8.3 Command Execution

- **Shell Commands**: Execute bash/shell commands
- **Build Commands**: Run build tools (npm, cargo, make, etc.)
- **Test Runners**: Execute test suites
- **Linters/Formatters**: Run code quality tools
- **Custom Scripts**: Execute project-specific scripts

### 8.4 Code Intelligence

- **Semantic Search**: Find code by meaning, not just text
- **Code Explanation**: Explain what code does in natural language
- **Error Diagnosis**: Analyze errors and suggest fixes
- **Refactoring Suggestions**: Identify improvement opportunities
- **Security Analysis**: Detect potential security issues
- **Performance Analysis**: Identify performance bottlenecks

### 8.5 Code Generation

- **Feature Implementation**: Implement features from descriptions
- **Boilerplate Generation**: Generate common code patterns
- **Test Generation**: Create unit, integration, and e2e tests
- **Documentation Generation**: Generate docstrings, README, API docs
- **Type Generation**: Generate type definitions and interfaces

---

## 9. Tool System

### 9.1 Core Tools

#### File Operations

```yaml
read_file:
  description: Read contents of a file
  parameters:
    - path: string (required)
    - encoding: string (default: utf-8)
    - line_start: int (optional)
    - line_end: int (optional)
  requires_approval: false

write_file:
  description: Write content to a file
  parameters:
    - path: string (required)
    - content: string (required)
    - create_directories: bool (default: true)
  requires_approval: true

edit_file:
  description: Make targeted edits to a file
  parameters:
    - path: string (required)
    - edits: array of {search: string, replace: string}
  requires_approval: true

delete_file:
  description: Delete a file
  parameters:
    - path: string (required)
  requires_approval: true
```

#### Search Operations

```yaml
grep_search:
  description: Search for patterns in files
  parameters:
    - pattern: string (required)
    - path: string (default: ".")
    - include: string (file glob pattern)
    - exclude: string (file glob pattern)
    - case_sensitive: bool (default: true)
    - max_results: int (default: 100)
  requires_approval: false

semantic_search:
  description: Search code by meaning
  parameters:
    - query: string (required)
    - path: string (default: ".")
    - file_types: array of strings
    - max_results: int (default: 10)
  requires_approval: false

find_files:
  description: Find files by name pattern
  parameters:
    - pattern: string (required)
    - path: string (default: ".")
  requires_approval: false
```

#### Command Execution

```yaml
bash_execute:
  description: Execute a shell command
  parameters:
    - command: string (required)
    - working_directory: string (default: project root)
    - timeout: int (default: 300 seconds)
    - background: bool (default: false)
  requires_approval: true (configurable allowlist)
```

#### Git Operations

```yaml
git_status:
  description: Get git status
  requires_approval: false

git_diff:
  description: Show git diff
  parameters:
    - staged: bool (default: false)
    - file: string (optional)
  requires_approval: false

git_commit:
  description: Create a git commit
  parameters:
    - message: string (required)
    - files: array of strings (optional, default: all staged)
  requires_approval: true

git_log:
  description: Show git history
  parameters:
    - count: int (default: 10)
    - file: string (optional)
  requires_approval: false
```

### 9.2 Tool Execution Flow

```
User Request → Agent Plans Tools → Show Plan → User Approval → Execute → Show Results
                     │                              │
                     │                              ├─ Approved: Execute
                     │                              ├─ Rejected: Skip
                     │                              └─ Modified: Execute modified
                     │
                     └─ Auto-approved tools (read operations) execute immediately
```

---

## 10. Memory & Context Management

### 10.1 Memory Tiers

| Tier | Location | Scope | Purpose |
|------|----------|-------|---------|
| **Global User Memory** | `~/.config/mini-claude-code/memory.md` | All projects | Personal preferences, coding style |
| **Project Memory** | `<project>/AGENT.md` | Current project | Project conventions, architecture decisions |
| **Local Project Memory** | `<project>/.mini-claude-code/memory.md` | Current project (gitignored) | Personal project notes |
| **Session Memory** | In-memory | Current session | Conversation context |

### 10.2 AGENT.md Structure

```markdown
# Project: MyApp

## Overview
Brief description of the project.

## Tech Stack
- Python 3.11
- FastAPI
- PostgreSQL
- React (frontend)

## Conventions
- Use type hints everywhere
- Follow PEP 8
- Use async/await for I/O operations

## Architecture
- `/src/api` - API endpoints
- `/src/models` - Database models
- `/src/services` - Business logic

## Common Commands
- `make dev` - Start development server
- `make test` - Run tests
- `make lint` - Run linters

## Notes
- Database migrations are in `/migrations`
- Environment variables in `.env.example`
```

### 10.3 Context Window Management

- **Token Counting**: Track token usage in real-time
- **Context Prioritization**: Keep most relevant content in context
- **Automatic Compaction**: Summarize old messages when approaching limit
- **File Content Caching**: Smart caching of file contents
- **Incremental Updates**: Only send changed portions when possible

### 10.4 Conversation History

- **Persistence**: Save conversations to disk
- **Resume**: Continue previous conversations
- **Search**: Search through past conversations
- **Export**: Export conversations to markdown/JSON

---

## 11. Security & Permissions

### 11.1 Permission Model

```yaml
permission_levels:
  read:
    description: Read files and run safe commands
    auto_approve: true
    includes:
      - read_file
      - grep_search
      - find_files
      - git_status
      - git_diff
      - git_log

  write:
    description: Modify files
    auto_approve: false
    includes:
      - write_file
      - edit_file
      - delete_file

  execute:
    description: Run shell commands
    auto_approve: false
    includes:
      - bash_execute

  git_write:
    description: Git write operations
    auto_approve: false
    includes:
      - git_commit
      - git_push
      - git_branch
```

### 11.2 Allowlists & Blocklists

```yaml
# Commands that can auto-execute
command_allowlist:
  - "npm test"
  - "npm run lint"
  - "pytest"
  - "make test"
  - "cargo test"
  - "go test"

# Commands that are always blocked
command_blocklist:
  - "rm -rf /"
  - "sudo rm"
  - ":(){ :|:& };:"
  - patterns: ["curl.*|.*sh", "wget.*|.*sh"]

# Paths that cannot be modified
protected_paths:
  - "~/.ssh"
  - "~/.gnupg"
  - "/etc"
  - ".env"
  - "*.pem"
  - "*.key"
```

### 11.3 Sandboxing (Future)

- **Filesystem Isolation**: Restrict access to project directory
- **Network Isolation**: Control network access for commands
- **Resource Limits**: CPU, memory, and time limits for commands

---

## 12. LLM Provider Integration

### 12.1 Supported Providers

| Provider | Models | Features |
|----------|--------|----------|
| **OpenAI** | GPT-4, GPT-4-turbo, GPT-3.5-turbo | Function calling, streaming |
| **Anthropic** | Claude 3.5 Sonnet, Claude 3 Opus | Tool use, streaming |
| **Ollama** | Llama 3, Mistral, CodeLlama, etc. | Local inference, streaming |
| **OpenRouter** | Multiple providers | Unified API |
| **Local (llama.cpp)** | GGUF models | Offline, private |
| **Azure OpenAI** | GPT-4, GPT-3.5 | Enterprise compliance |
| **Google** | Gemini Pro, Gemini Ultra | Function calling |

### 12.2 Provider Configuration

```yaml
# ~/.config/mini-claude-code/config.yaml

providers:
  openai:
    api_key: ${OPENAI_API_KEY}
    base_url: https://api.openai.com/v1
    default_model: gpt-4-turbo-preview

  anthropic:
    api_key: ${ANTHROPIC_API_KEY}
    default_model: claude-3-5-sonnet-20241022

  ollama:
    base_url: http://localhost:11434
    default_model: llama3.1:70b

  openrouter:
    api_key: ${OPENROUTER_API_KEY}
    default_model: anthropic/claude-3.5-sonnet

default_provider: anthropic
```

### 12.3 Model Selection Strategy

- **Task-based Selection**: Use appropriate model for task complexity
- **Fallback Chain**: Fallback to cheaper/faster models on failure
- **Cost Tracking**: Track and display token costs
- **Rate Limiting**: Handle rate limits gracefully with backoff

---

## 13. Development Workflow Integration

### 13.1 Git Integration

- **Status Awareness**: Understand current git state
- **Commit Generation**: Generate meaningful commit messages
- **PR Description**: Generate pull request descriptions
- **Code Review**: Review changes and suggest improvements
- **Conflict Resolution**: Help resolve merge conflicts

### 13.2 Build System Integration

- **Auto-detection**: Detect build system (npm, cargo, make, etc.)
- **Command Suggestions**: Suggest appropriate commands
- **Error Parsing**: Parse and explain build errors
- **Dependency Management**: Understand and manage dependencies

### 13.3 Testing Integration

- **Test Discovery**: Find and understand test files
- **Test Generation**: Generate tests for code
- **Test Running**: Execute tests and parse results
- **Coverage Analysis**: Understand test coverage

### 13.4 CI/CD Integration

- **GitHub Actions**: Understand and modify workflows
- **GitLab CI**: Support for .gitlab-ci.yml
- **Pipeline Debugging**: Help debug CI failures

---

## 14. Configuration System

### 14.1 Configuration Hierarchy

1. **Defaults**: Built-in sensible defaults
2. **Global Config**: `~/.config/mini-claude-code/config.yaml`
3. **Project Config**: `<project>/.mini-claude-code/config.yaml`
4. **Environment Variables**: `MCC_*` prefixed variables
5. **CLI Arguments**: Highest priority

### 14.2 Configuration Options

```yaml
# ~/.config/mini-claude-code/config.yaml

# LLM Settings
llm:
  provider: anthropic
  model: claude-3-5-sonnet-20241022
  temperature: 0.7
  max_tokens: 4096

# TUI Settings
tui:
  theme: dark
  show_token_count: true
  show_cost: true
  auto_scroll: true
  vim_mode: false

# Behavior Settings
behavior:
  auto_approve_reads: true
  auto_approve_safe_commands: true
  confirm_before_write: true
  confirm_before_execute: true
  max_file_size_kb: 1024
  max_context_files: 20

# Memory Settings
memory:
  enable_global_memory: true
  enable_project_memory: true
  auto_compact_threshold: 80000  # tokens

# Security Settings
security:
  command_allowlist: []
  command_blocklist: []
  protected_paths: []
  sandbox_mode: false

# Logging
logging:
  level: info
  file: ~/.local/share/mini-claude-code/logs/mcc.log
```

---

## 15. Extensibility

### 15.1 Custom Tools

Users can define custom tools:

```yaml
# ~/.config/mini-claude-code/tools/deploy.yaml

name: deploy
description: Deploy the application to production
parameters:
  - name: environment
    type: string
    required: true
    enum: [staging, production]
  - name: version
    type: string
    required: false
command: |
  ./scripts/deploy.sh --env {{ environment }} --version {{ version | default('latest') }}
requires_approval: true
```

### 15.2 Hooks System

```yaml
# Project-level hooks: .mini-claude-code/hooks.yaml

hooks:
  pre_write:
    - command: "npm run lint --fix {{ file }}"
      on_file_types: [".js", ".ts", ".tsx"]

  post_write:
    - command: "npm run format {{ file }}"
      on_file_types: [".js", ".ts", ".tsx"]

  pre_commit:
    - command: "npm test"
      fail_on_error: true

  on_error:
    - notify: true
      command: "echo 'Error occurred' | notify-send"
```

### 15.3 MCP (Model Context Protocol) Support (Future)

- **MCP Server Integration**: Connect to MCP servers for extended capabilities
- **Tool Discovery**: Dynamically discover and use MCP tools
- **Resource Access**: Access MCP resources (databases, APIs, etc.)

---

## 16. Performance Requirements

### 16.1 Targets

| Metric | Target |
|--------|--------|
| **Startup Time** | < 500ms |
| **First Response** | < 2s (excluding LLM latency) |
| **Memory Usage** | < 100MB idle, < 500MB active |
| **File Indexing** | < 5s for 10,000 files |
| **Search Latency** | < 100ms for grep, < 500ms for semantic |

### 16.2 Optimization Strategies

- **Lazy Loading**: Load components on demand
- **Streaming Responses**: Stream LLM responses in real-time
- **Async I/O**: Non-blocking file and network operations
- **Caching**: Cache file contents, embeddings, and responses
- **Incremental Indexing**: Update index on file changes only

---

## 17. Technical Stack

### 17.1 Core Technologies

| Component | Technology | Rationale |
|-----------|------------|-----------|
| **Language** | Python 3.11+ | Rich ecosystem, async support |
| **TUI Framework** | Textual | Modern, feature-rich, async-native |
| **CLI Framework** | Click / Typer | Excellent CLI experience |
| **LLM Integration** | LiteLLM | Unified interface for all providers |
| **Async Runtime** | asyncio | Native Python async |
| **HTTP Client** | httpx | Modern async HTTP |
| **Config** | Pydantic | Type-safe configuration |
| **Storage** | SQLite | Lightweight, no server needed |

### 17.2 Dependencies

```toml
[project]
dependencies = [
    "textual>=0.47.0",           # TUI framework
    "typer>=0.9.0",              # CLI framework
    "litellm>=1.30.0",           # LLM provider abstraction
    "httpx>=0.27.0",             # Async HTTP client
    "pydantic>=2.5.0",           # Data validation
    "pydantic-settings>=2.1.0", # Settings management
    "rich>=13.7.0",              # Rich text formatting
    "pygments>=2.17.0",          # Syntax highlighting
    "aiosqlite>=0.19.0",         # Async SQLite
    "watchfiles>=0.21.0",        # File watching
    "tiktoken>=0.6.0",           # Token counting
    "tree-sitter>=0.21.0",       # Code parsing (optional)
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.23.0",
    "pytest-cov>=4.1.0",
    "ruff>=0.2.0",
    "mypy>=1.8.0",
]
```

---

## 18. Milestones & Phases

### Phase 1: Foundation (MVP)

**Goal**: Basic working TUI with core functionality

- [ ] Project structure and build setup
- [ ] Basic TUI layout with Textual
- [ ] Single LLM provider integration (Anthropic)
- [ ] Core tools: read_file, write_file, bash_execute, grep_search
- [ ] Basic permission system (confirm all writes)
- [ ] Simple conversation history
- [ ] Basic CLI with `-p` flag

**Deliverable**: Usable coding assistant for simple tasks

### Phase 2: Enhanced Agent

**Goal**: Full agentic capabilities

- [ ] Multi-file editing with diffs
- [ ] Git integration (status, diff, commit)
- [ ] Project memory (AGENT.md)
- [ ] Slash commands
- [ ] Context window management
- [ ] Semantic search (basic)
- [ ] Multiple LLM providers

**Deliverable**: Feature-complete coding assistant

### Phase 3: Polish & Performance

**Goal**: Production-ready quality

- [ ] Comprehensive error handling
- [ ] Performance optimization
- [ ] Theme support
- [ ] Configuration system
- [ ] Keyboard shortcuts
- [ ] Command history and search
- [ ] Conversation persistence

**Deliverable**: Polished, reliable tool

### Phase 4: Advanced Features

**Goal**: Power user features

- [ ] Custom tools
- [ ] Hooks system
- [ ] Sub-agents for parallel tasks
- [ ] MCP integration
- [ ] Sandboxing
- [ ] Plugin system

**Deliverable**: Extensible platform

---

## Appendix A: Comparison with Claude Code

| Feature | Claude Code | Mini-Claude-Code |
|---------|-------------|------------------|
| Model Support | Claude only | Any LLM |
| Pricing | Usage-based | Bring your own API key |
| TUI | Yes | Yes |
| IDE Integration | VS Code, JetBrains | Terminal only (by design) |
| MCP Support | Yes | Planned |
| Sandboxing | Yes | Planned |
| Custom Tools | Limited | Full support |
| Offline Mode | No | Yes (with local models) |
| Open Source | No | Yes |

---

## Appendix B: Keyboard Shortcut Reference

| Context | Shortcut | Action |
|---------|----------|--------|
| Global | `Ctrl+C` | Cancel/Exit |
| Global | `Ctrl+L` | Clear screen |
| Global | `Ctrl+K` | Command palette |
| Input | `Enter` | Send (single-line) |
| Input | `Ctrl+Enter` | Send (multi-line) |
| Input | `↑` | Previous history |
| Input | `↓` | Next history |
| Input | `Tab` | Autocomplete |
| Diff View | `Ctrl+Y` | Accept changes |
| Diff View | `Ctrl+N` | Reject changes |
| Diff View | `Ctrl+D` | Toggle diff |
| Output | `Ctrl+U` | Scroll up |
| Output | `Ctrl+D` | Scroll down |
| Output | `g` | Go to top |
| Output | `G` | Go to bottom |

---

## Appendix C: Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `MCC_CONFIG` | Config file path | `~/.config/mini-claude-code/config.yaml` |
| `MCC_PROVIDER` | Default LLM provider | `anthropic` |
| `MCC_MODEL` | Default model | Provider default |
| `OPENAI_API_KEY` | OpenAI API key | - |
| `ANTHROPIC_API_KEY` | Anthropic API key | - |
| `OPENROUTER_API_KEY` | OpenRouter API key | - |
| `MCC_LOG_LEVEL` | Logging level | `info` |
| `MCC_NO_COLOR` | Disable colors | `false` |
| `MCC_DEBUG` | Debug mode | `false` |

---

*Document Version: 1.0*
*Last Updated: January 2026*
