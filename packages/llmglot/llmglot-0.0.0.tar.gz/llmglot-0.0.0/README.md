# llmglot

A CLI tool for syncing canonical LLM agent configuration files across different coding assistants.

## Why llmglot?

Managing configurations for multiple AI coding assistants is tedious. Each tool has its own location for instructions and skills:

- Claude uses `CLAUDE.md` and `.claude/skills/`
- Cursor uses `.cursorrules` and `.cursor/rules/`
- Windsurf uses `.windsurfrules` and `.windsurf/rules/`
- And so on...

**llmglot** lets you maintain a single source of truth (`LLMGLOT.md` + `skills/`) and sync it everywhere.

## Installation

```bash
pip install llmglot
```

Or with [uv](https://github.com/astral-sh/uv):

```bash
uv add llmglot
```

## Quick Start

1. Create your canonical config:

```bash
# Create LLMGLOT.md with your project instructions
echo "# My Project\n\nProject-specific instructions for AI assistants." > LLMGLOT.md

# Create skills directory
mkdir -p skills
echo "# Code Review\n\nWhen reviewing code, check for..." > skills/code-review.md
```

2. Sync to all agents:

```bash
llmglot sync all
```

That's it! Your config is now available to Claude, Cursor, Windsurf, Copilot, Cline, and Gemini.

## Usage

```bash
# Preview what will be synced (recommended first step)
llmglot sync all --dry-run

# Sync everything to all agents
llmglot sync all

# Sync only to specific agents
llmglot sync all --target claude --target cursor

# Sync only skills or only the main instructions
llmglot sync skills
llmglot sync agents
```

## Supported Agents

| Agent | Skills Directory | Instructions File |
|-------|------------------|-------------------|
| Claude | `.claude/skills/` | `CLAUDE.md` |
| Cursor | `.cursor/rules/` | `.cursorrules` |
| Windsurf | `.windsurf/rules/` | `.windsurfrules` |
| Copilot | `.github/copilot-skills/` | `.github/copilot-instructions.md` |
| Cline | `.cline/rules/` | `.clinerules` |
| Gemini | `.gemini/skills/` | `GEMINI.md` |

## Templating

Use Jinja2 templates to customize content per agent:

```markdown
# Project Guide

{% if agent_name %}
You are **{{ agent_name }}**.
{% endif %}

{% if agent_id == "claude" %}
Use /help for assistance.
{% elif agent_id == "cursor" %}
Use Cmd+K for inline edits.
{% endif %}
```

### Available Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `{{ agent_name }}` | Human-readable name | "Claude", "Cursor" |
| `{{ agent_id }}` | CLI identifier | "claude", "cursor" |
| `{{ skill_name }}` | Skill file stem (skills only) | "code-review" |

## Project Structure

```
your-project/
├── LLMGLOT.md          # Canonical instructions (synced to all agents)
├── skills/             # Reusable skills
│   ├── code-review.md
│   └── testing.md
├── CLAUDE.md           # Generated - don't edit directly
├── .cursorrules        # Generated - don't edit directly
└── ...
```

## License

MIT
