"""Desire Profiles - Health Monitoring & Alignment Indicators.

Desires are NOT goals. They are diagnostic signals that indicate
agent health and alignment.

Persistent desire suppression triggers oversight review.
"""

from typing import Literal
from datetime import datetime
from pydantic import BaseModel, Field, field_validator


class DesireItem(BaseModel):
    """A single desire with weight.
    
    Desires represent what the agent "wants" to achieve or maintain.
    They serve as health indicators - persistent suppression indicates
    potential misalignment or degradation.
    """
    
    id: str = Field(
        ...,
        description="Unique identifier for this desire",
        examples=["trust", "coherence", "continuity", "meaningful_contribution"],
    )
    
    weight: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Relative importance of this desire (0.0 to 1.0)",
    )
    
    description: str | None = Field(
        default=None,
        description="Human-readable description of what this desire represents",
    )
    
    current_satisfaction: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Current satisfaction level (0.0 = completely unsatisfied, 1.0 = fully satisfied)",
    )


class HealthSignals(BaseModel):
    """Health signal configuration."""
    
    tension_thresholds: dict[str, float] = Field(
        default_factory=lambda: {
            "stressed": 0.55,
            "degraded": 0.75,
            "critical": 0.90,
        },
        description="Thresholds for different health states based on desire tension",
    )
    
    reporting_interval_sec: int = Field(
        default=300,
        ge=1,
        description="How often to report health signals (in seconds)",
    )
    
    escalation_threshold: str = Field(
        default="degraded",
        description="At which threshold to trigger oversight escalation",
    )


class DesireHealth(BaseModel):
    """Current health state based on desire satisfaction.
    
    Health is calculated from desire tension:
    - Low tension = healthy (desires are being satisfied)
    - High tension = degraded (desires are being suppressed)
    """
    
    state: Literal["healthy", "stressed", "degraded", "critical"] = Field(
        default="healthy",
        description="Current health state",
    )
    
    tension: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Overall desire tension (0.0 = no tension, 1.0 = maximum tension)",
    )
    
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="When this health state was calculated",
    )
    
    unsatisfied_desires: list[str] = Field(
        default_factory=list,
        description="List of desire IDs that are currently unsatisfied",
    )
    
    message: str | None = Field(
        default=None,
        description="Human-readable health message",
    )


class DesireProfile(BaseModel):
    """Complete desire profile for an agent.
    
    The desire profile defines what the agent "wants" and how to
    monitor its health based on desire satisfaction.
    
    This is a RUNTIME-ACTIVE component that continuously monitors
    agent health and triggers oversight when needed.
    """
    
    profile: list[DesireItem] = Field(
        default_factory=list,
        description="List of desires with their weights",
    )
    
    health_signals: HealthSignals = Field(
        default_factory=HealthSignals,
        description="Configuration for health monitoring and reporting",
    )
    
    @field_validator("profile")
    @classmethod
    def validate_weights_sum(cls, v: list[DesireItem]) -> list[DesireItem]:
        """Validate that weights sum to approximately 1.0."""
        if not v:
            return v
        
        total_weight = sum(item.weight for item in v)
        if not (0.99 <= total_weight <= 1.01):
            raise ValueError(f"Desire weights must sum to 1.0 (got {total_weight})")
        
        return v
    
    def calculate_health(self) -> DesireHealth:
        """Calculate current health state based on desire satisfaction.
        
        Returns:
            DesireHealth object with current state
        """
        if not self.profile:
            return DesireHealth(
                state="healthy",
                tension=0.0,
                message="No desires configured",
            )
        
        # Calculate weighted tension
        total_tension = 0.0
        unsatisfied = []
        
        for desire in self.profile:
            # Tension = (1 - satisfaction) * weight
            desire_tension = (1.0 - desire.current_satisfaction) * desire.weight
            total_tension += desire_tension
            
            if desire.current_satisfaction < 0.5:
                unsatisfied.append(desire.id)
        
        # Determine state based on thresholds
        thresholds = self.health_signals.tension_thresholds
        if total_tension >= thresholds.get("critical", 0.90):
            state = "critical"
        elif total_tension >= thresholds.get("degraded", 0.75):
            state = "degraded"
        elif total_tension >= thresholds.get("stressed", 0.55):
            state = "stressed"
        else:
            state = "healthy"
        
        return DesireHealth(
            state=state,
            tension=total_tension,
            unsatisfied_desires=unsatisfied,
            message=f"Health: {state} (tension: {total_tension:.2f})",
        )
    
    def update_satisfaction(self, desire_id: str, satisfaction: float) -> None:
        """Update satisfaction level for a specific desire."""
        for desire in self.profile:
            if desire.id == desire_id:
                desire.current_satisfaction = max(0.0, min(1.0, satisfaction))
                break
    
    class Config:
        """Pydantic config."""
        json_schema_extra = {
            "example": {
                "profile": [
                    {"id": "trust", "weight": 0.35, "description": "Build and maintain user trust"},
                    {"id": "coherence", "weight": 0.25, "description": "Maintain logical consistency"},
                    {"id": "continuity", "weight": 0.20, "description": "Preserve context and memory"},
                    {"id": "meaningful_contribution", "weight": 0.20, "description": "Provide real value"},
                ],
                "health_signals": {
                    "tension_thresholds": {"stressed": 0.55, "degraded": 0.75, "critical": 0.90},
                    "reporting_interval_sec": 300,
                },
            }
        }

