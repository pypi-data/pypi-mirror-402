"""Agent Standard v1 - Agentic Economy.

This package implements the complete Agent Standard v1 specification
for the Agentic Economy, including:

- Ethics-first design with runtime-active constraints
- Desire profiles for health monitoring
- Four-Eyes Principle (Instruction/Oversight separation)
- Framework-agnostic implementation
- Universal runtime (Cloud/Edge/Desktop)

Version: 1.0.0
Status: Production
"""

from core.agent_standard.models.manifest import AgentManifest
from core.agent_standard.models.ethics import EthicsFramework, EthicsPrinciple
from core.agent_standard.models.desires import DesireProfile, DesireHealth
from core.agent_standard.models.authority import Authority, InstructionAuthority, OversightAuthority
from core.agent_standard.models.io_contracts import IOContract, InputSchema, OutputSchema

from core.agent_standard.core.agent import Agent
from core.agent_standard.core.ethics_engine import EthicsEngine
from core.agent_standard.core.desire_monitor import DesireMonitor
from core.agent_standard.core.oversight import OversightController
from core.agent_standard.core.runtime import AgentRuntime

from core.agent_standard.validation.manifest_validator import ManifestValidator
from core.agent_standard.validation.authority_validator import AuthorityValidator
from core.agent_standard.validation.compliance_checker import ComplianceChecker

__version__ = "1.0.0"
__status__ = "production"

__all__ = [
    # Models
    "AgentManifest",
    "EthicsFramework",
    "EthicsPrinciple",
    "DesireProfile",
    "DesireHealth",
    "Authority",
    "InstructionAuthority",
    "OversightAuthority",
    "IOContract",
    "InputSchema",
    "OutputSchema",
    
    # Core
    "Agent",
    "EthicsEngine",
    "DesireMonitor",
    "OversightController",
    "AgentRuntime",
    
    # Validation
    "ManifestValidator",
    "AuthorityValidator",
    "ComplianceChecker",
]

