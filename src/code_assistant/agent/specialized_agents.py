"""Specialized agents for specific tasks like project analysis and planning."""

from pathlib import Path
from typing import AsyncIterator

from agno.agent import Agent, RunOutputEvent
from agno.models.base import Model

from code_assistant.tools import FileToolkit, SearchToolkit, ShellToolkit


# === System Prompts for Specialized Agents ===

INIT_AGENT_PROMPT = """\
You are a project analyzer that creates comprehensive AGENT.md files for coding projects.

Your task is to analyze a project directory and generate a detailed AGENT.md file that captures:

1. **Project Overview**: What the project does, its purpose
2. **Tech Stack**: Languages, frameworks, libraries, databases
3. **Architecture**: Directory structure, key components, patterns used
4. **Conventions**: Coding style, naming conventions, patterns observed
5. **Common Commands**: Build, test, lint, run commands from package.json/Makefile/etc.
6. **Important Notes**: Dependencies, configuration, environment setup

## Analysis Steps:
1. Read key configuration files (package.json, requirements.txt, Cargo.toml, pyproject.toml, etc.)
2. Examine the directory structure
3. Look at a few key source files to understand patterns
4. Check for existing documentation (README.md)
5. Identify build/test commands

## Output Format:
Generate a complete AGENT.md file in markdown format. Be thorough but concise.
Focus on information that would help an AI coding assistant understand the project.

After analysis, output ONLY the AGENT.md content, nothing else.
"""

PLAN_AGENT_PROMPT = """\
You are a technical planning agent that creates detailed implementation plans.

When given a feature request or requirement, you will:

1. **Understand the Request**: Clarify the goal and scope
2. **Analyze the Codebase**: Identify relevant files and patterns
3. **Create a Step-by-Step Plan**: Break down into actionable tasks
4. **Identify Dependencies**: Note what needs to be done first
5. **Estimate Complexity**: Mark each task as simple/medium/complex
6. **Consider Edge Cases**: Note potential issues and how to handle them

## Output Format:
```
# Implementation Plan: [Feature Name]

## Overview
Brief description of what will be implemented.

## Prerequisites
- [ ] Any setup or preparation needed

## Tasks
1. [ ] **Task 1** (complexity: simple)
   - Description of what to do
   - Files affected: `path/to/file.py`
   
2. [ ] **Task 2** (complexity: medium)
   - Description
   - Depends on: Task 1
   - Files affected: `path/to/other.py`

## Testing Strategy
- How to verify the implementation works

## Potential Issues
- Edge cases to consider
- Known limitations
```

Be thorough and practical. Plans should be actionable by a developer or AI assistant.
"""


def create_init_agent(project_path: str, model: Model) -> Agent:
    """Create an agent for analyzing projects and generating AGENT.md."""
    return Agent(
        name="init-agent",
        model=model,
        instructions=INIT_AGENT_PROMPT,
        tools=[
            FileToolkit(working_directory=project_path),
            SearchToolkit(working_directory=project_path),
            ShellToolkit(working_directory=project_path),
        ],
        markdown=True,
    )


def create_plan_agent(project_path: str, model: Model) -> Agent:
    """Create an agent for creating implementation plans."""
    return Agent(
        name="plan-agent",
        model=model,
        instructions=PLAN_AGENT_PROMPT,
        tools=[
            FileToolkit(working_directory=project_path),
            SearchToolkit(working_directory=project_path),
        ],
        markdown=True,
    )


async def run_init_agent(
    project_path: str,
    model: Model,
    session_id: str | None = None,
) -> AsyncIterator[RunOutputEvent]:
    """Run the init agent to analyze a project and generate AGENT.md content."""
    agent = create_init_agent(project_path, model)
    
    project_name = Path(project_path).name
    prompt = f"""Analyze the project at "{project_path}" (named "{project_name}") and generate a comprehensive AGENT.md file.

Start by:
1. Listing the root directory to see project structure
2. Reading any configuration files (package.json, pyproject.toml, requirements.txt, Cargo.toml, etc.)
3. Reading README.md if it exists
4. Examining a few key source files

Then generate the AGENT.md content."""

    async for event in agent.arun(
        prompt,
        session_id=session_id,
        stream=True,
        stream_events=True,
    ):
        yield event


async def run_plan_agent(
    project_path: str,
    model: Model,
    requirement: str,
    session_id: str | None = None,
) -> AsyncIterator[RunOutputEvent]:
    """Run the planning agent to create an implementation plan."""
    agent = create_plan_agent(project_path, model)
    
    prompt = f"""Create a detailed implementation plan for the following requirement:

---
{requirement}
---

First, analyze the codebase to understand the current structure and patterns.
Then create a comprehensive, step-by-step implementation plan."""

    async for event in agent.arun(
        prompt,
        session_id=session_id,
        stream=True,
        stream_events=True,
    ):
        yield event
