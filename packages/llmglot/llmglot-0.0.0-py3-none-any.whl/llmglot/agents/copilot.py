"""GitHub Copilot agent implementation."""

from pathlib import Path

from llmglot.agents.base import Agent, register_agent


@register_agent
class CopilotAgent(Agent):
    """GitHub Copilot agent."""

    @property
    def name(self) -> str:
        return "GitHub Copilot"

    @property
    def id(self) -> str:
        return "copilot"

    @property
    def skills_dir(self) -> Path:
        return Path(".github/copilot-skills")

    @property
    def agent_file(self) -> Path:
        return Path(".github/copilot-instructions.md")
