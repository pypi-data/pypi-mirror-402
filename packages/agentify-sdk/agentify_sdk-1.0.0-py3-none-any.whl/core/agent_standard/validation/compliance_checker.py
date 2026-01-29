"""Compliance Checker - Full Agent Standard v1 Compliance.

Performs comprehensive compliance checking against Agent Standard v1.
"""

import structlog
from typing import Any

from core.agent_standard.models.manifest import AgentManifest
from core.agent_standard.validation.manifest_validator import ManifestValidator, ValidationResult
from core.agent_standard.validation.authority_validator import AuthorityValidator

logger = structlog.get_logger()


class ComplianceChecker:
    """Comprehensive compliance checker for Agent Standard v1.
    
    Checks:
    - Manifest validity
    - Authority separation (Four-Eyes Principle)
    - Ethics configuration
    - Desires configuration
    - IO contracts
    - Revision history
    - Framework adapter compatibility
    """
    
    def __init__(self):
        self.manifest_validator = ManifestValidator()
        self.authority_validator = AuthorityValidator()
    
    def check_compliance(
        self,
        manifest: AgentManifest | dict[str, Any],
    ) -> ValidationResult:
        """Perform full compliance check.
        
        Args:
            manifest: Agent manifest to check
        
        Returns:
            ValidationResult with all errors and warnings
        """
        logger.info("Starting compliance check")
        
        # Validate manifest
        result = self.manifest_validator.validate(manifest)
        
        # If manifest is invalid, return early
        if not result.is_valid:
            logger.error(
                "Compliance check failed - invalid manifest",
                errors=len(result.errors),
            )
            return result
        
        # Additional compliance checks
        if isinstance(manifest, dict):
            manifest = AgentManifest(**manifest)
        
        # Check authority
        authority_valid, authority_errors = self.authority_validator.validate(
            manifest.authority
        )
        for error in authority_errors:
            result.add_error(error)
        
        # Check framework adapter (if present)
        if manifest.framework_adapter:
            self._check_framework_adapter(manifest, result)
        
        # Check observability (recommended)
        if not manifest.observability:
            result.add_warning(
                "No observability configuration - consider adding logs/traces/incidents"
            )
        
        logger.info(
            "Compliance check complete",
            agent_id=manifest.agent_id,
            is_compliant=result.is_valid,
            errors=len(result.errors),
            warnings=len(result.warnings),
        )
        
        return result
    
    def _check_framework_adapter(
        self,
        manifest: AgentManifest,
        result: ValidationResult,
    ) -> None:
        """Check framework adapter configuration."""
        adapter = manifest.framework_adapter
        
        if not adapter:
            return
        
        # Check that adapter name is recognized
        known_adapters = ["langchain", "n8n", "make", "custom"]
        if adapter.name not in known_adapters:
            result.add_warning(
                f"Unknown framework adapter: {adapter.name} "
                f"(known: {', '.join(known_adapters)})"
            )
        
        # Check that entrypoint is defined
        if not adapter.entrypoint:
            result.add_error("Framework adapter must specify entrypoint")
    
    def is_compliant(self, manifest: AgentManifest | dict[str, Any]) -> bool:
        """Quick compliance check.
        
        Args:
            manifest: Agent manifest to check
        
        Returns:
            True if compliant, False otherwise
        """
        result = self.check_compliance(manifest)
        return result.is_valid

