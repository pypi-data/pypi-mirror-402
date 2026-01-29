# 🚀 Agent Standard v1 - Quick Start Guide

Get started with Agent Standard v1 in 5 minutes!

---

## 📦 Installation

The Agent Standard is already included in the CPA project. No additional installation needed!

```bash
# Verify installation
poetry run python -c "from core.agent_standard import Agent; print('✅ Agent Standard ready!')"
```

---

## 🎯 Create Your First Agent

### Step 1: Create Agent Manifest

Create a JSON file `my_agent.json`:

```json
{
  "agent_id": "agent.my-company.my-agent",
  "name": "My First Agent",
  "version": "1.0.0",
  "status": "active",
  
  "revisions": {
    "current_revision": "rev-001",
    "history": [
      {
        "revision_id": "rev-001",
        "timestamp": "2026-01-14T10:00:00Z",
        "author": {"type": "human", "id": "your.name"},
        "change_summary": "Initial version"
      }
    ]
  },
  
  "overview": {
    "description": "My first compliant agent",
    "tags": ["demo", "test"],
    "owner": {"type": "human", "id": "your.name"},
    "lifecycle": {"stage": "development", "sla": "none"}
  },
  
  "capabilities": [
    {"name": "example_task", "level": "medium"}
  ],
  
  "ethics": {
    "framework": "harm-minimization",
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
      {"id": "trust", "weight": 0.5},
      {"id": "helpfulness", "weight": 0.5}
    ],
    "health_signals": {
      "tension_thresholds": {"stressed": 0.6, "degraded": 0.8, "critical": 0.95},
      "reporting_interval_sec": 300,
      "escalation_threshold": "degraded"
    }
  },
  
  "authority": {
    "instruction": {"type": "human", "id": "your.name"},
    "oversight": {"type": "human", "id": "supervisor.name", "independent": true},
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
```

### Step 2: Validate Manifest

```python
from core.agent_standard import AgentManifest, ComplianceChecker

# Load manifest
manifest = AgentManifest.from_json_file("my_agent.json")

# Check compliance
checker = ComplianceChecker()
result = checker.check_compliance(manifest)

if result.is_valid:
    print("✅ Agent is compliant!")
else:
    print("❌ Errors:", result.errors)
```

### Step 3: Create and Run Agent

```python
import asyncio
from core.agent_standard import Agent

async def main():
    # Create agent
    agent = Agent.from_manifest_file("my_agent.json")
    
    # Start agent
    await agent.start()
    print("✅ Agent started!")
    
    # Execute task
    result = await agent.execute({
        "type": "example_task",
        "input": {"message": "Hello, Agent!"}
    })
    print(f"Result: {result}")
    
    # Check health
    health = agent.get_health()
    print(f"Health: {health.state}, Tension: {health.tension:.2f}")
    
    # Stop agent
    await agent.stop()

asyncio.run(main())
```

---

## 🔍 Key Concepts

### 1. **Ethics (Runtime-Active)**
Ethics are NOT documentation - they are evaluated on EVERY action!

```python
# Ethics violations BLOCK execution
try:
    await agent.execute({"type": "harmful_action"})
except EthicsViolation as e:
    print(f"Blocked: {e.violations}")
```

### 2. **Desires (Health Indicators)**
Desires track agent health. Low satisfaction = degraded health.

```python
# Check health
health = agent.get_health()
if health.state == "degraded":
    print("⚠️ Agent health degraded - oversight notified!")
```

### 3. **Four-Eyes Principle**
Instruction and Oversight MUST be different entities!

```json
{
  "authority": {
    "instruction": {"type": "human", "id": "boss"},
    "oversight": {"type": "human", "id": "auditor", "independent": true}
  }
}
```

### 4. **Non-Punitive Incident Reporting**
Agents can report issues without consequences!

```python
agent.report_incident(
    severity="warning",
    category="uncertainty",
    message="I'm not sure about this task",
    details={"task": task}
)
```

---

## 📚 Examples

See `core/agent_standard/examples/` for complete examples:

- **meeting_assistant.json** - Full-featured meeting assistant
- **test_agent_standard.py** - Complete test script

Run the example:

```bash
poetry run python core/agent_standard/examples/test_agent_standard.py
```

---

## 🌐 Universal Runtime

The same agent runs identically on:

- ☁️ **Cloud** (Railway, AWS, Azure)
- 🔌 **Edge** (IoT, local servers)
- 💻 **Desktop** (Windows, Mac, Linux)

Just deploy the manifest + runtime!

---

## 🔒 Compliance Checklist

✅ All required fields present  
✅ Ethics framework configured  
✅ Desires profile defined  
✅ Authority separation enforced  
✅ Oversight independent  
✅ Escalation channels configured  
✅ IO contracts defined  
✅ Revision history maintained  

---

## 📞 Next Steps

1. **Read the full spec**: See `README.md`
2. **Explore examples**: Check `examples/`
3. **Build your agent**: Start with the template above
4. **Test compliance**: Use `ComplianceChecker`
5. **Deploy**: Same manifest works everywhere!

---

**Happy Agent Building! 🤖**

