"""Agent Runtime - Universal Runtime Wrapper.

The Agent Runtime provides a universal execution environment that works
identically across Cloud, Edge, and Desktop deployments.

The same agent manifest runs the same way everywhere.
"""

import asyncio
import structlog
from typing import Any, Literal
from enum import Enum

from core.agent_standard.models.manifest import AgentManifest
from core.agent_standard.core.ethics_engine import EthicsEngine
from core.agent_standard.core.desire_monitor import DesireMonitor
from core.agent_standard.core.oversight import OversightController

logger = structlog.get_logger()


class RuntimeEnvironment(str, Enum):
    """Runtime environment types."""
    CLOUD = "cloud"
    EDGE = "edge"
    DESKTOP = "desktop"


class AgentRuntime:
    """Universal agent runtime.
    
    Provides a consistent execution environment across:
    - Cloud (Railway, AWS, Azure, etc.)
    - Edge (IoT devices, local servers)
    - Desktop (Windows, Mac, Linux)
    
    The runtime:
    - Loads and validates the agent manifest
    - Initializes ethics engine, desire monitor, and oversight
    - Provides execution hooks for framework adapters
    - Ensures compliance with Agent Standard v1
    """
    
    def __init__(
        self,
        manifest: AgentManifest,
        environment: RuntimeEnvironment = RuntimeEnvironment.DESKTOP,
    ):
        """Initialize agent runtime.
        
        Args:
            manifest: The agent manifest to run
            environment: Runtime environment (cloud/edge/desktop)
        """
        self.manifest = manifest
        self.environment = environment
        
        # Initialize core components
        self.ethics_engine = EthicsEngine(manifest.ethics)
        self.desire_monitor = DesireMonitor(
            manifest.desires,
            health_callback=self._on_health_update,
        )
        self.oversight = OversightController(manifest.authority)
        
        self.is_running = False
        self.execution_count = 0
        
        logger.info(
            "AgentRuntime initialized",
            agent_id=manifest.agent_id,
            version=manifest.version,
            environment=environment.value,
        )
    
    async def start(self) -> None:
        """Start the agent runtime."""
        if self.is_running:
            logger.warning("Runtime already running")
            return
        
        logger.info("Starting agent runtime", agent_id=self.manifest.agent_id)
        
        # Start desire monitoring
        await self.desire_monitor.start()
        
        self.is_running = True
        logger.info("Agent runtime started")
    
    async def stop(self) -> None:
        """Stop the agent runtime."""
        if not self.is_running:
            return
        
        logger.info("Stopping agent runtime", agent_id=self.manifest.agent_id)
        
        # Stop desire monitoring
        await self.desire_monitor.stop()
        
        self.is_running = False
        logger.info("Agent runtime stopped")
    
    async def execute(
        self,
        task: dict[str, Any],
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Execute a task.
        
        This is the main execution entry point. It:
        1. Validates the task against ethics
        2. Executes the task (via framework adapter)
        3. Audits the result
        4. Updates desire satisfaction
        
        Args:
            task: The task to execute
            context: Optional execution context
        
        Returns:
            Execution result
        """
        if not self.is_running:
            raise RuntimeError("Runtime not started - call start() first")
        
        self.execution_count += 1
        
        logger.info(
            "Executing task",
            agent_id=self.manifest.agent_id,
            task_type=task.get("type"),
            execution_count=self.execution_count,
        )
        
        try:
            # 1. Ethics check (PRE-ACTION)
            action = {"type": task.get("type"), "params": task}
            self.ethics_engine.evaluate_action(action)
            
            # 2. Execute task (via framework adapter)
            result = await self._execute_task(task, context or {})
            
            # 3. Audit result
            self.oversight.audit_action(action, result)
            
            # 4. Update desire satisfaction based on result
            self._update_desires_from_result(result)
            
            logger.info(
                "Task completed",
                agent_id=self.manifest.agent_id,
                success=result.get("success", False),
            )
            
            return result
        
        except Exception as e:
            logger.error(
                "Task execution failed",
                agent_id=self.manifest.agent_id,
                error=str(e),
            )
            
            # Report incident
            self.oversight.report_incident(
                severity=self.oversight.IncidentSeverity.INCIDENT,
                category="execution_error",
                message=f"Task execution failed: {str(e)}",
                details={"task": task, "error": str(e)},
            )
            
            return {
                "success": False,
                "error": str(e),
            }
    
    async def _execute_task(
        self,
        task: dict[str, Any],
        context: dict[str, Any],
    ) -> dict[str, Any]:
        """Execute the actual task.
        
        This is where framework adapters would plug in.
        For now, this is a placeholder.
        
        Args:
            task: The task to execute
            context: Execution context
        
        Returns:
            Execution result
        """
        # TODO: Implement framework adapter integration
        # This would delegate to:
        # - LangChain agent executor
        # - n8n workflow
        # - Make.com scenario
        # - Custom implementation
        
        logger.debug("Task execution (placeholder)", task_type=task.get("type"))
        
        return {
            "success": True,
            "message": "Task executed (placeholder)",
            "task": task,
        }
    
    def _update_desires_from_result(self, result: dict[str, Any]) -> None:
        """Update desire satisfaction based on execution result.
        
        Args:
            result: Execution result
        """
        # TODO: Implement intelligent desire satisfaction updates
        # For now, simple heuristic: success = slight satisfaction increase
        
        if result.get("success"):
            # Slightly increase all desires on success
            for desire in self.manifest.desires.profile:
                current = desire.current_satisfaction
                new_satisfaction = min(1.0, current + 0.05)
                self.desire_monitor.update_desire_satisfaction(
                    desire.id,
                    new_satisfaction,
                )
    
    def _on_health_update(self, health: Any) -> None:
        """Callback for health updates from desire monitor.
        
        Args:
            health: Current health state
        """
        # Report health degradation to oversight
        self.oversight.report_health_degradation(health)
    
    def get_status(self) -> dict[str, Any]:
        """Get runtime status."""
        return {
            "agent_id": self.manifest.agent_id,
            "version": self.manifest.version,
            "status": self.manifest.status,
            "environment": self.environment.value,
            "is_running": self.is_running,
            "execution_count": self.execution_count,
            "health": self.desire_monitor.get_current_health().model_dump(),
            "ethics_stats": self.ethics_engine.get_stats(),
            "oversight_stats": self.oversight.get_stats(),
        }

