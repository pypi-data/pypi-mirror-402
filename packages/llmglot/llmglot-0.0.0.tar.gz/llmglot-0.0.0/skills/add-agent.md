# Add Agent Skill

Guide for adding support for a new LLM coding assistant to llmglot.

{% if agent_name %}
> **{{ agent_name }}**: This skill explains how to add new agents like yourself to llmglot.
{% endif %}

## Steps

1. **Create the agent module** at `src/llmglot/agents/<agent_id>.py`:

```python
from pathlib import Path
from llmglot.agents.base import Agent, register_agent

@register_agent
class NewAgent(Agent):
    @property
    def name(self) -> str:
        return "Agent Name"

    @property
    def id(self) -> str:
        return "agent_id"

    @property
    def skills_dir(self) -> Path:
        return Path(".agent/skills")

    @property
    def agent_file(self) -> Path:
        return Path(".agentrules")
```

2. **Add the import** to `src/llmglot/agents/__init__.py`:

```python
from llmglot.agents.new_agent import NewAgent
```

3. **Add to `__all__`** in the same file.

4. **Test the new agent**:

```bash
uv run llmglot sync skills --target agent_id --dry-run
```

## Optional: Custom Transformations

Override `transform_skill` or `transform_agents_md` if the agent needs special formatting:

```python
def transform_skill(self, content: str, skill_name: str) -> str:
    # Add agent-specific header
    return f"<!-- Agent skill: {skill_name} -->\n{content}"
```
