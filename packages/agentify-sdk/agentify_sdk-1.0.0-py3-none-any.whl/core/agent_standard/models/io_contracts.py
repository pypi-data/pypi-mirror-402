"""IO Contracts - Input/Output Schemas.

IO Contracts define the interface between agents and their environment.
They ensure type safety and compatibility across agent interactions.
"""

from typing import Any
from pydantic import BaseModel, Field


class InputSchema(BaseModel):
    """Schema definition for agent input.
    
    Uses JSON Schema format for validation.
    """
    
    type: str = Field(
        default="object",
        description="JSON Schema type",
    )
    
    properties: dict[str, Any] = Field(
        default_factory=dict,
        description="Schema properties (JSON Schema format)",
    )
    
    required: list[str] = Field(
        default_factory=list,
        description="Required property names",
    )
    
    additional_properties: bool = Field(
        default=False,
        description="Whether additional properties are allowed",
    )
    
    def validate_data(self, data: dict) -> tuple[bool, list[str]]:
        """Validate data against this schema.
        
        Returns:
            (is_valid, errors)
        """
        errors = []
        
        # Check required fields
        for field in self.required:
            if field not in data:
                errors.append(f"Missing required field: {field}")
        
        # Check for unexpected fields
        if not self.additional_properties:
            for field in data:
                if field not in self.properties:
                    errors.append(f"Unexpected field: {field}")
        
        return len(errors) == 0, errors


class OutputSchema(BaseModel):
    """Schema definition for agent output.
    
    Uses JSON Schema format for validation.
    """
    
    type: str = Field(
        default="object",
        description="JSON Schema type",
    )
    
    properties: dict[str, Any] = Field(
        default_factory=dict,
        description="Schema properties (JSON Schema format)",
    )
    
    required: list[str] = Field(
        default_factory=list,
        description="Required property names",
    )
    
    def validate_data(self, data: dict) -> tuple[bool, list[str]]:
        """Validate data against this schema.
        
        Returns:
            (is_valid, errors)
        """
        errors = []
        
        # Check required fields
        for field in self.required:
            if field not in data:
                errors.append(f"Missing required field: {field}")
        
        return len(errors) == 0, errors


class IOContract(BaseModel):
    """Complete IO contract for an agent capability.
    
    Defines the input and output schemas for a specific agent function.
    """
    
    name: str = Field(
        ...,
        description="Name of this contract (e.g., 'meeting_summary_v1')",
    )
    
    version: str = Field(
        default="1.0.0",
        description="Contract version (semantic versioning)",
    )
    
    description: str | None = Field(
        default=None,
        description="Human-readable description of what this contract does",
    )
    
    input_schema: InputSchema = Field(
        ...,
        description="Schema for input data",
    )
    
    output_schema: OutputSchema = Field(
        ...,
        description="Schema for output data",
    )
    
    input_formats: list[str] = Field(
        default_factory=lambda: ["json"],
        description="Supported input formats (e.g., 'json', 'text', 'audio')",
    )
    
    output_formats: list[str] = Field(
        default_factory=lambda: ["json"],
        description="Supported output formats (e.g., 'json', 'markdown', 'text')",
    )
    
    class Config:
        """Pydantic config."""
        json_schema_extra = {
            "example": {
                "name": "meeting_summary_v1",
                "version": "1.0.0",
                "description": "Summarize meeting transcript and extract action items",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "transcript": {"type": "string"},
                        "participants": {"type": "array", "items": {"type": "string"}},
                    },
                    "required": ["transcript"],
                },
                "output_schema": {
                    "type": "object",
                    "properties": {
                        "summary": {"type": "string"},
                        "action_items": {"type": "array"},
                        "decisions": {"type": "array"},
                    },
                    "required": ["summary"],
                },
                "input_formats": ["json", "text"],
                "output_formats": ["json", "markdown"],
            }
        }

