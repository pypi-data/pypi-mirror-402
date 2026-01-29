# Sync Workflow Skill

Best practices for using llmglot to sync agent configurations.

{% if agent_name %}
> **{{ agent_name }}**: You're reading a synced copy. Edit `skills/{{ skill_name }}.md` to modify.
{% endif %}

## Recommended Workflow

1. **Edit canonical files only**
   - Modify `AGENTS.md` for project instructions
   - Add/edit files in `skills/` for reusable skills
   - Never edit agent-specific files directly (they get overwritten)

2. **Preview with dry-run**
   ```bash
   uv run llmglot sync all --dry-run
   ```

3. **Sync to all agents**
   ```bash
   uv run llmglot sync all
   ```

4. **Or sync selectively**
   ```bash
   uv run llmglot sync skills --target claude
   uv run llmglot sync agents --target cursor
   ```

## Using Template Variables

Make skills agent-aware with Jinja2:

```markdown
# My Skill

This skill is configured for {{ '{{' }} agent_name {{ '}}' }}.

Agent ID: {{ '{{' }} agent_id {{ '}}' }}
```

## Gitignore Recommendations

Add agent-specific directories to `.gitignore` if you only want canonical files in version control:

```
# Agent-specific (generated)
.claude/
.cursor/
.windsurf/
.cline/
.github/copilot-*
CLAUDE.md
.cursorrules
.windsurfrules
.clinerules
```

Or keep them tracked to ensure all team members have the same config.
