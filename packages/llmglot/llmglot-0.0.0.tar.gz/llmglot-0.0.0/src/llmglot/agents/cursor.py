"""Cursor agent implementation."""

from pathlib import Path

from llmglot.agents.base import Agent, register_agent


@register_agent
class CursorAgent(Agent):
    """Cursor editor agent."""

    @property
    def name(self) -> str:
        return "Cursor"

    @property
    def id(self) -> str:
        return "cursor"

    @property
    def skills_dir(self) -> Path:
        return Path(".cursor/rules")

    @property
    def agent_file(self) -> Path:
        return Path(".cursorrules")
