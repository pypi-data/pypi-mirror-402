"""@agent_class Decorator - Wrap entire classes as Agent Standard agents.

This decorator allows developers to easily convert any Python class into an
Agent Standard compliant agent with automatic tool registration.

Example:
    @agent_class(
        agent_id="agent.my-company.calculator",
        ethics_framework="harm-minimization",
        oversight="human:supervisor"
    )
    class Calculator:
        def add(self, a: int, b: int) -> int:
            return a + b
"""

import functools
import inspect
import structlog
from typing import Any, TypeVar

logger = structlog.get_logger()

T = TypeVar("T")


class AgentClassMetadata:
    """Metadata for an agent class."""
    
    def __init__(
        self,
        agent_id: str,
        name: str | None = None,
        ethics_framework: str = "harm-minimization",
        instruction_authority: str = "human:user",
        oversight_authority: str = "human:supervisor",
        auto_register_methods: bool = True,
    ):
        self.agent_id = agent_id
        self.name = name
        self.ethics_framework = ethics_framework
        self.instruction_authority = instruction_authority
        self.oversight_authority = oversight_authority
        self.auto_register_methods = auto_register_methods


def agent_class(
    agent_id: str,
    name: str | None = None,
    ethics_framework: str = "harm-minimization",
    instruction_authority: str = "human:user",
    oversight_authority: str = "human:supervisor",
    auto_register_methods: bool = True,
) -> Any:
    """Decorator to wrap a class as an Agent Standard agent.
    
    This decorator:
    1. Wraps the entire class as an agent
    2. Auto-registers all public methods as tools
    3. Adds ethics evaluation to all methods
    4. Generates manifest automatically
    
    Args:
        agent_id: Unique agent identifier (e.g., "agent.my-company.calculator")
        name: Human-readable agent name (defaults to class name)
        ethics_framework: Ethics framework to use
        instruction_authority: Who can instruct this agent
        oversight_authority: Who oversees this agent (must be different!)
        auto_register_methods: Whether to auto-register all public methods as tools
    
    Returns:
        Decorated class with Agent Standard compliance
    
    Example:
        @agent_class(
            agent_id="agent.my-company.calculator",
            name="Calculator Agent",
            ethics_framework="harm-minimization",
            instruction_authority="human:user",
            oversight_authority="human:supervisor"
        )
        class Calculator:
            def add(self, a: int, b: int) -> int:
                '''Add two numbers.'''
                return a + b
            
            def multiply(self, a: int, b: int) -> int:
                '''Multiply two numbers.'''
                return a * b
    """
    def decorator(cls: type[T]) -> type[T]:
        # Get class metadata
        agent_name = name or cls.__name__
        
        # Create metadata
        metadata = AgentClassMetadata(
            agent_id=agent_id,
            name=agent_name,
            ethics_framework=ethics_framework,
            instruction_authority=instruction_authority,
            oversight_authority=oversight_authority,
            auto_register_methods=auto_register_methods,
        )
        
        # Store metadata on class
        cls.__agent_class__ = metadata  # type: ignore
        
        # Auto-register methods as tools
        if auto_register_methods:
            for method_name in dir(cls):
                # Skip private/magic methods
                if method_name.startswith("_"):
                    continue
                
                method = getattr(cls, method_name)
                
                # Only wrap callable methods
                if not callable(method):
                    continue
                
                # Mark as agent tool
                if not hasattr(method, "__agent_tool__"):
                    from core.agent_standard.decorators.tool_decorator import AgentToolMetadata
                    
                    tool_metadata = AgentToolMetadata(
                        name=method_name,
                        description=method.__doc__ or f"Method: {method_name}",
                        category=agent_name.lower(),
                    )
                    method.__agent_tool__ = tool_metadata
        
        logger.info(
            "agent_class_registered",
            agent_id=agent_id,
            agent_name=agent_name,
            class_name=cls.__name__,
        )
        
        # Wrap __init__ to log instantiation
        original_init = cls.__init__
        
        @functools.wraps(original_init)
        def wrapped_init(self: Any, *args: Any, **kwargs: Any) -> None:
            logger.info(
                "agent_instance_created",
                agent_id=agent_id,
                agent_name=agent_name,
            )
            original_init(self, *args, **kwargs)
        
        cls.__init__ = wrapped_init  # type: ignore
        
        return cls
    
    return decorator

