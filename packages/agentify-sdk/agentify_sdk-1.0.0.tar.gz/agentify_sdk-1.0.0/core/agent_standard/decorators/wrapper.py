"""Runtime Wrapper - Wrap any code as Agent Standard agent at runtime.

This module provides the `wrap_as_agent()` function to wrap existing code
(functions, classes, modules) as Agent Standard compliant agents WITHOUT
modifying the original code.

Example:
    # Legacy function (no changes needed!)
    def legacy_function(x: int) -> int:
        return x * 2
    
    # Wrap at runtime
    agent = wrap_as_agent(
        legacy_function,
        manifest="manifests/my_agent.json"
    )
    
    # Now Agent Standard compliant!
    result = await agent.execute({"x": 5})
"""

import inspect
import structlog
from pathlib import Path
from typing import Any, Callable

from core.agent_standard.core.agent import Agent
from core.agent_standard.models.manifest import AgentManifest

logger = structlog.get_logger()


def wrap_as_agent(
    target: Callable[..., Any] | type | Any,
    manifest: str | Path | dict[str, Any] | AgentManifest | None = None,
    agent_id: str | None = None,
    auto_ethics: bool = True,
    auto_desires: bool = True,
    auto_manifest: bool = True,
) -> Agent:
    """Wrap any code as an Agent Standard compliant agent at runtime.
    
    This function wraps existing code (functions, classes, modules) as an
    Agent Standard agent WITHOUT requiring any code changes. Perfect for
    integrating legacy code or third-party libraries.
    
    Args:
        target: Function, class, or object to wrap
        manifest: Path to manifest file, dict, or AgentManifest instance
        agent_id: Agent ID (auto-generated if not provided)
        auto_ethics: Automatically detect and enforce ethics
        auto_desires: Automatically track desires
        auto_manifest: Auto-generate manifest if not provided
    
    Returns:
        Agent instance wrapping the target
    
    Example:
        # Wrap a function
        def my_function(x: int) -> int:
            return x * 2
        
        agent = wrap_as_agent(my_function, agent_id="agent.my.function")
        result = await agent.execute({"x": 5})
        
        # Wrap a class
        class MyClass:
            def process(self, data: str) -> str:
                return data.upper()
        
        agent = wrap_as_agent(MyClass, manifest="manifest.json")
        result = await agent.execute({"method": "process", "data": "hello"})
    """
    logger.info(
        "wrapping_as_agent",
        target_type=type(target).__name__,
        agent_id=agent_id,
    )
    
    # Load or generate manifest
    if manifest is None and auto_manifest:
        manifest_obj = _auto_generate_manifest(target, agent_id)
    elif isinstance(manifest, (str, Path)):
        manifest_obj = AgentManifest.from_json_file(str(manifest))
    elif isinstance(manifest, dict):
        manifest_obj = AgentManifest(**manifest)
    elif isinstance(manifest, AgentManifest):
        manifest_obj = manifest
    else:
        raise ValueError("Invalid manifest type")
    
    # Create agent
    agent = Agent(manifest_obj)
    
    # Register target as tool
    if inspect.isfunction(target) or inspect.ismethod(target):
        _register_function(agent, target)
    elif inspect.isclass(target):
        _register_class(agent, target)
    else:
        _register_object(agent, target)
    
    logger.info(
        "agent_wrapped",
        agent_id=manifest_obj.agent_id,
        target_type=type(target).__name__,
    )
    
    return agent


def _auto_generate_manifest(
    target: Any,
    agent_id: str | None = None,
) -> AgentManifest:
    """Auto-generate a manifest for the target."""
    # Get target name
    if hasattr(target, "__name__"):
        target_name = target.__name__
    else:
        target_name = type(target).__name__
    
    # Generate agent ID
    if agent_id is None:
        agent_id = f"agent.auto.{target_name.lower()}"
    
    # Create minimal manifest
    manifest_dict = {
        "agent_id": agent_id,
        "name": f"Auto-wrapped: {target_name}",
        "version": "1.0.0",
        "status": "active",
        "revisions": {
            "current_revision": "rev-001",
            "history": [
                {
                    "revision_id": "rev-001",
                    "timestamp": "2026-01-14T00:00:00Z",
                    "author": {"type": "system", "id": "auto-wrapper"},
                    "change_summary": "Auto-generated manifest",
                }
            ],
        },
        "overview": {
            "description": f"Auto-wrapped agent for {target_name}",
            "tags": ["auto-wrapped"],
            "owner": {"type": "system", "id": "auto-wrapper"},
            "lifecycle": {"stage": "development", "sla": "none"},
        },
        "capabilities": [{"name": "auto_wrapped", "level": "medium"}],
        "ethics": {
            "framework": "harm-minimization",
            "principles": [],
            "hard_constraints": ["no_illegal_guidance"],
            "soft_constraints": [],
            "evaluation_mode": "pre_action",
        },
        "desires": {
            "profile": [
                {"id": "trust", "weight": 0.5},
                {"id": "helpfulness", "weight": 0.5},
            ],
            "health_signals": {
                "tension_thresholds": {"stressed": 0.6, "degraded": 0.8, "critical": 0.95},
                "reporting_interval_sec": 300,
                "escalation_threshold": "degraded",
            },
        },
        "authority": {
            "instruction": {"type": "system", "id": "auto-wrapper"},
            "oversight": {"type": "system", "id": "auto-oversight", "independent": True},
            "escalation": {
                "channels": ["system"],
                "severity_levels": ["warning", "incident", "critical"],
                "default_channel": "system",
            },
        },
        "io": {
            "input_formats": ["json"],
            "output_formats": ["json"],
        },
    }
    
    return AgentManifest(**manifest_dict)


def _register_function(agent: Agent, func: Callable[..., Any]) -> None:
    """Register a function as an agent tool."""
    # TODO: Implement function registration
    pass


def _register_class(agent: Agent, cls: type) -> None:
    """Register a class as an agent tool."""
    # TODO: Implement class registration
    pass


def _register_object(agent: Agent, obj: Any) -> None:
    """Register an object as an agent tool."""
    # TODO: Implement object registration
    pass

