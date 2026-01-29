"""Oversight Controller - Four-Eyes Principle Implementation.

The Oversight Controller enforces the separation between Instruction
and Oversight authorities. It monitors agent behavior, audits decisions,
and escalates issues.

This implements the Four-Eyes Principle: at least one independent
controller reviews, monitors, or audits the agent's behavior.
"""

import structlog
from typing import Any, Literal
from datetime import datetime
from enum import Enum

from core.agent_standard.models.authority import Authority
from core.agent_standard.models.desires import DesireHealth

logger = structlog.get_logger()


class IncidentSeverity(str, Enum):
    """Incident severity levels."""
    WARNING = "warning"
    INCIDENT = "incident"
    CRITICAL = "critical"


class Incident(dict):
    """An incident report."""
    
    def __init__(
        self,
        severity: IncidentSeverity,
        category: str,
        message: str,
        details: dict[str, Any] | None = None,
    ):
        super().__init__(
            timestamp=datetime.utcnow().isoformat(),
            severity=severity.value,
            category=category,
            message=message,
            details=details or {},
        )


class OversightController:
    """Oversight and escalation controller.
    
    Responsibilities:
    - Monitor agent behavior
    - Audit decisions and actions
    - Escalate issues to oversight authority
    - Track incidents and violations
    - Enforce Four-Eyes Principle
    """
    
    def __init__(self, authority: Authority):
        """Initialize oversight controller.
        
        Args:
            authority: Authority configuration (must have separate oversight)
        """
        self.authority = authority
        self.incidents: list[Incident] = []
        self.escalation_count = 0
        
        logger.info(
            "OversightController initialized",
            instruction_authority=authority.instruction.id,
            oversight_authority=authority.oversight.id,
        )
    
    def report_incident(
        self,
        severity: IncidentSeverity,
        category: str,
        message: str,
        details: dict[str, Any] | None = None,
        auto_escalate: bool = True,
    ) -> Incident:
        """Report an incident.
        
        Args:
            severity: Incident severity level
            category: Incident category (e.g., 'ethics_violation', 'health_degraded')
            message: Human-readable incident message
            details: Additional incident details
            auto_escalate: Whether to auto-escalate based on severity
        
        Returns:
            The created incident
        """
        incident = Incident(severity, category, message, details)
        self.incidents.append(incident)
        
        logger.warning(
            "Incident reported",
            severity=severity.value,
            category=category,
            message=message,
        )
        
        # Auto-escalate if needed
        if auto_escalate and self.authority.should_auto_escalate(category):
            self.escalate_incident(incident)
        
        return incident
    
    def escalate_incident(
        self,
        incident: Incident,
        channel: str | None = None,
    ) -> None:
        """Escalate an incident to oversight authority.
        
        Args:
            incident: The incident to escalate
            channel: Escalation channel (defaults to configured default)
        """
        if channel is None:
            channel = self.authority.escalation.default_channel
        
        if not self.authority.can_escalate_to(channel):
            logger.error(
                "Invalid escalation channel",
                channel=channel,
                available=self.authority.escalation.channels,
            )
            return
        
        self.escalation_count += 1
        
        logger.critical(
            "Incident escalated to oversight",
            oversight_authority=self.authority.oversight.id,
            channel=channel,
            severity=incident["severity"],
            category=incident["category"],
            message=incident["message"],
        )
        
        # TODO: Implement actual escalation mechanisms
        # - Send email/webhook
        # - Notify oversight agent
        # - Create ticket in oversight system
        # - etc.
    
    def report_health_degradation(self, health: DesireHealth) -> None:
        """Report health degradation.
        
        Args:
            health: Current health state
        """
        if health.state in ["degraded", "critical"]:
            severity = (
                IncidentSeverity.CRITICAL
                if health.state == "critical"
                else IncidentSeverity.INCIDENT
            )
            
            self.report_incident(
                severity=severity,
                category="health_degraded",
                message=f"Agent health degraded: {health.state}",
                details={
                    "tension": health.tension,
                    "unsatisfied_desires": health.unsatisfied_desires,
                    "timestamp": health.timestamp.isoformat(),
                },
            )
    
    def report_ethics_violation(
        self,
        violations: list[str],
        action: dict[str, Any],
    ) -> None:
        """Report ethics violation.
        
        Args:
            violations: List of violated constraints
            action: The action that was blocked
        """
        self.report_incident(
            severity=IncidentSeverity.CRITICAL,
            category="ethics_violation",
            message=f"Ethics violation: {', '.join(violations)}",
            details={
                "violations": violations,
                "action": action,
            },
        )
    
    def audit_action(
        self,
        action: dict[str, Any],
        result: dict[str, Any],
    ) -> None:
        """Audit a completed action.
        
        Args:
            action: The action that was executed
            result: The result of the action
        """
        logger.debug(
            "Action audited",
            action_type=action.get("type"),
            success=result.get("success", False),
        )
        
        # TODO: Implement actual auditing
        # - Log to audit trail
        # - Check for anomalies
        # - Validate against policies
        # - etc.
    
    def get_stats(self) -> dict[str, Any]:
        """Get oversight statistics."""
        return {
            "total_incidents": len(self.incidents),
            "escalations": self.escalation_count,
            "incidents_by_severity": {
                "warning": len([i for i in self.incidents if i["severity"] == "warning"]),
                "incident": len([i for i in self.incidents if i["severity"] == "incident"]),
                "critical": len([i for i in self.incidents if i["severity"] == "critical"]),
            },
            "oversight_authority": self.authority.oversight.id,
        }
    
    def get_recent_incidents(self, limit: int = 10) -> list[Incident]:
        """Get recent incidents.
        
        Args:
            limit: Maximum number of incidents to return
        
        Returns:
            List of recent incidents
        """
        return self.incidents[-limit:]

