"""Agent implementations for different LLM coding assistants."""

from llmglot.agents.base import Agent, get_agent, get_all_agents
from llmglot.agents.claude import ClaudeAgent
from llmglot.agents.cursor import CursorAgent
from llmglot.agents.windsurf import WindsurfAgent
from llmglot.agents.copilot import CopilotAgent
from llmglot.agents.cline import ClineAgent
from llmglot.agents.gemini import GeminiAgent

__all__ = [
    "Agent",
    "get_agent",
    "get_all_agents",
    "ClaudeAgent",
    "CursorAgent",
    "WindsurfAgent",
    "CopilotAgent",
    "ClineAgent",
    "GeminiAgent",
]
