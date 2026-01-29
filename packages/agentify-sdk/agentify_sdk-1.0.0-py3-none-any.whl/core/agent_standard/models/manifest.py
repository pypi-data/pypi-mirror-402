"""Agent Manifest - Complete Agent Definition.

The Agent Manifest is the single source of truth for an agent.
It defines ALL aspects of the agent: identity, ethics, desires,
authority, capabilities, and runtime configuration.

The manifest is framework-agnostic and portable across environments.
"""

from typing import Any, Literal
from datetime import datetime
from pydantic import BaseModel, Field, model_validator

from core.agent_standard.models.ethics import EthicsFramework
from core.agent_standard.models.desires import DesireProfile
from core.agent_standard.models.authority import Authority
from core.agent_standard.models.io_contracts import IOContract


class Revision(BaseModel):
    """A single revision in the agent's history."""
    
    revision_id: str = Field(..., description="Unique revision identifier")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    author: dict[str, str] = Field(..., description="Who made this revision")
    change_summary: str = Field(..., description="What changed in this revision")


class RevisionHistory(BaseModel):
    """Complete revision history for an agent."""
    
    current_revision: str = Field(..., description="Current active revision ID")
    history: list[Revision] = Field(default_factory=list, description="All revisions")


class Overview(BaseModel):
    """High-level agent overview."""
    
    description: str = Field(..., description="What this agent does")
    tags: list[str] = Field(default_factory=list, description="Searchable tags")
    owner: dict[str, str] = Field(..., description="Who owns this agent")
    lifecycle: dict[str, str] = Field(
        default_factory=lambda: {"stage": "development", "sla": "none"}
    )


class Capability(BaseModel):
    """A single agent capability."""
    
    name: str = Field(..., description="Capability name")
    level: Literal["low", "medium", "high", "expert"] = Field(
        default="medium",
        description="Proficiency level",
    )
    description: str | None = Field(default=None, description="What this capability does")


class AIModel(BaseModel):
    """AI model configuration."""
    
    provider: str = Field(..., description="Model provider (e.g., 'openai', 'anthropic')")
    model: str = Field(..., description="Model name/version")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=4000, ge=1)
    additional_params: dict[str, Any] = Field(default_factory=dict)


class FrameworkAdapter(BaseModel):
    """Framework adapter configuration (optional)."""
    
    name: str = Field(
        ...,
        description="Framework name (e.g., 'langchain', 'n8n', 'make', 'custom')",
    )
    version: str = Field(..., description="Framework version")
    mode: str = Field(..., description="Execution mode (e.g., 'agent_executor', 'workflow')")
    entrypoint: str = Field(..., description="How to start this agent")


class Tool(BaseModel):
    """A tool the agent can use."""

    name: str = Field(..., description="Tool name")
    description: str = Field(..., description="What this tool does")
    category: str | None = Field(default=None, description="Tool category")
    executor: str | None = Field(default=None, description="Python path to executor class")
    input_schema: dict[str, Any] = Field(..., description="Input schema (JSON Schema)")
    output_schema: dict[str, Any] = Field(..., description="Output schema (JSON Schema)")
    connection: dict[str, Any] = Field(
        default_factory=dict,
        description="Connection status and configuration",
    )
    policies: dict[str, Any] = Field(
        default_factory=dict,
        description="Tool usage policies (rate limits, approval requirements, etc.)",
    )


class Activity(BaseModel):
    """A single activity in the execution queue."""

    id: str = Field(..., description="Activity ID")
    type: str = Field(..., description="Activity type (e.g., 'tool_call', 'scheduled_job')")
    tool: str | None = Field(default=None, description="Tool name if type is 'tool_call'")
    job_id: str | None = Field(default=None, description="Job ID if type is 'scheduled_job'")
    params: dict[str, Any] = Field(default_factory=dict, description="Activity parameters")
    status: Literal["queued", "running", "completed", "failed"] = Field(
        default="queued",
        description="Activity status",
    )
    started_at: datetime | None = Field(default=None, description="When activity started")
    completed_at: datetime | None = Field(default=None, description="When activity completed")
    progress: float = Field(default=0.0, ge=0.0, le=1.0, description="Progress (0.0 to 1.0)")
    scheduled_for: datetime | None = Field(default=None, description="When activity is scheduled for")


class ExecutionState(BaseModel):
    """Current execution state."""

    current_activity: str | None = Field(default=None, description="Current activity ID")
    queue_length: int = Field(default=0, ge=0, description="Number of queued activities")
    avg_execution_time_ms: float = Field(default=0.0, ge=0.0, description="Average execution time in ms")


class Activities(BaseModel):
    """Activity queue and execution state."""

    queue: list[Activity] = Field(default_factory=list, description="Activity queue")
    execution_state: ExecutionState = Field(
        default_factory=ExecutionState,
        description="Current execution state",
    )


class Prompt(BaseModel):
    """System prompt configuration."""

    system: str = Field(..., description="System prompt")
    user_template: str | None = Field(default=None, description="User message template")
    assistant_template: str | None = Field(default=None, description="Assistant message template")
    temperature: float | None = Field(default=None, ge=0.0, le=2.0, description="LLM temperature override")
    max_tokens: int | None = Field(default=None, ge=1, description="Max tokens override")


