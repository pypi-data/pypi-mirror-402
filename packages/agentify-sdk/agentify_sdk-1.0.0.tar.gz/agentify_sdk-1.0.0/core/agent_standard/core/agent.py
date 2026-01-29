"""Agent - Universal Agent Implementation.

The Agent class is the main entry point for creating and running agents.
It wraps the runtime, ethics engine, desire monitor, and oversight controller
into a single, easy-to-use interface.

This is the CORE of the Agent Standard v1 implementation.
"""

import structlog
from typing import Any

from core.agent_standard.models.manifest import AgentManifest
from core.agent_standard.core.runtime import AgentRuntime, RuntimeEnvironment

logger = structlog.get_logger()


class Agent:
    """Universal Agent - Works on Cloud, Edge, and Desktop.
    
    The Agent class provides a simple, consistent interface for:
    - Creating agents from manifests
    - Starting and stopping agents
    - Executing tasks
    - Monitoring health and ethics
    - Accessing oversight and audit data
    
    Example:
        ```python
        # Load manifest
        manifest = AgentManifest.from_json_file("my_agent.json")
        
        # Create agent
        agent = Agent(manifest)
        
        # Start agent
        await agent.start()
        
        # Execute task
        result = await agent.execute({
            "type": "summarize_meeting",
            "input": {"transcript": "..."}
        })
        
        # Check health
        health = agent.get_health()
        print(f"Health: {health.state}, Tension: {health.tension}")
        
        # Stop agent
        await agent.stop()
        ```
    """
    
    def __init__(
        self,
        manifest: AgentManifest,
        environment: RuntimeEnvironment = RuntimeEnvironment.DESKTOP,
    ):
        """Initialize agent.
        
        Args:
            manifest: The agent manifest (validated)
            environment: Runtime environment (cloud/edge/desktop)
        """
        self.manifest = manifest
        self.runtime = AgentRuntime(manifest, environment)
        
        logger.info(
            "Agent initialized",
            agent_id=manifest.agent_id,
            name=manifest.name,
            version=manifest.version,
        )
    
    @classmethod
    def from_manifest_file(
        cls,
        path: str,
        environment: RuntimeEnvironment = RuntimeEnvironment.DESKTOP,
    ) -> "Agent":
        """Create agent from manifest file.
        
        Args:
            path: Path to manifest JSON file
            environment: Runtime environment
        
        Returns:
            Agent instance
        """
        manifest = AgentManifest.from_json_file(path)
        return cls(manifest, environment)
    
    async def start(self) -> None:
        """Start the agent.
        
        This starts:
        - Desire monitoring (health tracking)
        - Scheduled jobs (if any)
        - Framework adapter (if configured)
        """
        logger.info("Starting agent", agent_id=self.manifest.agent_id)
        await self.runtime.start()
    
    async def stop(self) -> None:
        """Stop the agent.
        
        This stops all background tasks and cleans up resources.
        """
        logger.info("Stopping agent", agent_id=self.manifest.agent_id)
        await self.runtime.stop()
    
    async def execute(
        self,
        task: dict[str, Any],
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Execute a task.
        
        The task is:
        1. Validated against ethics (pre-action)
        2. Executed via framework adapter
        3. Audited by oversight
        4. Used to update desire satisfaction
        
        Args:
            task: The task to execute
            context: Optional execution context
        
        Returns:
            Execution result
        
        Raises:
            EthicsViolation: If task violates ethical constraints
        """
        return await self.runtime.execute(task, context)
    
    def get_health(self) -> Any:
        """Get current health state.
        
        Returns:
            DesireHealth object with current state
        """
        return self.runtime.desire_monitor.get_current_health()
    
    def get_status(self) -> dict[str, Any]:
        """Get complete agent status.
        
        Returns:
            Status dict with health, ethics, oversight, etc.
        """
        return self.runtime.get_status()
    
    def get_incidents(self, limit: int = 10) -> list[Any]:
        """Get recent incidents.
        
        Args:
            limit: Maximum number of incidents to return
        
        Returns:
            List of recent incidents
        """
        return self.runtime.oversight.get_recent_incidents(limit)
    
    def report_incident(
        self,
        severity: str,
        category: str,
        message: str,
        details: dict[str, Any] | None = None,
    ) -> Any:
        """Report an incident (non-punitive).
        
        Agents can report incidents, uncertainty, or ethical conflicts
        without negative consequences.
        
        Args:
            severity: "warning", "incident", or "critical"
            category: Incident category
            message: Human-readable message
            details: Additional details
        
        Returns:
            The created incident
        """
        from core.agent_standard.core.oversight import IncidentSeverity
        
        severity_enum = IncidentSeverity(severity)
        return self.runtime.oversight.report_incident(
            severity_enum,
            category,
            message,
            details,
        )
    
    def __repr__(self) -> str:
        """String representation."""
        return (
            f"Agent(id={self.manifest.agent_id}, "
            f"name={self.manifest.name}, "
            f"version={self.manifest.version}, "
            f"status={self.manifest.status})"
        )

