"""Agent Standard CLI - Main entry point.

Usage:
    agent-std init <agent-name>     # Create new agent
    agent-std validate [manifest]   # Validate manifest
    agent-std run [manifest]        # Run agent
    agent-std check [manifest]      # Check compliance
"""

import sys
from pathlib import Path
from typing import Any

import structlog

logger = structlog.get_logger()


def cli() -> None:
    """Main CLI entry point."""
    if len(sys.argv) < 2:
        print_help()
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "init":
        cmd_init()
    elif command == "validate":
        cmd_validate()
    elif command == "run":
        cmd_run()
    elif command == "check":
        cmd_check()
    elif command == "help" or command == "--help" or command == "-h":
        print_help()
    else:
        print(f"❌ Unknown command: {command}")
        print_help()
        sys.exit(1)


def print_help() -> None:
    """Print CLI help."""
    print("""
🤖 Agent Standard CLI - v1.0.0

Usage:
    agent-std init <agent-name>     Create new agent with scaffolding
    agent-std validate [manifest]   Validate manifest file
    agent-std run [manifest]        Run agent
    agent-std check [manifest]      Check Agent Standard v1 compliance
    agent-std help                  Show this help

Examples:
    agent-std init my-agent
    agent-std validate manifest.json
    agent-std run manifest.json
    agent-std check manifest.json

Documentation:
    https://github.com/JonasDEMA/cpa_agent_platform
""")


def cmd_init() -> None:
    """Initialize a new agent."""
    if len(sys.argv) < 3:
        print("❌ Usage: agent-std init <agent-name>")
        sys.exit(1)
    
    agent_name = sys.argv[2]
    
    print(f"\n🤖 Creating new Agent Standard v1 agent: {agent_name}\n")
    
    # Interactive wizard
    print("📝 Agent Configuration:")
    agent_id = input(f"  Agent ID [agent.my-company.{agent_name}]: ").strip() or f"agent.my-company.{agent_name}"
    description = input(f"  Description: ").strip() or f"Agent: {agent_name}"
    ethics_framework = input(f"  Ethics Framework [harm-minimization]: ").strip() or "harm-minimization"
    instruction_authority = input(f"  Instruction Authority [human:user]: ").strip() or "human:user"
    oversight_authority = input(f"  Oversight Authority [human:supervisor]: ").strip() or "human:supervisor"
    
    # Validate authority separation
    if instruction_authority == oversight_authority:
        print("❌ Error: Instruction and Oversight must be different (Four-Eyes Principle)!")
        sys.exit(1)
    
    # Create directory
    agent_dir = Path(agent_name)
    agent_dir.mkdir(exist_ok=True)
    
    # Create manifest
    manifest_path = agent_dir / "manifest.json"
    _create_manifest(manifest_path, agent_id, agent_name, description, ethics_framework, instruction_authority, oversight_authority)
    
    # Create agent.py
    agent_py_path = agent_dir / "agent.py"
    _create_agent_py(agent_py_path, agent_name)
    
    # Create README
    readme_path = agent_dir / "README.md"
    _create_readme(readme_path, agent_name, agent_id)
    
    print(f"\n✅ Agent created successfully!")
    print(f"\n📁 Files created:")
    print(f"   - {manifest_path}")
    print(f"   - {agent_py_path}")
    print(f"   - {readme_path}")
    print(f"\n🚀 Next steps:")
    print(f"   1. cd {agent_name}")
    print(f"   2. Edit agent.py to implement your logic")
    print(f"   3. agent-std validate")
    print(f"   4. agent-std run")
    print()


def cmd_validate() -> None:
    """Validate a manifest."""
    manifest_path = sys.argv[2] if len(sys.argv) > 2 else "manifest.json"
    
    print(f"\n🔍 Validating manifest: {manifest_path}\n")
    
    from core.agent_standard.validation.compliance_checker import ComplianceChecker
    from core.agent_standard.models.manifest import AgentManifest
    
    try:
        manifest = AgentManifest.from_json_file(manifest_path)
        checker = ComplianceChecker()
        result = checker.check_compliance(manifest)
        
        if result.is_valid:
            print("✅ Manifest is valid and compliant with Agent Standard v1!")
        else:
            print(f"❌ Validation failed with {len(result.errors)} errors:")
            for error in result.errors:
                print(f"   - {error}")
        
        if result.warnings:
            print(f"\n⚠️  {len(result.warnings)} warnings:")
            for warning in result.warnings:
                print(f"   - {warning}")
        
        print()
        
        sys.exit(0 if result.is_valid else 1)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


