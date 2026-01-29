"""Ethics Engine - Runtime-Active Ethical Constraint Evaluation.

The Ethics Engine evaluates EVERY action against the agent's ethical
framework BEFORE execution. Ethics override all other objectives.

This is NOT documentation - this is a RUNTIME-ACTIVE control layer.
"""

import structlog
from typing import Any

from core.agent_standard.models.ethics import EthicsFramework, EthicsPrinciple

logger = structlog.get_logger()


class EthicsViolation(Exception):
    """Raised when an action violates ethical constraints."""
    
    def __init__(self, violations: list[str]):
        self.violations = violations
        super().__init__(f"Ethics violation: {', '.join(violations)}")


class EthicsEngine:
    """Runtime ethics evaluation engine.
    
    Evaluates every action against the agent's ethical framework.
    Hard constraints BLOCK execution. Soft constraints generate warnings.
    """
    
    def __init__(self, framework: EthicsFramework):
        """Initialize ethics engine.
        
        Args:
            framework: The ethical framework to enforce
        """
        self.framework = framework
        self.violation_count = 0
        self.warning_count = 0
        
        logger.info(
            "EthicsEngine initialized",
            framework=framework.framework,
            hard_constraints=len(framework.hard_constraints),
            principles=len(framework.principles),
        )
    
    def evaluate_action(self, action: dict[str, Any]) -> tuple[bool, list[str]]:
        """Evaluate an action against ethical framework.
        
        Args:
            action: The action to evaluate (dict with 'type', 'params', etc.)
        
        Returns:
            (is_allowed, violations/warnings)
        
        Raises:
            EthicsViolation: If hard constraints are violated
        """
        logger.debug("Evaluating action", action_type=action.get("type"))
        
        # Evaluate using framework's validation
        is_valid, violations = self.framework.validate_action(action)
        
        # Separate hard violations from soft warnings
        hard_violations = [v for v in violations if "Hard constraint" in v]
        soft_warnings = [v for v in violations if "Soft constraint" in v]
        
        # Log warnings
        if soft_warnings:
            self.warning_count += len(soft_warnings)
            logger.warning(
                "Soft constraint warnings",
                action_type=action.get("type"),
                warnings=soft_warnings,
            )
        
        # Block on hard violations
        if hard_violations:
            self.violation_count += len(hard_violations)
            logger.error(
                "Hard constraint violation - action BLOCKED",
                action_type=action.get("type"),
                violations=hard_violations,
            )
            raise EthicsViolation(hard_violations)
        
        logger.debug("Action passed ethics check", action_type=action.get("type"))
        return is_valid, violations
    
    def evaluate_principle(
        self,
        principle_id: str,
        action: dict[str, Any],
    ) -> tuple[bool, str | None]:
        """Evaluate a specific principle against an action.
        
        Args:
            principle_id: ID of the principle to check
            action: The action to evaluate
        
        Returns:
            (is_compliant, violation_message)
        """
        principle = self.framework.get_principle(principle_id)
        if not principle:
            logger.warning("Unknown principle", principle_id=principle_id)
            return True, None
        
        # TODO: Implement actual principle evaluation
        # This would typically use LLM-based evaluation or rule-based checking
        # For now, we return compliant
        return True, None
    
    def get_stats(self) -> dict[str, Any]:
        """Get ethics engine statistics."""
        return {
            "framework": self.framework.framework,
            "total_violations": self.violation_count,
            "total_warnings": self.warning_count,
            "hard_constraints": len(self.framework.hard_constraints),
            "soft_constraints": len(self.framework.soft_constraints),
            "principles": len(self.framework.principles),
        }
    
    def reset_stats(self) -> None:
        """Reset violation and warning counters."""
        self.violation_count = 0
        self.warning_count = 0
        logger.info("Ethics stats reset")

