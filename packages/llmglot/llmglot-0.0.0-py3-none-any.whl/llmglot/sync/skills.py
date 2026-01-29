"""Sync skills to agent-specific directories."""

from pathlib import Path
from typing import TYPE_CHECKING

from jinja2 import Environment, BaseLoader

if TYPE_CHECKING:
    from collections.abc import Iterator

    from llmglot.agents.base import Agent


class SkillSyncResult:
    """Result of syncing a skill to an agent."""

    def __init__(
        self,
        skill_name: str,
        agent_id: str,
        source: Path,
        destination: Path,
        success: bool,
        error: str | None = None,
    ):
        self.skill_name = skill_name
        self.agent_id = agent_id
        self.source = source
        self.destination = destination
        self.success = success
        self.error = error


def discover_skills(source_dir: Path) -> "Iterator[Path]":
    """Discover all skill files in the skills/ directory."""
    skills_dir = source_dir / "skills"
    if not skills_dir.exists():
        return

    for skill_file in skills_dir.glob("*.md"):
        yield skill_file


def transform_skill(content: str, agent: "Agent", skill_name: str) -> str:
    """Transform skill content using Jinja2 and agent-specific transformations."""
    env = Environment(loader=BaseLoader())

    template_vars = {
        "agent_name": agent.name,
        "agent_id": agent.id,
        "skill_name": skill_name,
    }

    try:
        template = env.from_string(content)
        rendered = template.render(**template_vars)
    except Exception:
        rendered = content

    return agent.transform_skill(rendered, skill_name)


def sync_skill_to_agent(
    skill_path: Path,
    agent: "Agent",
    root: Path,
    dry_run: bool = False,
) -> SkillSyncResult:
    """Sync a single skill file to an agent's skills directory."""
    skill_name = skill_path.stem
    dest_dir = agent.get_skills_dir(root)
    dest_file = dest_dir / skill_path.name

    try:
        content = skill_path.read_text()
        transformed = transform_skill(content, agent, skill_name)

        if not dry_run:
            dest_dir.mkdir(parents=True, exist_ok=True)
            dest_file.write_text(transformed)

        return SkillSyncResult(
            skill_name=skill_name,
            agent_id=agent.id,
            source=skill_path,
            destination=dest_file,
            success=True,
        )
    except Exception as e:
        return SkillSyncResult(
            skill_name=skill_name,
            agent_id=agent.id,
            source=skill_path,
            destination=dest_file,
            success=False,
            error=str(e),
        )


def sync_skills(
    source_dir: Path,
    agents: "list[Agent]",
    dry_run: bool = False,
) -> "list[SkillSyncResult]":
    """Sync all skills to all specified agents."""
    results: list[SkillSyncResult] = []

    skills = list(discover_skills(source_dir))

    for skill_path in skills:
        for agent in agents:
            result = sync_skill_to_agent(skill_path, agent, source_dir, dry_run)
            results.append(result)

    return results
