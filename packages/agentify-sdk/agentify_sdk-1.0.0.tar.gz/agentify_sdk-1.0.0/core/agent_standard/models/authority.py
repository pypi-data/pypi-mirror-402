"""Authority & Oversight - Four-Eyes Principle.

Every agent MUST have separate Instruction and Oversight authorities.
These MUST NOT be the same entity.

This enforces the Four-Eyes Principle: at least one independent
controller reviews, monitors, or audits the agent's behavior.
"""

from typing import Literal
from pydantic import BaseModel, Field, model_validator


class InstructionAuthority(BaseModel):
    """Entity that assigns tasks to the agent.
    
    The Instruction Authority is responsible for:
    - Assigning tasks and goals
    - Providing input and context
    - Defining success criteria
    """
    
    type: Literal["agent", "human", "org"] = Field(
        ...,
        description="Type of authority",
    )
    
    id: str = Field(
        ...,
        description="Unique identifier for this authority",
        examples=["orchestrator.agent.alpha", "jonas.mossler", "org.abacus-alpha"],
    )
    
    name: str | None = Field(
        default=None,
        description="Human-readable name",
    )
    
    contact: str | None = Field(
        default=None,
        description="Contact information (email, URL, etc.)",
    )


class OversightAuthority(BaseModel):
    """Entity that monitors and audits the agent.
    
    The Oversight Authority is responsible for:
    - Monitoring agent behavior
    - Auditing decisions and actions
    - Escalating issues
    - Reviewing health signals
    
    MUST be independent from Instruction Authority.
    """
    
    type: Literal["agent", "human", "org"] = Field(
        ...,
        description="Type of authority",
    )
    
    id: str = Field(
        ...,
        description="Unique identifier for this authority",
        examples=["watcher.agent.beta", "compliance.team", "ethics-board"],
    )
    
    independent: bool = Field(
        ...,
        description="MUST be True - oversight must be independent",
    )
    
    name: str | None = Field(
        default=None,
        description="Human-readable name",
    )
    
    contact: str | None = Field(
        default=None,
        description="Contact information (email, URL, etc.)",
    )
    
    escalation_policy: str | None = Field(
        default=None,
        description="Reference to escalation policy document",
    )
    
    @model_validator(mode="after")
    def validate_independent(self) -> "OversightAuthority":
        """Ensure oversight is marked as independent."""
        if not self.independent:
            raise ValueError("Oversight authority MUST be independent (independent=True)")
        return self


class EscalationConfig(BaseModel):
    """Configuration for incident escalation."""

    channels: list[Literal["human", "ethics-board", "system", "email", "webhook", "slack", "pagerduty", "teams", "discord"]] = Field(
        default_factory=lambda: ["human"],
        description="Available escalation channels",
    )
    
    severity_levels: list[Literal["warning", "incident", "critical"]] = Field(
        default_factory=lambda: ["warning", "incident", "critical"],
        description="Severity levels for escalation",
    )
    
    default_channel: str = Field(
        default="human",
        description="Default escalation channel",
    )
    
    auto_escalate_on: list[str] = Field(
        default_factory=lambda: ["ethics_violation", "health_critical"],
        description="Conditions that trigger automatic escalation",
    )


class Authority(BaseModel):
    """Complete authority configuration for an agent.
    
    Implements the Four-Eyes Principle:
    - Instruction Authority assigns tasks
    - Oversight Authority monitors and audits
    - These MUST be different entities
    """
    
    instruction: InstructionAuthority = Field(
        ...,
        description="Entity that assigns tasks to this agent",
    )
    
    oversight: OversightAuthority = Field(
        ...,
        description="Entity that monitors and audits this agent (MUST be independent)",
    )
    
    escalation: EscalationConfig = Field(
        default_factory=EscalationConfig,
        description="Escalation configuration",
    )
    
    @model_validator(mode="after")
    def validate_separation(self) -> "Authority":
        """Ensure instruction and oversight are different entities."""
        if self.instruction.id == self.oversight.id:
            raise ValueError(
                "Instruction and Oversight authorities MUST be different entities. "
                f"Both are set to: {self.instruction.id}"
            )
        return self
    
    def can_escalate_to(self, channel: str) -> bool:
        """Check if escalation to a specific channel is allowed."""
        return channel in self.escalation.channels
    
    def should_auto_escalate(self, condition: str) -> bool:
        """Check if a condition triggers automatic escalation."""
        return condition in self.escalation.auto_escalate_on
    
    class Config:
        """Pydantic config."""
        json_schema_extra = {
            "example": {
                "instruction": {
                    "type": "agent",
                    "id": "orchestrator.meetings",
                    "name": "Meeting Orchestrator",
                },
                "oversight": {
                    "type": "agent",
                    "id": "watcher.compliance",
                    "independent": True,
                    "name": "Compliance Watcher",
                },
                "escalation": {
                    "channels": ["human", "ethics-board", "system"],
                    "severity_levels": ["warning", "incident", "critical"],
                    "default_channel": "human",
                },
            }
        }

