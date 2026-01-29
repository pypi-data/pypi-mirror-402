"""Base agent abstraction for LLM coding assistants."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterator


class Agent(ABC):
    """Base class for LLM coding assistant agents."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable name of the agent."""
        ...

    @property
    @abstractmethod
    def id(self) -> str:
        """Short identifier for the agent (used in CLI)."""
        ...

    @property
    @abstractmethod
    def skills_dir(self) -> Path:
        """Relative path to the skills directory for this agent."""
        ...

    @property
    @abstractmethod
    def agent_file(self) -> Path:
        """Relative path to the agent instructions file."""
        ...

    def transform_skill(self, content: str, skill_name: str) -> str:
        """Transform a skill file for this agent.

        Override in subclasses if agent-specific transformation is needed.
        """
        return content

    def transform_agents_md(self, content: str) -> str:
        """Transform LLMGLOT.md content for this agent.

        Override in subclasses if agent-specific transformation is needed.
        """
        return content

    def get_skills_dir(self, root: Path) -> Path:
        """Get the absolute path to skills directory."""
        return root / self.skills_dir

    def get_agent_file(self, root: Path) -> Path:
        """Get the absolute path to agent file."""
        return root / self.agent_file


_AGENTS: dict[str, type[Agent]] = {}


def register_agent(agent_cls: type[Agent]) -> type[Agent]:
    """Register an agent class."""
    instance = agent_cls()
    _AGENTS[instance.id] = agent_cls
    return agent_cls


def get_agent(agent_id: str) -> Agent:
    """Get an agent instance by ID."""
    if agent_id not in _AGENTS:
        available = ", ".join(sorted(_AGENTS.keys()))
        raise ValueError(f"Unknown agent: {agent_id}. Available: {available}")
    return _AGENTS[agent_id]()


def get_all_agents() -> "Iterator[Agent]":
    """Get all registered agent instances."""
    for agent_cls in _AGENTS.values():
        yield agent_cls()
