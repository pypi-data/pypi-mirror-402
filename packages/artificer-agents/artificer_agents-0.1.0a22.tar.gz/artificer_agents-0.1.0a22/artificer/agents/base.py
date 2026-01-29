"""ArtificerAgent - composable agents with skills."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from pydantic_ai import Agent, Tool
from pydantic_ai.mcp import MCPServer


class Skill(ABC):
    """Base class for agent skills.

    A skill provides:
    - Tools the agent can use
    - MCP servers for external tools
    - Instructions on how to use them

    Skills are instantiated per-agent, so they can hold instance state.
    Tool names are prefixed with the skill name (e.g., planning__plan).
    """

    @property
    def name(self) -> str:
        """Short name for this skill (used as tool prefix).

        Derived from class name: PlanningSkill -> planning
        Override to customize.
        """
        class_name = self.__class__.__name__
        if class_name.endswith("Skill"):
            class_name = class_name[:-5]
        return class_name.lower()

    @property
    @abstractmethod
    def instructions(self) -> str:
        """Instructions for using this skill."""
        ...

    def get_tools(self) -> list[Tool]:
        """Return the tools this skill provides. Override to add tools."""
        return []

    def get_mcp_servers(self) -> list[MCPServer]:
        """Return MCP servers this skill requires. Override to add servers.

        Returns list of pydantic-ai MCP server instances (e.g., MCPServerStdio).
        """
        return []


class ArtificerAgent(Agent[None, str]):
    """Base agent with composable skills.

    Subclass and define skills to create capable agents:

        class MyAgent(ArtificerAgent):
            skills = [MyCustomSkill]

        agent = MyAgent("openai:gpt-4o", instructions="You are a developer.")
        result = await agent.run("Build a CLI tool")

    Skills contribute tools and instructions that are automatically
    appended to the system prompt.
    """

    skills: list[type[Skill]] = []

    def __init__(
        self,
        model: str,
        *,
        name: str | None = None,
        tools: list[Any] | None = None,
        **kwargs: Any,
    ):
        # Instantiate skills
        self._skill_instances: list[Skill] = [skill_cls() for skill_cls in self.skills]

        # Collect tools from skills + user tools
        all_tools = list(tools or [])
        for skill in self._skill_instances:
            all_tools.extend(skill.get_tools())

        # Collect MCP servers from skills
        all_mcp_servers: list[MCPServer] = list(kwargs.pop("mcp_servers", None) or [])
        for skill in self._skill_instances:
            all_mcp_servers.extend(skill.get_mcp_servers())

        # Build system prompt from user instructions + skill instructions
        user_instructions = kwargs.pop("instructions", None) or ""
        skill_instructions = self._build_skill_instructions()
        parts = [p for p in [user_instructions, skill_instructions] if p]
        system_prompt = "\n\n".join(parts)

        # Only pass mcp_servers if we have any
        if all_mcp_servers:
            kwargs["mcp_servers"] = all_mcp_servers

        super().__init__(
            model,
            system_prompt=system_prompt or (),
            name=name or self.__class__.__name__.lower(),
            tools=all_tools,
            **kwargs,
        )

    def _build_skill_instructions(self) -> str:
        """Build instructions from skills."""
        sections = []
        for skill in self._skill_instances:
            sections.append(f"## {skill.name.title()} Skill\n{skill.instructions}")
        return "\n\n".join(sections)

    def get_skill(self, skill_type: type[Skill]) -> Skill | None:
        """Get an instantiated skill by type."""
        for skill in self._skill_instances:
            if isinstance(skill, skill_type):
                return skill
        return None
