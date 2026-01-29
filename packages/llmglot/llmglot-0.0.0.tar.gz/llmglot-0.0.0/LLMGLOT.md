# llmglot

A CLI tool for syncing canonical LLM agent configuration files across different coding assistants.

{% if agent_name %}
> You are reading this as **{{ agent_name }}** (agent ID: `{{ agent_id }}`).
{% endif %}

## Project Overview

llmglot takes a single source of truth (`LLMGLOT.md`, `skills/`) and distributes it to agent-specific locations:

| Agent | Skills Directory | Instructions File |
|-------|------------------|-------------------|
| Claude | `.claude/skills/` | `CLAUDE.md` |
| Cursor | `.cursor/rules/` | `.cursorrules` |
| Windsurf | `.windsurf/rules/` | `.windsurfrules` |
| Copilot | `.github/copilot-skills/` | `.github/copilot-instructions.md` |
| Cline | `.cline/rules/` | `.clinerules` |
| Gemini | `.gemini/skills/` | `GEMINI.md` |

## Architecture

```
src/llmglot/
├── cli.py              # Typer CLI entry point
├── agents/
│   ├── base.py         # Agent base class and registry
│   └── <agent>.py      # Agent implementations
└── sync/
    ├── skills.py       # Skills sync logic
    └── agents.py       # LLMGLOT.md sync logic
```

### Key Concepts

- **Agent**: A coding assistant with specific paths for skills and instructions
- **Skill**: A markdown file in `skills/` that gets synced to each agent's skill directory
- **Transform**: Jinja2 templating + agent-specific transformations

### Template Variables

Skills and LLMGLOT.md support Jinja2 templating:

- `{{ '{{' }} agent_name {{ '}}' }}` - Human-readable name (e.g., "Claude", "Cursor")
- `{{ '{{' }} agent_id {{ '}}' }}` - Short identifier (e.g., "claude", "cursor")
- `{{ '{{' }} skill_name {{ '}}' }}` - Name of the skill being processed (skills only)

## Development

### Running the CLI

```bash
uv run llmglot --help
uv run llmglot sync skills --dry-run
uv run llmglot sync agents --target claude
```

### Adding a New Agent

1. Create `src/llmglot/agents/<agent>.py`
2. Define a class inheriting from `Agent`
3. Use the `@register_agent` decorator
4. Define `name`, `id`, `skills_dir`, and `agent_file` properties

### Testing Changes

Always use `--dry-run` first to verify what will be synced:

```bash
uv run llmglot sync all --dry-run
```

## Code Style

- Python 3.12+
- Type hints required
- Use `Path` from `pathlib` for all file operations
- Keep agent implementations minimal - override `transform_*` methods only when needed
