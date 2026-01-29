"""CLI for llmglot - sync LLM agent configuration files."""

from pathlib import Path
from typing import Annotated, Optional

import typer

from llmglot.agents import get_agent, get_all_agents
from llmglot.sync.skills import sync_skills as do_sync_skills, discover_skills
from llmglot.sync.agents import sync_agents as do_sync_agents

app = typer.Typer(
    name="llmglot",
    help="Sync LLM agent configuration files across different coding assistants.",
    no_args_is_help=True,
)

GITIGNORE_HEADER = "# llmglot - machine-generated agent files"

sync_app = typer.Typer(
    name="sync",
    help="Sync skills and agent files.",
    no_args_is_help=True,
)
app.add_typer(sync_app, name="sync")


def _get_agents(target: Optional[str]):
    """Get agents based on target filter."""
    if target:
        return [get_agent(target)]
    return list(get_all_agents())


@sync_app.command("skills")
def sync_skills(
    source: Annotated[
        Path,
        typer.Option(
            "--source",
            "-s",
            help="Source directory containing skills/",
        ),
    ] = Path("."),
    target: Annotated[
        Optional[str],
        typer.Option(
            "--target",
            "-t",
            help="Target agent (claude, cursor, windsurf, copilot, cline, gemini)",
        ),
    ] = None,
    dry_run: Annotated[
        bool,
        typer.Option(
            "--dry-run",
            "-n",
            help="Show what would be synced without making changes",
        ),
    ] = False,
):
    """Sync skills/ directory to agent-specific skill directories."""
    source = source.resolve()
    agents = _get_agents(target)

    skills = list(discover_skills(source))
    if not skills:
        typer.echo(f"No skills found in {source / 'skills'}")
        raise typer.Exit(1)

    if dry_run:
        typer.echo("Dry run - no changes will be made\n")

    typer.echo(f"Found {len(skills)} skill(s): {', '.join(s.stem for s in skills)}")
    typer.echo(f"Syncing to {len(agents)} agent(s): {', '.join(a.name for a in agents)}\n")

    results = do_sync_skills(source, agents, dry_run)

    success_count = sum(1 for r in results if r.success)
    fail_count = len(results) - success_count

    for result in results:
        status = "OK" if result.success else "FAIL"
        typer.echo(f"  [{status}] {result.skill_name} -> {result.agent_id}: {result.destination}")
        if result.error:
            typer.echo(f"       Error: {result.error}")

    typer.echo(f"\nSynced {success_count} skill(s), {fail_count} failed")

    if fail_count > 0:
        raise typer.Exit(1)


@sync_app.command("agents")
def sync_agents(
    source: Annotated[
        Path,
        typer.Option(
            "--source",
            "-s",
            help="Source directory containing LLMGLOT.md",
        ),
    ] = Path("."),
    target: Annotated[
        Optional[str],
        typer.Option(
            "--target",
            "-t",
            help="Target agent (claude, cursor, windsurf, copilot, cline, gemini)",
        ),
    ] = None,
    dry_run: Annotated[
        bool,
        typer.Option(
            "--dry-run",
            "-n",
            help="Show what would be synced without making changes",
        ),
    ] = False,
):
    """Sync LLMGLOT.md to agent-specific instruction files."""
    source = source.resolve()
    agents = _get_agents(target)

    agents_md = source / "LLMGLOT.md"
    if not agents_md.exists():
        typer.echo(f"LLMGLOT.md not found in {source}")
        raise typer.Exit(1)

    if dry_run:
        typer.echo("Dry run - no changes will be made\n")

    typer.echo(f"Found LLMGLOT.md in {source}")
    typer.echo(f"Syncing to {len(agents)} agent(s): {', '.join(a.name for a in agents)}\n")

    results = do_sync_agents(source, agents, dry_run)

    success_count = sum(1 for r in results if r.success)
    fail_count = len(results) - success_count

    for result in results:
        status = "OK" if result.success else "FAIL"
        typer.echo(f"  [{status}] {result.agent_id}: {result.destination}")
        if result.error:
            typer.echo(f"       Error: {result.error}")

    typer.echo(f"\nSynced to {success_count} agent(s), {fail_count} failed")

    if fail_count > 0:
        raise typer.Exit(1)


@sync_app.command("all")
def sync_all(
    source: Annotated[
        Path,
        typer.Option(
            "--source",
            "-s",
            help="Source directory",
        ),
    ] = Path("."),
    target: Annotated[
        Optional[str],
        typer.Option(
            "--target",
            "-t",
            help="Target agent (claude, cursor, windsurf, copilot, cline, gemini)",
        ),
    ] = None,
    dry_run: Annotated[
        bool,
        typer.Option(
            "--dry-run",
            "-n",
            help="Show what would be synced without making changes",
        ),
    ] = False,
):
    """Sync both skills/ and LLMGLOT.md to all agents."""
    source = source.resolve()
    agents = _get_agents(target)

    if dry_run:
        typer.echo("Dry run - no changes will be made\n")

    typer.echo(f"Syncing to {len(agents)} agent(s): {', '.join(a.name for a in agents)}\n")

    skills = list(discover_skills(source))
    agents_md = source / "LLMGLOT.md"

    total_success = 0
    total_fail = 0

    if skills:
        typer.echo(f"Skills: {len(skills)} found")
        results = do_sync_skills(source, agents, dry_run)
        for result in results:
            status = "OK" if result.success else "FAIL"
            typer.echo(f"  [{status}] {result.skill_name} -> {result.agent_id}")
            if result.success:
                total_success += 1
            else:
                total_fail += 1
        typer.echo()
    else:
        typer.echo("Skills: none found\n")

    if agents_md.exists():
        typer.echo("LLMGLOT.md: found")
        results = do_sync_agents(source, agents, dry_run)
        for result in results:
            status = "OK" if result.success else "FAIL"
            typer.echo(f"  [{status}] -> {result.agent_id}")
            if result.success:
                total_success += 1
            else:
                total_fail += 1
        typer.echo()
    else:
        typer.echo("LLMGLOT.md: not found\n")

    typer.echo(f"Total: {total_success} synced, {total_fail} failed")

    if total_fail > 0:
        raise typer.Exit(1)


@app.command("init")
def init(
    path: Annotated[
        Path,
        typer.Option(
            "--path",
            "-p",
            help="Path to the project directory",
        ),
    ] = Path("."),
    dry_run: Annotated[
        bool,
        typer.Option(
            "--dry-run",
            "-n",
            help="Show what would be added without making changes",
        ),
    ] = False,
):
    """Add machine-generated agent files to .gitignore."""
    path = path.resolve()
    gitignore = path / ".gitignore"

    agents = list(get_all_agents())
    entries: list[str] = []

    for agent in agents:
        entries.append(f"/{agent.agent_file}")
        entries.append(f"/{agent.skills_dir}/")

    block = f"{GITIGNORE_HEADER}\n" + "\n".join(entries) + "\n"

    if gitignore.exists():
        content = gitignore.read_text()
        if GITIGNORE_HEADER in content:
            typer.echo("llmglot entries already present in .gitignore")
            return
        new_content = content.rstrip() + "\n\n" + block
    else:
        new_content = block

    if dry_run:
        typer.echo("Would add to .gitignore:\n")
        typer.echo(block)
        return

    gitignore.write_text(new_content)
    typer.echo(f"Added {len(entries)} entries to .gitignore:")
    for entry in entries:
        typer.echo(f"  {entry}")


if __name__ == "__main__":
    app()
