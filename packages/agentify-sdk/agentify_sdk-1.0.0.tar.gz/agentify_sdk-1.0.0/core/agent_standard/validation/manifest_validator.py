"""Manifest Validator - Validates Agent Manifests.

Ensures that agent manifests comply with Agent Standard v1 requirements.
"""

import structlog
from typing import Any
from pydantic import ValidationError

from core.agent_standard.models.manifest import AgentManifest

logger = structlog.get_logger()


class ValidationResult:
    """Result of manifest validation."""
    
    def __init__(self):
        self.is_valid = True
        self.errors: list[str] = []
        self.warnings: list[str] = []
    
    def add_error(self, error: str) -> None:
        """Add a validation error."""
        self.errors.append(error)
        self.is_valid = False
    
    def add_warning(self, warning: str) -> None:
        """Add a validation warning."""
        self.warnings.append(warning)
    
    def __repr__(self) -> str:
        if self.is_valid:
            return f"ValidationResult(valid=True, warnings={len(self.warnings)})"
        return f"ValidationResult(valid=False, errors={len(self.errors)}, warnings={len(self.warnings)})"


class ManifestValidator:
    """Validates agent manifests against Agent Standard v1.
    
    Checks:
    - Required fields are present
    - Authority separation (Four-Eyes Principle)
    - Ethics and desires are configured
    - IO contracts are valid
    - Revision history is present
    """
    
    REQUIRED_FIELDS = [
        "agent_id",
        "name",
        "version",
        "status",
        "revisions",
        "overview",
        "capabilities",
        "ethics",
        "desires",
        "authority",
        "io",
    ]
    
    def validate(self, manifest: AgentManifest | dict[str, Any]) -> ValidationResult:
        """Validate a manifest.
        
        Args:
            manifest: AgentManifest instance or dict
        
        Returns:
            ValidationResult with errors and warnings
        """
        result = ValidationResult()
        
        # If dict, try to parse as AgentManifest
        if isinstance(manifest, dict):
            try:
                manifest = AgentManifest(**manifest)
            except ValidationError as e:
                for error in e.errors():
                    field = ".".join(str(x) for x in error["loc"])
                    result.add_error(f"{field}: {error['msg']}")
                return result
        
        # Validate required fields (Pydantic already does this, but double-check)
        self._validate_required_fields(manifest, result)
        
        # Validate authority separation
        self._validate_authority(manifest, result)
        
        # Validate ethics
        self._validate_ethics(manifest, result)
        
        # Validate desires
        self._validate_desires(manifest, result)
        
        # Validate IO
        self._validate_io(manifest, result)
        
        # Validate revisions
        self._validate_revisions(manifest, result)
        
        logger.info(
            "Manifest validation complete",
            agent_id=manifest.agent_id,
            is_valid=result.is_valid,
            errors=len(result.errors),
            warnings=len(result.warnings),
        )
        
        return result
    
    def _validate_required_fields(
        self,
        manifest: AgentManifest,
        result: ValidationResult,
    ) -> None:
        """Validate that all required fields are present."""
        # Pydantic already enforces this, but we can add custom checks
        pass
    
    def _validate_authority(
        self,
        manifest: AgentManifest,
        result: ValidationResult,
    ) -> None:
        """Validate authority configuration."""
        # Check that instruction and oversight are different
        if manifest.authority.instruction.id == manifest.authority.oversight.id:
            result.add_error(
                "Authority violation: instruction and oversight must be different entities"
            )
        
        # Check that oversight is marked as independent
        if not manifest.authority.oversight.independent:
            result.add_error("Authority violation: oversight must be independent")
        
        # Warn if escalation channels are limited
        if len(manifest.authority.escalation.channels) < 2:
            result.add_warning(
                "Limited escalation channels - consider adding more options"
            )
    
    def _validate_ethics(
        self,
        manifest: AgentManifest,
        result: ValidationResult,
    ) -> None:
        """Validate ethics configuration."""
        # Check that ethics framework is defined
        if not manifest.ethics.framework:
            result.add_error("Ethics framework must be specified")
        
        # Warn if no hard constraints
        if not manifest.ethics.hard_constraints:
            result.add_warning(
                "No hard constraints defined - consider adding ethical boundaries"
            )
        
        # Warn if no principles
        if not manifest.ethics.principles:
            result.add_warning(
                "No ethical principles defined - consider adding guiding principles"
            )
    
    def _validate_desires(
        self,
        manifest: AgentManifest,
        result: ValidationResult,
    ) -> None:
        """Validate desires configuration."""
        # Check that desires are defined
        if not manifest.desires.profile:
            result.add_warning(
                "No desires defined - health monitoring will be limited"
            )
        
        # Check that weights sum to 1.0 (Pydantic validator already does this)
        pass
    
    def _validate_io(
        self,
        manifest: AgentManifest,
        result: ValidationResult,
    ) -> None:
        """Validate IO configuration."""
        # Check that IO is defined
        if not manifest.io:
            result.add_error("IO configuration must be defined")
    
    def _validate_revisions(
        self,
        manifest: AgentManifest,
        result: ValidationResult,
    ) -> None:
        """Validate revision history."""
        # Check that current revision exists
        if not manifest.revisions.current_revision:
            result.add_error("Current revision must be specified")
        
        # Warn if no history
        if not manifest.revisions.history:
            result.add_warning(
                "No revision history - consider documenting changes"
            )

