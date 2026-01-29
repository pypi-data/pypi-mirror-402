"""Gemini CLI agent implementation."""

from pathlib import Path

from llmglot.agents.base import Agent, register_agent


@register_agent
class GeminiAgent(Agent):
    """Gemini CLI agent."""

    @property
    def name(self) -> str:
        return "Gemini"

    @property
    def id(self) -> str:
        return "gemini"

    @property
    def skills_dir(self) -> Path:
        return Path(".gemini/skills")

    @property
    def agent_file(self) -> Path:
        return Path("GEMINI.md")
