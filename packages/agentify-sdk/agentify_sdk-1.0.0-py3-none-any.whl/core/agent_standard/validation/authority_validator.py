"""Authority Validator - Validates Four-Eyes Principle.

Ensures that instruction and oversight authorities are properly separated.
"""

import structlog
from typing import Any

from core.agent_standard.models.authority import Authority

logger = structlog.get_logger()


class AuthorityValidator:
    """Validates authority configuration.
    
    Enforces the Four-Eyes Principle:
    - Instruction and Oversight must be different entities
    - Oversight must be marked as independent
    - Escalation channels must be configured
    """
    
    def validate(self, authority: Authority) -> tuple[bool, list[str]]:
        """Validate authority configuration.
        
        Args:
            authority: Authority configuration to validate
        
        Returns:
            (is_valid, errors)
        """
        errors = []
        
        # Check separation
        if authority.instruction.id == authority.oversight.id:
            errors.append(
                f"Four-Eyes Principle violation: instruction and oversight "
                f"are the same entity ({authority.instruction.id})"
            )
        
        # Check independence
        if not authority.oversight.independent:
            errors.append(
                "Oversight must be marked as independent (independent=True)"
            )
        
        # Check escalation channels
        if not authority.escalation.channels:
            errors.append("At least one escalation channel must be configured")
        
        # Check severity levels
        if not authority.escalation.severity_levels:
            errors.append("At least one severity level must be configured")
        
        is_valid = len(errors) == 0
        
        logger.info(
            "Authority validation complete",
            is_valid=is_valid,
            errors=len(errors),
            instruction=authority.instruction.id,
            oversight=authority.oversight.id,
        )
        
        return is_valid, errors
    
    def validate_separation(
        self,
        instruction_id: str,
        oversight_id: str,
    ) -> bool:
        """Validate that two authority IDs are different.
        
        Args:
            instruction_id: Instruction authority ID
            oversight_id: Oversight authority ID
        
        Returns:
            True if different, False if same
        """
        return instruction_id != oversight_id

