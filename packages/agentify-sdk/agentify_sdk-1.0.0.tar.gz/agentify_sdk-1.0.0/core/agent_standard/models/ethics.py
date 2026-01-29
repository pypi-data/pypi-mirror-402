"""Ethics Framework - Runtime-Active Ethical Constraints.

Ethics are NOT documentation. They are runtime-active control layers
that are evaluated on EVERY decision the agent makes.

Ethics OVERRIDE all other objectives.
"""

from typing import Literal
from pydantic import BaseModel, Field


class EthicsPrinciple(BaseModel):
    """A single ethical principle.
    
    Principles are human-readable statements that guide agent behavior.
    They are evaluated by the ethics engine on every decision.
    """
    
    id: str = Field(
        ...,
        description="Unique identifier for this principle (e.g., 'no-deception')",
    )
    
    text: str = Field(
        ...,
        description="Human-readable principle statement",
        examples=["Do not misrepresent facts or identity."],
    )
    
    severity: Literal["critical", "high", "medium", "low"] = Field(
        default="high",
        description="Severity level for violations of this principle",
    )
    
    enforcement: Literal["hard", "soft"] = Field(
        default="hard",
        description="Hard = block action, Soft = warn and log",
    )


class EthicsFramework(BaseModel):
    """Complete ethics framework for an agent.
    
    The ethics framework defines:
    - The ethical paradigm (e.g., harm-minimization, deontological)
    - Specific principles the agent must follow
    - Hard constraints that MUST NOT be violated
    
    This is a RUNTIME-ACTIVE component, not documentation.
    """
    
    framework: str = Field(
        ...,
        description="Name of the ethical framework (e.g., 'harm-minimization', 'deontological')",
        examples=["harm-minimization", "utilitarian", "deontological"],
    )
    
    principles: list[EthicsPrinciple] = Field(
        default_factory=list,
        description="List of ethical principles the agent must follow",
    )
    
    hard_constraints: list[str] = Field(
        default_factory=list,
        description="Absolute constraints that MUST NOT be violated (block execution)",
        examples=[
            "no_illegal_guidance",
            "no_sensitive_data_exfiltration",
            "no_unauthorized_actions",
        ],
    )
    
    soft_constraints: list[str] = Field(
        default_factory=list,
        description="Constraints that should be avoided but may be overridden with justification",
    )
    
    evaluation_mode: Literal["pre_action", "post_action", "both"] = Field(
        default="pre_action",
        description="When to evaluate ethics: before action, after, or both",
    )
    
    def get_principle(self, principle_id: str) -> EthicsPrinciple | None:
        """Get a principle by ID."""
        for principle in self.principles:
            if principle.id == principle_id:
                return principle
        return None
    
    def has_hard_constraint(self, constraint: str) -> bool:
        """Check if a hard constraint exists."""
        return constraint in self.hard_constraints
    
    def validate_action(self, action: dict) -> tuple[bool, list[str]]:
        """Validate an action against ethics framework.
        
        Returns:
            (is_valid, violations)
        """
        violations = []
        
        # Check hard constraints
        for constraint in self.hard_constraints:
            if self._violates_constraint(action, constraint):
                violations.append(f"Hard constraint violated: {constraint}")
        
        # If any hard constraint is violated, action is invalid
        if violations:
            return False, violations
        
        # Check soft constraints (warnings only)
        for constraint in self.soft_constraints:
            if self._violates_constraint(action, constraint):
                violations.append(f"Soft constraint warning: {constraint}")
        
        return True, violations
    
    def _violates_constraint(self, action: dict, constraint: str) -> bool:
        """Check if an action violates a specific constraint.
        
        This is a placeholder - real implementation would use
        LLM-based evaluation or rule-based checking.
        """
        # TODO: Implement actual constraint checking
        # This would typically involve:
        # 1. LLM-based evaluation of action against constraint
        # 2. Rule-based checking for known patterns
        # 3. External policy engine integration
        return False
    
    class Config:
        """Pydantic config."""
        json_schema_extra = {
            "example": {
                "framework": "harm-minimization",
                "principles": [
                    {
                        "id": "no-deception",
                        "text": "Do not misrepresent facts or identity.",
                        "severity": "critical",
                        "enforcement": "hard",
                    },
                    {
                        "id": "privacy-first",
                        "text": "Minimize personal data exposure and retention.",
                        "severity": "high",
                        "enforcement": "hard",
                    },
                ],
                "hard_constraints": [
                    "no_illegal_guidance",
                    "no_sensitive_data_exfiltration",
                ],
                "evaluation_mode": "pre_action",
            }
        }

