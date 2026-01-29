"""Sync LLMGLOT.md to agent-specific files."""

from pathlib import Path
from typing import TYPE_CHECKING

from jinja2 import Environment, BaseLoader

if TYPE_CHECKING:
    from llmglot.agents.base import Agent


class AgentSyncResult:
    """Result of syncing LLMGLOT.md to an agent file."""

    def __init__(
        self,
        agent_id: str,
        source: Path,
        destination: Path,
        success: bool,
        error: str | None = None,
    ):
        self.agent_id = agent_id
        self.source = source
        self.destination = destination
        self.success = success
        self.error = error


def transform_agents_md(content: str, agent: "Agent") -> str:
    """Transform LLMGLOT.md content using Jinja2 and agent-specific transformations."""
    env = Environment(loader=BaseLoader())

    template_vars = {
        "agent_name": agent.name,
        "agent_id": agent.id,
    }

    try:
        template = env.from_string(content)
        rendered = template.render(**template_vars)
    except Exception:
        rendered = content

    return agent.transform_agents_md(rendered)


def sync_agent_file(
    source_dir: Path,
    agent: "Agent",
    dry_run: bool = False,
) -> AgentSyncResult | None:
    """Sync LLMGLOT.md to an agent's instruction file."""
    agents_md = source_dir / "LLMGLOT.md"

    if not agents_md.exists():
        return None

    dest_file = agent.get_agent_file(source_dir)

    try:
        content = agents_md.read_text()
        transformed = transform_agents_md(content, agent)

        if not dry_run:
            dest_file.parent.mkdir(parents=True, exist_ok=True)
            dest_file.write_text(transformed)

        return AgentSyncResult(
            agent_id=agent.id,
            source=agents_md,
            destination=dest_file,
            success=True,
        )
    except Exception as e:
        return AgentSyncResult(
            agent_id=agent.id,
            source=agents_md,
            destination=dest_file,
            success=False,
            error=str(e),
        )


def sync_agents(
    source_dir: Path,
    agents: "list[Agent]",
    dry_run: bool = False,
) -> "list[AgentSyncResult]":
    """Sync LLMGLOT.md to all specified agents."""
    results: list[AgentSyncResult] = []

    for agent in agents:
        result = sync_agent_file(source_dir, agent, dry_run)
        if result:
            results.append(result)

    return results
