# I Built a "Mini" Claude Code to See How It Works. Here’s What I Learned.

When Anthropic released **Claude Code**, I was hooked. An AI that could navigate my filesystem, edit code safely, and understand project context? I didn't want to just use it—I wanted to reverse-engineer it.

So, I built **Mini-Claude-Code (MCC)**: a functional, terminal-based coding assistant built with Python. It’s not a competitor (and won’t be maintained), but building it revealed exactly how these agentic tools tick.

## Code
https://github.com/s-aravindh/code-assistant

## The Architecture:

1.  **The Brain (Agent Loop):** An LLM that can "think," decide to use a tool, pause for results, and continue.
2.  **The Hands (Toolkits):** File operations, shell commands, and git integration.
3.  **The Safety Layer (HITL):** A "Human-in-the-Loop" system. Before writing files or running commands, the AI *must* ask for permission.
4.  **Context:** The `AGENT.md` file (inspired by `CLAUDE.md`) that teaches the AI your project's specific conventions.

## The Stack: Agno & Textual

To avoid reinventing the wheel, I used two well designed python libraries:

*   **[Agno](https://github.com/agno-agi/agno):** A Python framework for AI agents. It handled the heavy lifting—memory, tool execution, and streaming—so I didn't have to write an agent loop from scratch.
*   **[Textual](https://github.com/Textualize/textual):** A TUI framework that creates beautiful, web-like interfaces in the terminal.

## The Code: How It Actually Works

The core agent setup with Agno turned out to be surprisingly concise:

```python
agent = Agent(
    name="coding-assistant",
    model=Claude(id="claude-sonnet-4-20250514"),
    instructions=system_prompt,
    tools=[
        FileToolkit(working_directory=project_path),
        ShellToolkit(working_directory=project_path),
        SearchToolkit(working_directory=project_path),
        GitToolkit(working_directory=project_path),
    ],
    enable_user_memories=True,
    markdown=True,
    num_history_runs=15,
)
```

### The Safety Layer
One critical lesson was path traversal protection. You can't just let the AI write to `../../../etc/passwd`. Every path needs validation:

```python
def _resolve_path(self, file_path: str) -> Path:
    path = Path(file_path)
    if not path.is_absolute():
        path = self.working_directory / path
    resolved = path.resolve()
    
    # Security: Ensure path is actually inside our working directory
    try:
        resolved.relative_to(self.working_directory)
    except ValueError:
        raise ValueError(f"Access denied: {file_path} is outside the working directory")
    
    return resolved
```

### The UX Challenge: Human-in-the-Loop
The hardest part wasn't the AI—it was handling the "ask for permission" flow while streaming. The agent might pause multiple times in a single turn.

```python
async def _process_message(self, message: str) -> None:
    # Start the stream
    run_result = await self._stream_run(...)
    run_event = run_result.get("run_event")
    
    # Loop to handle multiple approval requests
    while run_event and run_event.is_paused:
        tools_to_confirm = getattr(run_event, 'tools', [])
        
        for tool in tools_to_confirm:
            if tool.confirmation_required:
                # Show TUI dialog
                approved = await self._show_approval_dialog(tool)
                tool.confirmed = approved
        
        # Continue execution with user's decision
        continue_result = await self._stream_run(
            self.agent.acontinue_run(run_id=run_event.run_id, ...)
        )
```

## Key Lessons

### 1. The Model is the Ceiling
I tested MCC with various models. No matter how good my engineering was, the experience lived or died by the model's intelligence:
- Claude 4.5 opus/sonnet is a beast in coding.
- claude-code success comes from how usable these models have become for coding compared to what it was.
- i could not get simillar good coding results with Gemini or GPT models (didnt try codex or gemini cli)

### 2. Context Changes Everything
Injecting a simple `AGENT.md` file transformed the AI from a generic coder into a specialized team member. It knew our architecture and naming conventions immediately.

### 3. Streaming is Non-Negotiable
Batch responses feel broken. Users need to see the "thought process" in real-time. Implementing streaming with tool interruptions was the hardest technical challenge, but it’s essential for the tool to feel "alive."

## Final Thoughts

Building **Mini-Claude-Code** was a humbling exercise. It turned the "magic" of Claude Code into concrete engineering challenges: streaming management, state loops, and safety checks.

While I won't be maintaining this project, the code is available for anyone who wants to learn. If you want to truly understand agentic AI, don't just read about it—build it.
