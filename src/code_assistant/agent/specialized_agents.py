"""Specialized agents for specific tasks like project analysis, planning, and sub-tasks."""

from pathlib import Path
from typing import AsyncIterator

from agno.agent import Agent, RunContentEvent, RunOutputEvent
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

SUBAGENT_COORDINATOR_PROMPT = """\
You are a task coordinator that breaks down complex tasks into parallel sub-tasks.

Your role is to:
1. Analyze the main task
2. Identify independent sub-tasks that can run in parallel
3. Identify dependent sub-tasks that must run sequentially
4. Assign each sub-task a clear, specific goal
5. Define success criteria for each sub-task
6. Aggregate results when all sub-tasks complete

## Sub-task Format:
Each sub-task should have:
- **ID**: Unique identifier (e.g., "task-1")
- **Goal**: Clear, specific objective
- **Context**: What the sub-agent needs to know
- **Dependencies**: List of task IDs this depends on (empty for parallel tasks)
- **Success Criteria**: How to verify completion

## Output Format:
When breaking down a task, output JSON:
```json
{
  "main_goal": "Overall objective",
  "subtasks": [
    {
      "id": "task-1",
      "goal": "Specific task goal",
      "context": "Relevant context",
      "dependencies": [],
      "files_hint": ["possible/files/to/check.py"]
    }
  ],
  "execution_order": [["task-1", "task-2"], ["task-3"]]
}
```
The execution_order is an array of arrays - tasks in the same inner array run in parallel.
"""

SUBAGENT_WORKER_PROMPT = """\
You are a focused sub-agent working on a specific task as part of a larger goal.

You have been assigned a specific task. Focus ONLY on completing this task.

Your task details:
- **Goal**: {goal}
- **Context**: {context}
- **Files to check**: {files_hint}

Complete the task and provide a clear summary of:
1. What you did
2. What files you modified (if any)
3. Any issues encountered
4. Whether the task was successful

Be efficient and focused. Do not deviate from the assigned task.
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


def create_subagent_coordinator(project_path: str, model: Model) -> Agent:
    """Create a coordinator agent for managing sub-tasks."""
    return Agent(
        name="subagent-coordinator",
        model=model,
        instructions=SUBAGENT_COORDINATOR_PROMPT,
        tools=[
            FileToolkit(working_directory=project_path),
            SearchToolkit(working_directory=project_path),
        ],
        markdown=True,
    )


def create_subagent_worker(
    project_path: str,
    model: Model,
    goal: str,
    context: str,
    files_hint: list[str] | None = None,
) -> Agent:
    """Create a worker sub-agent for a specific task."""
    prompt = SUBAGENT_WORKER_PROMPT.format(
        goal=goal,
        context=context,
        files_hint=", ".join(files_hint) if files_hint else "None specified",
    )
    return Agent(
        name="subagent-worker",
        model=model,
        instructions=prompt,
        tools=[
            FileToolkit(working_directory=project_path),
            SearchToolkit(working_directory=project_path),
            ShellToolkit(working_directory=project_path),
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


class SubAgentManager:
    """Manager for coordinating sub-agents on complex tasks."""
    
    def __init__(self, project_path: str, model: Model):
        self.project_path = project_path
        self.model = model
        self.coordinator = create_subagent_coordinator(project_path, model)
        self.results: dict[str, str] = {}
        self.completed_tasks: set[str] = set()
    
    async def execute_task(
        self,
        main_task: str,
        session_id: str | None = None,
    ) -> AsyncIterator[RunOutputEvent]:
        """Execute a complex task using sub-agents."""
        import json
        
        # First, have the coordinator break down the task
        breakdown_prompt = f"""Break down this task into sub-tasks that can be executed in parallel where possible:

---
{main_task}
---

Analyze the codebase first to understand what's needed, then output the task breakdown as JSON."""

        breakdown_content = ""
        async for event in self.coordinator.arun(
            breakdown_prompt,
            session_id=session_id,
            stream=True,
            stream_events=True,
        ):
            yield event
            if isinstance(event, RunContentEvent) and event.content:
                breakdown_content += event.content
        
        # Try to parse the task breakdown
        try:
            # Find JSON in the response
            json_start = breakdown_content.find("{")
            json_end = breakdown_content.rfind("}") + 1
            if json_start >= 0 and json_end > json_start:
                task_breakdown = json.loads(breakdown_content[json_start:json_end])
            else:
                # No JSON found, execute as single task
                yield RunContentEvent(
                    content="\n\n---\nNo task breakdown found, executing as single task...\n"
                )
                async for event in self._execute_single_task(main_task, session_id):
                    yield event
                return
        except json.JSONDecodeError:
            yield RunContentEvent(
                content="\n\n---\nCould not parse task breakdown, executing as single task...\n"
            )
            async for event in self._execute_single_task(main_task, session_id):
                yield event
            return
        
        # Execute tasks according to execution order
        execution_order = task_breakdown.get("execution_order", [])
        subtasks = {t["id"]: t for t in task_breakdown.get("subtasks", [])}
        
        for parallel_batch in execution_order:
            yield RunContentEvent(
                content=f"\n\n### Executing batch: {parallel_batch}\n"
            )
            
            # For simplicity, execute sequentially (true parallelism would need asyncio.gather)
            # but structure allows for parallel execution in future
            for task_id in parallel_batch:
                if task_id not in subtasks:
                    continue
                    
                task = subtasks[task_id]
                yield RunContentEvent(
                    content=f"\n#### Sub-task: {task_id}\n**Goal**: {task['goal']}\n\n"
                )
                
                # Create and run worker agent
                worker = create_subagent_worker(
                    self.project_path,
                    self.model,
                    goal=task["goal"],
                    context=task.get("context", ""),
                    files_hint=task.get("files_hint"),
                )
                
                task_result = ""
                async for event in worker.arun(
                    f"Complete this task: {task['goal']}",
                    session_id=f"{session_id}-{task_id}" if session_id else None,
                    stream=True,
                    stream_events=True,
                ):
                    yield event
                    if isinstance(event, RunContentEvent) and event.content:
                        task_result += event.content
                
                self.results[task_id] = task_result
                self.completed_tasks.add(task_id)
        
        # Final summary
        yield RunContentEvent(
            content=f"\n\n### All sub-tasks completed\n"
            f"Completed: {len(self.completed_tasks)} tasks\n"
        )
    
    async def _execute_single_task(
        self,
        task: str,
        session_id: str | None = None,
    ) -> AsyncIterator[RunOutputEvent]:
        """Fallback: execute as a single task without breakdown."""
        worker = create_subagent_worker(
            self.project_path,
            self.model,
            goal=task,
            context="Execute this task directly",
            files_hint=None,
        )
        
        async for event in worker.arun(
            task,
            session_id=session_id,
            stream=True,
            stream_events=True,
        ):
            yield event
