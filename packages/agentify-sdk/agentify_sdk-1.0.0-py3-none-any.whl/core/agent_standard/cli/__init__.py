"""Agent Standard CLI - Command-line interface for agent development.

This module provides CLI commands for:
- Scaffolding new agents (agent-std init)
- Validating manifests (agent-std validate)
- Running agents (agent-std run)
- Checking compliance (agent-std check)
"""

from core.agent_standard.cli.main import cli

__all__ = ["cli"]

