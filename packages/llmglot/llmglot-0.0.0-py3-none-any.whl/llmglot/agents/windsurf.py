"""Windsurf agent implementation."""

from pathlib import Path

from llmglot.agents.base import Agent, register_agent


@register_agent
class WindsurfAgent(Agent):
    """Windsurf editor agent."""

    @property
    def name(self) -> str:
        return "Windsurf"

    @property
    def id(self) -> str:
        return "windsurf"

    @property
    def skills_dir(self) -> Path:
        return Path(".windsurf/rules")

    @property
    def agent_file(self) -> Path:
        return Path(".windsurfrules")
