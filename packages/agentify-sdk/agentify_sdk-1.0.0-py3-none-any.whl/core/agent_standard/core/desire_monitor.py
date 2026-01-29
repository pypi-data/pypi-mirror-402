"""Desire Monitor - Health Monitoring & Alignment Indicators.

The Desire Monitor continuously tracks desire satisfaction and
calculates agent health. Persistent degradation triggers oversight.

This is NOT documentation - this is a RUNTIME-ACTIVE monitoring layer.
"""

import asyncio
import structlog
from typing import Callable, Any
from datetime import datetime

from core.agent_standard.models.desires import DesireProfile, DesireHealth

logger = structlog.get_logger()


class DesireMonitor:
    """Runtime desire monitoring and health tracking.
    
    Continuously monitors desire satisfaction and calculates health state.
    Triggers oversight escalation when health degrades.
    """
    
    def __init__(
        self,
        profile: DesireProfile,
        health_callback: Callable[[DesireHealth], None] | None = None,
    ):
        """Initialize desire monitor.
        
        Args:
            profile: The desire profile to monitor
            health_callback: Optional callback for health updates
        """
        self.profile = profile
        self.health_callback = health_callback
        self.current_health: DesireHealth | None = None
        self.health_history: list[DesireHealth] = []
        self.monitoring_task: asyncio.Task | None = None
        self.is_running = False
        
        logger.info(
            "DesireMonitor initialized",
            desires=len(profile.profile),
            reporting_interval=profile.health_signals.reporting_interval_sec,
        )
    
    async def start(self) -> None:
        """Start continuous health monitoring."""
        if self.is_running:
            logger.warning("DesireMonitor already running")
            return
        
        self.is_running = True
        self.monitoring_task = asyncio.create_task(self._monitor_loop())
        logger.info("DesireMonitor started")
    
    async def stop(self) -> None:
        """Stop health monitoring."""
        if not self.is_running:
            return
        
        self.is_running = False
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
        
        logger.info("DesireMonitor stopped")
    
    async def _monitor_loop(self) -> None:
        """Main monitoring loop."""
        interval = self.profile.health_signals.reporting_interval_sec
        
        while self.is_running:
            try:
                # Calculate current health
                health = self.profile.calculate_health()
                self.current_health = health
                self.health_history.append(health)
                
                # Keep only last 100 health states
                if len(self.health_history) > 100:
                    self.health_history = self.health_history[-100:]
                
                # Log health state
                logger.info(
                    "Health check",
                    state=health.state,
                    tension=health.tension,
                    unsatisfied=len(health.unsatisfied_desires),
                )
                
                # Call health callback if provided
                if self.health_callback:
                    try:
                        self.health_callback(health)
                    except Exception as e:
                        logger.error("Health callback failed", error=str(e))
                
                # Check if escalation is needed
                if self._should_escalate(health):
                    logger.warning(
                        "Health degradation - escalation needed",
                        state=health.state,
                        tension=health.tension,
                    )
                    # Escalation is handled by OversightController
                
                # Wait for next interval
                await asyncio.sleep(interval)
            
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Error in monitoring loop", error=str(e))
                await asyncio.sleep(interval)
    
    def _should_escalate(self, health: DesireHealth) -> bool:
        """Check if health state requires escalation."""
        threshold = self.profile.health_signals.escalation_threshold
        
        # Map threshold name to state
        threshold_states = {
            "stressed": ["stressed", "degraded", "critical"],
            "degraded": ["degraded", "critical"],
            "critical": ["critical"],
        }
        
        return health.state in threshold_states.get(threshold, ["critical"])
    
    def update_desire_satisfaction(
        self,
        desire_id: str,
        satisfaction: float,
    ) -> None:
        """Update satisfaction level for a specific desire.
        
        Args:
            desire_id: ID of the desire to update
            satisfaction: New satisfaction level (0.0 to 1.0)
        """
        self.profile.update_satisfaction(desire_id, satisfaction)
        logger.debug(
            "Desire satisfaction updated",
            desire_id=desire_id,
            satisfaction=satisfaction,
        )
    
    def get_current_health(self) -> DesireHealth:
        """Get current health state."""
        if self.current_health is None:
            return self.profile.calculate_health()
        return self.current_health
    
    def get_health_trend(self, window: int = 10) -> str:
        """Get health trend over recent history.
        
        Args:
            window: Number of recent health states to analyze
        
        Returns:
            "improving", "stable", or "degrading"
        """
        if len(self.health_history) < 2:
            return "stable"
        
        recent = self.health_history[-window:]
        if len(recent) < 2:
            return "stable"
        
        # Compare average tension in first half vs second half
        mid = len(recent) // 2
        first_half_avg = sum(h.tension for h in recent[:mid]) / mid
        second_half_avg = sum(h.tension for h in recent[mid:]) / (len(recent) - mid)
        
        if second_half_avg < first_half_avg - 0.05:
            return "improving"
        elif second_half_avg > first_half_avg + 0.05:
            return "degrading"
        else:
            return "stable"
    
    def get_stats(self) -> dict[str, Any]:
        """Get monitoring statistics."""
        return {
            "current_health": self.current_health.state if self.current_health else "unknown",
            "current_tension": self.current_health.tension if self.current_health else 0.0,
            "health_checks": len(self.health_history),
            "trend": self.get_health_trend(),
            "is_running": self.is_running,
        }

