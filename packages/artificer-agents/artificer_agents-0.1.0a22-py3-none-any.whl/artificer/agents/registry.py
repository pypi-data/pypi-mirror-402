"""Simple registry for agents."""

from __future__ import annotations

from typing import Any

from pydantic_ai import Agent

# Global registry mapping names to agents
_agents: dict[str, Agent[Any, Any]] = {}


def register_agent(name: str, agent: Agent[Any, Any]) -> Agent[Any, Any]:
    """Register an agent with the CLI.

    Args:
        name: The name to register the agent under.
        agent: A pydantic-ai Agent instance.

    Returns:
        The agent (for chaining).

    Raises:
        TypeError: If agent is not a pydantic-ai Agent instance.

    Example:
        from pydantic_ai import Agent
        from artificer.agents import register_agent

        my_agent = Agent('openai:gpt-4o', instructions='Be helpful.')
        register_agent('my-agent', my_agent)
    """
    if not isinstance(agent, Agent):
        raise TypeError(
            f"agent must be a pydantic-ai Agent instance, got {type(agent).__name__}"
        )
    _agents[name] = agent
    return agent


def get_agent(name: str) -> Agent[Any, Any] | None:
    """Get a registered agent by name."""
    return _agents.get(name)


def list_agents() -> dict[str, Agent[Any, Any]]:
    """Get all registered agents."""
    return _agents.copy()


def clear_registry() -> None:
    """Clear all registered agents (useful for testing)."""
    _agents.clear()
