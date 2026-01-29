"""Cline agent implementation."""

from pathlib import Path

from llmglot.agents.base import Agent, register_agent


@register_agent
class ClineAgent(Agent):
    """Cline (Claude Dev) agent."""

    @property
    def name(self) -> str:
        return "Cline"

    @property
    def id(self) -> str:
        return "cline"

    @property
    def skills_dir(self) -> Path:
        return Path(".cline/rules")

    @property
    def agent_file(self) -> Path:
        return Path(".clinerules")
