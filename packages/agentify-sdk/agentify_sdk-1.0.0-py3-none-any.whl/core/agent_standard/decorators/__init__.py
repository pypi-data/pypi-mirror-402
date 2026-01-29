"""Agent Standard v1 - Decorators for Easy Integration.

This module provides decorators to easily wrap existing code into Agent Standard compliant agents.
"""

from core.agent_standard.decorators.tool_decorator import agent_tool
from core.agent_standard.decorators.class_decorator import agent_class
from core.agent_standard.decorators.wrapper import wrap_as_agent

__all__ = [
    "agent_tool",
    "agent_class",
    "wrap_as_agent",
]

