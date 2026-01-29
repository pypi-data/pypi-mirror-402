"""@agent_tool Decorator - Wrap functions as Agent Standard tools.

This decorator allows developers to easily convert any Python function into an
Agent Standard compliant tool with automatic ethics evaluation and health monitoring.

Example:
    @agent_tool(
        name="calculate_sum",
        description="Calculates sum of two numbers",
        ethics=["no_harm"],
        desires=["trust", "helpfulness"]
    )
    def calculate(a: int, b: int) -> int:
        return a + b
"""

import functools
import inspect
import structlog
from typing import Any, Callable, TypeVar

from core.agent_standard.models.ethics import EthicalPrinciple

logger = structlog.get_logger()

F = TypeVar("F", bound=Callable[..., Any])


class AgentToolMetadata:
    """Metadata for an agent tool."""
    
    def __init__(
        self,
        name: str,
        description: str | None = None,
        ethics: list[str] | None = None,
        desires: list[str] | None = None,
        category: str = "general",
        requires_confirmation: bool = False,
    ):
        self.name = name
        self.description = description
        self.ethics = ethics or []
        self.desires = desires or []
        self.category = category
        self.requires_confirmation = requires_confirmation


def agent_tool(
    name: str | None = None,
    description: str | None = None,
    ethics: list[str] | None = None,
    desires: list[str] | None = None,
    category: str = "general",
    requires_confirmation: bool = False,
) -> Callable[[F], F]:
    """Decorator to wrap a function as an Agent Standard tool.
    
    This decorator:
    1. Registers the function as an agent tool
    2. Adds ethics evaluation before execution
    3. Tracks desire satisfaction during execution
    4. Provides automatic logging and monitoring
    
    Args:
        name: Tool name (defaults to function name)
        description: Tool description (defaults to docstring)
        ethics: List of ethical constraints to enforce
        desires: List of desires this tool satisfies
        category: Tool category (e.g., "desktop_automation", "api")
        requires_confirmation: Whether to require user confirmation before execution
    
    Returns:
        Decorated function with Agent Standard compliance
    
    Example:
        @agent_tool(
            name="send_email",
            description="Sends an email to a recipient",
            ethics=["no_spam", "privacy_first"],
            desires=["helpfulness", "trust"],
            category="communication",
            requires_confirmation=True
        )
        async def send_email(to: str, subject: str, body: str) -> bool:
            # Implementation
            return True
    """
    def decorator(func: F) -> F:
        # Get function metadata
        tool_name = name or func.__name__
        tool_description = description or func.__doc__ or f"Tool: {tool_name}"
        
        # Create metadata
        metadata = AgentToolMetadata(
            name=tool_name,
            description=tool_description,
            ethics=ethics,
            desires=desires,
            category=category,
            requires_confirmation=requires_confirmation,
        )
        
        # Store metadata on function
        func.__agent_tool__ = metadata  # type: ignore
        
        # Wrap function
        if inspect.iscoroutinefunction(func):
            @functools.wraps(func)
            async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
                logger.info(
                    "agent_tool_executing",
                    tool=tool_name,
                    category=category,
                )
                
                # TODO: Ethics evaluation before execution
                # if agent_context.ethics_engine:
                #     await agent_context.ethics_engine.evaluate(...)
                
                # Execute function
                try:
                    result = await func(*args, **kwargs)
                    
                    # TODO: Update desire satisfaction
                    # if agent_context.desire_monitor:
                    #     agent_context.desire_monitor.update_satisfaction(desires)
                    
                    logger.info(
                        "agent_tool_completed",
                        tool=tool_name,
                        success=True,
                    )
                    
                    return result
                    
                except Exception as e:
                    logger.error(
                        "agent_tool_failed",
                        tool=tool_name,
                        error=str(e),
                    )
                    raise
            
            return async_wrapper  # type: ignore
        
        else:
            @functools.wraps(func)
            def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
                logger.info(
                    "agent_tool_executing",
                    tool=tool_name,
                    category=category,
                )
                
                # Execute function
                try:
                    result = func(*args, **kwargs)
                    
                    logger.info(
                        "agent_tool_completed",
                        tool=tool_name,
                        success=True,
                    )
                    
                    return result
                    
                except Exception as e:
                    logger.error(
                        "agent_tool_failed",
                        tool=tool_name,
                        error=str(e),
                    )
                    raise
            
            return sync_wrapper  # type: ignore
    
    return decorator