class InputValidation(BaseModel):
    """Input validation configuration."""

    max_length: int = Field(default=10000, ge=1, description="Maximum input length")
    allowed_formats: list[str] = Field(default_factory=list, description="Allowed input formats")
    content_filters: list[str] = Field(default_factory=list, description="Content filters to apply")


class OutputValidation(BaseModel):
    """Output validation configuration."""

    max_length: int = Field(default=5000, ge=1, description="Maximum output length")
    required_format: str | None = Field(default=None, description="Required output format")
    content_filters: list[str] = Field(default_factory=list, description="Content filters to apply")


class Guardrails(BaseModel):
    """Guardrails configuration."""

    input_validation: InputValidation = Field(
        default_factory=InputValidation,
        description="Input validation rules",
    )
    output_validation: OutputValidation = Field(
        default_factory=OutputValidation,
        description="Output validation rules",
    )
    tool_usage_policies: dict[str, dict[str, Any]] = Field(
        default_factory=dict,
        description="Per-tool usage policies",
    )


class AgentManifest(BaseModel):
    """Complete Agent Manifest - Single Source of Truth.
    
    This is the canonical definition of an agent. It includes ALL
    required fields per the Agent Standard v1 specification.
    
    The manifest is:
    - Framework-agnostic (works with any runtime)
    - Portable (same definition works on Cloud/Edge/Desktop)
    - Validatable (enforces required fields and constraints)
    - Auditable (includes revision history)
    """
    
    # ========== REQUIRED FIELDS (per Agent Standard v1) ==========
    
    agent_id: str = Field(
        ...,
        description="Unique agent identifier (e.g., 'agent.demo.meet-harmony')",
    )
    
    name: str = Field(..., description="Human-readable agent name")
    
    version: str = Field(..., description="Agent version (semantic versioning)")
    
    status: Literal["draft", "active", "paused", "retired"] = Field(
        ...,
        description="Current agent status",
    )
    
    revisions: RevisionHistory = Field(..., description="Revision history")
    
    overview: Overview = Field(..., description="High-level overview")
    
    capabilities: list[Capability] = Field(
        default_factory=list,
        description="Agent capabilities",
    )
    
    ethics: EthicsFramework = Field(
        ...,
        description="Ethics framework (RUNTIME-ACTIVE)",
    )
    
    desires: DesireProfile = Field(
        ...,
        description="Desire profile (RUNTIME-ACTIVE)",
    )
    
    authority: Authority = Field(
        ...,
        description="Authority configuration (Four-Eyes Principle)",
    )
    
    io: dict[str, Any] = Field(
        ...,
        description="Input/output configuration",
    )
    
    # ========== OPTIONAL FIELDS ==========
    
    ai_model: AIModel | None = Field(default=None, description="AI model configuration")
    
    framework_adapter: FrameworkAdapter | None = Field(
        default=None,
        description="Framework adapter (optional but recommended)",
    )
    
    tools: list[Tool] = Field(default_factory=list, description="Available tools")
    
    knowledge: dict[str, Any] = Field(
        default_factory=dict,
        description="Knowledge base configuration (RAG, etc.)",
    )
    
    memory: dict[str, Any] = Field(
        default_factory=dict,
        description="Memory configuration",
    )
    
    schedule: dict[str, Any] = Field(
        default_factory=dict,
        description="Scheduled jobs",
    )

    activities: Activities = Field(
        default_factory=Activities,
        description="Activity queue and execution state",
    )

    prompt: Prompt | None = Field(
        default=None,
        description="System prompt configuration",
    )

    guardrails: Guardrails = Field(
        default_factory=Guardrails,
        description="Guardrails configuration",
    )

    team: dict[str, Any] = Field(
        default_factory=dict,
        description="Team relationships",
    )

    customers: dict[str, Any] = Field(
        default_factory=dict,
        description="Customer assignments",
    )

    pricing: dict[str, Any] = Field(
        default_factory=dict,
        description="Pricing configuration",
    )

    observability: dict[str, Any] = Field(
        default_factory=dict,
        description="Observability configuration (logs, traces, incidents)",
    )
    
    @model_validator(mode="after")
    def validate_manifest(self) -> "AgentManifest":
        """Validate the complete manifest."""
        # Authority validation is handled by Authority model
        # Additional cross-field validation can go here
        return self
    
    def to_json_file(self, path: str) -> None:
        """Save manifest to JSON file."""
        import json
        with open(path, "w") as f:
            json.dump(self.model_dump(mode="json"), f, indent=2, default=str)
    
    @classmethod
    def from_json_file(cls, path: str) -> "AgentManifest":
        """Load manifest from JSON file."""
        import json
        with open(path, "r") as f:
            data = json.load(f)
        return cls(**data)
    
    class Config:
        """Pydantic config."""
        json_schema_extra = {
            "title": "Agent Manifest v1",
            "description": "Complete agent definition per Agent Standard v1",
        }

