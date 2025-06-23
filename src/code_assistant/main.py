from agno.agent import Agent
from agno.team.team import Team
from agno.workflow.workflow import Workflow
from agno.models.openai import OpenAILike
from agno.tools.reasoning import ReasoningTools
from agno.tools.local_file_system import LocalFileSystemTools
from typing import Iterator
from agno.workflow import RunResponse
from agno.utils.log import logger
from code_assistant.prompts import PLANNER_PROMPT, IMPLEMENTATION_PROMPT, REVIEWER_PROMPT

planner = Agent(
    name="planner",
    model=OpenAILike(
        id="qwen3:4b",
        base_url="http://localhost:11434/v1",
    ),
    instructions=PLANNER_PROMPT,
    markdown=True,
    tools=[
        ReasoningTools(think=True),
        LocalFileSystemTools(
            target_directory="/Users/aravindh/Documents/GitHub/code-ai/agents_test"
        ),
    ],
)

coder = Agent(
    name="coder",
    model=OpenAILike(
        id="qwen3:4b",
        base_url="http://localhost:11434/v1",
    ),
    instructions=IMPLEMENTATION_PROMPT,
    markdown=True,
    tools=[
        ReasoningTools(think=True),
        LocalFileSystemTools(
            target_directory="/Users/aravindh/Documents/GitHub/code-ai/agents_test"
        ),
    ],
)

reviewer = Agent(
    name="reviewer",
    model=OpenAILike(
        id="qwen3:4b",
        base_url="http://localhost:11434/v1",
    ),
    instructions=REVIEWER_PROMPT,
    tools=[
        ReasoningTools(think=True),
        LocalFileSystemTools(target_directory="/Users/aravindh/Documents/GitHub/code-ai/agents_test")
    ],
    markdown=True,

)


class SoftwareDevelopmentWorkflow(Workflow):
    """
    A complete software development workflow that orchestrates planning, coding, and review phases.

    This workflow uses three specialized agents:
    - Planner: Analyzes requirements and creates development plans
    - Coder: Implements the planned solution
    - Reviewer: Reviews and provides feedback on the implementation
    """

    # Add the agents as workflow attributes
    planner: Agent = planner
    coder: Agent = coder
    reviewer: Agent = reviewer

    def run(self, requirements: str) -> Iterator[RunResponse]:
        """
        Execute the complete software development workflow.

        Args:
            requirements: The software requirements to implement

        Yields:
            RunResponse: Streaming responses from each phase of the workflow
        """

        # Phase 1: Planning
        logger.info("🎯 Starting Planning Phase...")
        yield RunResponse(
            run_id=self.run_id,
            content="## 🎯 Planning Phase\n\nAnalyzing requirements and creating development plan...\n",
        )

        yield from self.planner.run(requirements, stream=True)
        development_plan = self.planner.run_response.content

        # Phase 2: Implementation
        logger.info("💻 Starting Implementation Phase...")
        yield RunResponse(
            run_id=self.run_id,
            content="\n\n## 💻 Implementation Phase\n\nImplementing the solution based on the plan...\n",
        )

        implementation_input = f"Requirements: {requirements}\n\nDevelopment Plan: {development_plan}"
        yield from self.coder.run(implementation_input, stream=True)
        implementation = self.coder.run_response.content

        # Phase 3: Code Review
        logger.info("🔍 Starting Review Phase...")
        yield RunResponse(
            run_id=self.run_id,
            content="\n\n## 🔍 Review Phase\n\nReviewing the implementation for quality and best practices...\n",
        )

        review_input = f"Requirements: {requirements}\n\nDevelopment Plan: {development_plan}\n\nImplementation: {implementation}"
        yield from self.reviewer.run(review_input, stream=True)

        # Store results in session state for potential reuse
        self.session_state["last_requirements"] = requirements
        self.session_state["last_plan"] = development_plan
        self.session_state["last_implementation"] = implementation
        self.session_state["last_review"] = self.reviewer.run_response.content

        logger.info("✅ Software Development Workflow completed!")


# Example usage
if __name__ == "__main__":
    from agno.utils.pprint import pprint_run_response

    # Create workflow instance
    run_workflow = SoftwareDevelopmentWorkflow()

    # Example requirements
    example_requirements = """
    build a RAG application with openai and qdrant
    """

    # Run the workflow
    print("Starting Software Development Workflow...")
    response = run_workflow.run(requirements=example_requirements)
    pprint_run_response(response, markdown=True, show_time=True)