def cmd_run() -> None:
    """Run an agent."""
    manifest_path = sys.argv[2] if len(sys.argv) > 2 else "manifest.json"
    
    print(f"\n🚀 Starting agent: {manifest_path}\n")
    
    from core.agent_standard.core.agent import Agent
    
    try:
        agent = Agent.from_manifest_file(manifest_path)
        print(f"✅ Agent loaded: {agent.manifest.name}")
        print(f"   Agent ID: {agent.manifest.agent_id}")
        print(f"   Version: {agent.manifest.version}")
        print(f"\n⏳ Agent is running... (Press Ctrl+C to stop)\n")
        
        # TODO: Implement agent runtime loop
        import asyncio
        asyncio.run(agent.start())
        
    except KeyboardInterrupt:
        print("\n\n⏹️  Agent stopped by user")
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


def cmd_check() -> None:
    """Check compliance."""
    cmd_validate()  # Same as validate for now


def _create_manifest(path: Path, agent_id: str, name: str, description: str, ethics: str, instruction: str, oversight: str) -> None:
    """Create manifest file."""
    import json

    manifest = {
        "agent_id": agent_id,
        "name": name,
        "version": "1.0.0",
        "status": "active",
        "revisions": {
            "current_revision": "rev-001",
            "history": [
                {
                    "revision_id": "rev-001",
                    "timestamp": "2026-01-14T00:00:00Z",
                    "author": {"type": "human", "id": "developer"},
                    "change_summary": "Initial version"
                }
            ]
        },
        "overview": {
            "description": description,
            "tags": ["new"],
            "owner": {"type": "human", "id": "developer"},
            "lifecycle": {"stage": "development", "sla": "none"}
        },
        "capabilities": [
            {"name": "example", "level": "medium"}
        ],
        "ethics": {
            "framework": ethics,
            "principles": [
                {
                    "id": "no-harm",
                    "text": "Do not cause harm to users",
                    "severity": "critical",
                    "enforcement": "hard"
                }
            ],
            "hard_constraints": ["no_illegal_guidance"],
            "soft_constraints": [],
            "evaluation_mode": "pre_action"
        },
        "desires": {
            "profile": [
                {"id": "trust", "weight": 0.4},
                {"id": "helpfulness", "weight": 0.3},
                {"id": "coherence", "weight": 0.3}
            ],
            "health_signals": {
                "tension_thresholds": {"stressed": 0.6, "degraded": 0.8, "critical": 0.95},
                "reporting_interval_sec": 300,
                "escalation_threshold": "degraded"
            }
        },
        "authority": {
            "instruction": {"type": instruction.split(":")[0], "id": instruction.split(":")[1]},
            "oversight": {"type": oversight.split(":")[0], "id": oversight.split(":")[1], "independent": True},
            "escalation": {
                "channels": ["human"],
                "severity_levels": ["warning", "incident", "critical"],
                "default_channel": "human"
            }
        },
        "io": {
            "input_formats": ["text", "json"],
            "output_formats": ["text", "json"]
        }
    }

    with path.open("w") as f:
        json.dump(manifest, f, indent=2)


def _create_agent_py(path: Path, name: str) -> None:
    """Create agent.py file."""
    content = f'''"""Agent: {name}

This is your agent implementation.
"""

from core.agent_standard.decorators import agent_tool


@agent_tool(
    name="example_task",
    description="Example task - replace with your logic",
    ethics=["no_harm"],
    desires=["trust", "helpfulness"]
)
async def example_task(input_data: str) -> str:
    """Example task implementation.

    Args:
        input_data: Input data

    Returns:
        Processed result
    """
    # TODO: Implement your logic here
    return f"Processed: {{input_data}}"


# Add more tools here using @agent_tool decorator
'''

    path.write_text(content)


def _create_readme(path: Path, name: str, agent_id: str) -> None:
    """Create README file."""
    content = f'''# {name}

Agent ID: `{agent_id}`

## Description

TODO: Add description

## Usage

```bash
# Validate
agent-std validate

# Run
agent-std run
```

## Development

1. Edit `agent.py` to implement your logic
2. Use `@agent_tool` decorator for each function
3. Validate with `agent-std validate`
4. Run with `agent-std run`

## Agent Standard v1 Compliance

✅ Ethics-First Design
✅ Desire-Based Health Monitoring
✅ Four-Eyes Principle (Instruction + Oversight)
✅ Manifest-Driven Configuration
'''

    path.write_text(content)

