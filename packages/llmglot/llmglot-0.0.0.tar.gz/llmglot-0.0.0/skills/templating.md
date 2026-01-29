# Templating Skill

How to use Jinja2 templates in llmglot skills and AGENTS.md.

{% if agent_name %}
> **{{ agent_name }}**: This file was rendered using the templating system it describes!
{% endif %}

## Available Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `{{ '{{' }} agent_name {{ '}}' }}` | Human-readable name | "Claude", "Cursor" |
| `{{ '{{' }} agent_id {{ '}}' }}` | CLI identifier | "claude", "cursor" |
| `{{ '{{' }} skill_name {{ '}}' }}` | Skill file stem (skills only) | "add-agent" |

## Examples

### Conditional Content

```jinja2
{{ '{%' }} if agent_id == "claude" {{ '%}' }}
Use /help for Claude Code assistance.
{{ '{%' }} elif agent_id == "cursor" {{ '%}' }}
Use Cmd+K for inline edits.
{{ '{%' }} endif {{ '%}' }}
```

### Agent-Specific Instructions

```markdown
# Project Guide for {{ '{{' }} agent_name {{ '}}' }}

You are working with {{ '{{' }} agent_name {{ '}}' }}.
{{ '{%' }} if agent_id in ["claude", "cline"] {{ '%}' }}
You have access to bash commands and file operations.
{{ '{%' }} else {{ '%}' }}
Focus on code suggestions and completions.
{{ '{%' }} endif {{ '%}' }}
```

## Escaping

To output literal braces, use:
- `{{ '{{' }} '{{ '{{' }}' {{ '}}' }}` for `{{ '{{' }}`
- `{{ '{{' }} '{{ '}}' }}' {{ '}}' }}` for `{{ '}}' }}`
