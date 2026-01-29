"""Claude agent implementation."""

from pathlib import Path

from llmglot.agents.base import Agent, register_agent


@register_agent
class ClaudeAgent(Agent):
    """Claude Code agent."""

    @property
    def name(self) -> str:
        return "Claude"

    @property
    def id(self) -> str:
        return "claude"

    @property
    def skills_dir(self) -> Path:
        return Path(".claude/skills")

    @property
    def agent_file(self) -> Path:
        return Path("CLAUDE.md")
