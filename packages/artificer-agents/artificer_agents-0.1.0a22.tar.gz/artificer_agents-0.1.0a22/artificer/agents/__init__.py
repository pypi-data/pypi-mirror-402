"""Agent CLI integration for Artificer.

This module provides:
- register_agent() for registering agents with the CLI
- CLI commands for managing and running agents

Example usage:

    from pydantic_ai import Agent
    from artificer.agents import register_agent

    my_agent = Agent(
        'openai:gpt-4o',
        instructions='You are a helpful assistant.',
    )
    register_agent('my-agent', my_agent)

Then use the CLI:

    artificer agents list
    artificer agents run my-agent "Hello!"
"""

from artificer.agents.base import (
    ArtificerAgent,
    Skill,
)
from artificer.agents.debugger import run_with_debug
from artificer.agents.features import AgentsFeature
from artificer.agents.registry import (
    clear_registry,
    get_agent,
    list_agents,
    register_agent,
)

__all__ = [
    "AgentsFeature",
    "ArtificerAgent",
    "Skill",
    "clear_registry",
    "get_agent",
    "list_agents",
    "register_agent",
    "run_with_debug",
]
