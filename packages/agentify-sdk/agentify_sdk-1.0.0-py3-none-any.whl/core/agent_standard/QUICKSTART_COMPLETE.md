# 🚀 Quick Start - Create Your First Agent

**Complete guide to creating an Agent Standard v1 compliant agent**

---

## 📋 **Overview**

Agents in the Agent Standard v1 are **JSON-first**. The agent manifest (JSON file) is the **single source of truth** that describes the agent completely, independent of implementation.

**Key Principle:**
> The JSON manifest describes WHAT the agent is and does.
> The code implements HOW it does it.

**🎯 Templates Available:**
- **[Minimal Template](templates/minimal_agent_template.json)** - Quick start with only required fields
- **[Complete Template](templates/agent_manifest_template.json)** - All 14 sections with examples
- **[Template Guide](templates/README.md)** - How to use templates

---

## 🎯 **Three Ways to Create an Agent**

### **1. Pure JSON (Recommended for Lovable, n8n, Make.com)**

Just create a JSON file with all 14 sections. No code needed!

**File:** `my_agent.json`

```json
{
  "agent_id": "agent.mycompany.myagent",
  "name": "My First Agent",
  "version": "1.0.0",
  "status": "active",
  
  "revisions": {
    "current_revision": "rev-001",
    "history": []
  },
  
  "overview": {
    "description": "My first agent",
    "tags": ["demo"],
    "owner": {"type": "human", "id": "me@example.com"}
  },
  
  "capabilities": [
    {"name": "greeting", "level": "high"}
  ],
  
  "ethics": {
    "framework": "harm-minimization",
    "principles": [
      {
        "id": "no-harm",
        "text": "Do not cause harm",
        "severity": "critical",
        "enforcement": "hard"
      }
    ],
    "hard_constraints": ["no_illegal_guidance"],
    "soft_constraints": []
  },
  
  "desires": {
    "profile": [
      {"id": "trust", "weight": 1.0}
    ],
    "health_signals": {
      "tension_thresholds": {"stressed": 0.6, "degraded": 0.8, "critical": 0.95}
    }
  },
  
  "pricing": {},
  "tools": [],
  "memory": {},
  "schedule": {},
  
  "activities": {
    "queue": [],
    "execution_state": {
      "current_activity": null,
      "queue_length": 0,
      "avg_execution_time_ms": 0.0
    }
  },
  
  "prompt": {
    "system": "You are a helpful assistant."
  },
  
  "guardrails": {
    "input_validation": {
      "max_length": 10000,
      "allowed_formats": ["text"],
      "content_filters": []
    },
    "output_validation": {
      "max_length": 5000,
      "content_filters": []
    }
  },
  
  "team": {},
  "customers": {},
  "knowledge": {},
  
  "io": {
    "input_formats": ["text"],
    "output_formats": ["text"]
  },
  
  "authority": {
    "instruction": {"type": "human", "id": "user@example.com"},
    "oversight": {"type": "human", "id": "supervisor@example.com", "independent": true}
  },
  
  "observability": {}
}
```

**That's it!** This JSON fully describes your agent.

---

### **2. Python Code (Programmatic Creation)**

**Install:**
```bash
pip install pydantic
```

**File:** `create_agent.py`

```python
from core.agent_standard.models.manifest import AgentManifest
from core.agent_standard.models.ethics import EthicsFramework, EthicsPrinciple
from core.agent_standard.models.desires import DesireProfile, Desire, HealthSignals
from core.agent_standard.models.authority import Authority, AuthorityEntity, Escalation

# Create agent manifest
manifest = AgentManifest(
    agent_id="agent.mycompany.myagent",
    name="My First Agent",
    version="1.0.0",
    status="active",
    
    # Required: Revisions
    revisions={
        "current_revision": "rev-001",
        "history": []
    },
    
    # Required: Overview
    overview={
        "description": "My first agent",
        "tags": ["demo"],
        "owner": {"type": "human", "id": "me@example.com"}
    },
    
    # Required: Capabilities
    capabilities=[
        {"name": "greeting", "level": "high"}
    ],
    
    # Required: Ethics
    ethics=EthicsFramework(
        framework="harm-minimization",
        principles=[
            EthicsPrinciple(
                id="no-harm",
                text="Do not cause harm",
                severity="critical",
                enforcement="hard"
            )
        ],
        hard_constraints=["no_illegal_guidance"],
        soft_constraints=[]
    ),

    # Required: Desires
    desires=DesireProfile(
        profile=[
            Desire(id="trust", weight=1.0)
        ],
        health_signals=HealthSignals(
            tension_thresholds={
                "stressed": 0.6,
                "degraded": 0.8,
                "critical": 0.95
            }
        )
    ),

    # Required: Authority (Four-Eyes Principle!)
    authority=Authority(
        instruction=AuthorityEntity(
            type="human",
            id="user@example.com"
        ),
        oversight=AuthorityEntity(
            type="human",
            id="supervisor@example.com",
            independent=True
        ),
        escalation=Escalation(
            default_channel="email",
            channels=["email"]
        )
    ),

    # Required: IO
    io={
        "input_formats": ["text"],
        "output_formats": ["text"]
    }
)

# Save to JSON file
manifest.to_json_file("my_agent.json")
print("✅ Agent manifest created: my_agent.json")
```

**Run:**
```bash
python create_agent.py
```

---

### **3. Using the CLI (Coming Soon)**

```bash
# Create new agent interactively
agent-standard create --interactive

# Validate existing manifest
agent-standard validate my_agent.json

# Deploy agent
agent-standard deploy my_agent.json
```

---

## 📚 **Complete Example**

See the complete example with ALL 14 sections:

👉 **[complete_agent_example.json](examples/complete_agent_example.json)** 👈

This example includes:
- ✅ All 14 core areas
- ✅ Detailed comments
- ✅ Real-world configurations
- ✅ Best practices

---

## 🔍 **The 14 Core Areas**

Every agent MUST have these sections in the JSON:

| # | Section | Required | Description |
|---|---------|----------|-------------|
| 1 | `overview` | ✅ Yes | Agent identity & summary |
| 2 | `ethics` | ✅ Yes | Ethics framework & principles |
| 2 | `desires` | ✅ Yes | Desire profile & health monitoring |
| 3 | `pricing` | ⚠️ Optional | Pricing model & revenue share |
| 4 | `tools` | ⚠️ Optional | Available tools & connections |
| 5 | `memory` | ⚠️ Optional | Memory configuration |
| 6 | `schedule` | ⚠️ Optional | Scheduled jobs |
| 7 | `activities` | ⚠️ Optional | Activity queue & execution state |
| 8 | `prompt` | ⚠️ Optional | System prompt configuration |
| 8 | `guardrails` | ⚠️ Optional | Input/output validation |
| 9 | `team` | ⚠️ Optional | Team relationships |
| 10 | `customers` | ⚠️ Optional | Customer assignments |
| 11 | `knowledge` | ⚠️ Optional | RAG & knowledge base |
| 12 | `io` | ✅ Yes | Input/output formats |
| 13 | `revisions` | ✅ Yes | Version history |
| 14 | `authority` | ✅ Yes | Four-Eyes Principle |

**See:** [AGENT_ANATOMY.md](AGENT_ANATOMY.md) for detailed reference

---

## 🎯 **Minimal Agent (Only Required Fields)**

```json
{
  "agent_id": "agent.company.name",
  "name": "Agent Name",
  "version": "1.0.0",
  "status": "active",

  "revisions": {
    "current_revision": "rev-001",
    "history": []
  },

  "overview": {
    "description": "What this agent does",
    "tags": [],
    "owner": {"type": "human", "id": "owner@example.com"}
  },

  "capabilities": [],

  "ethics": {
    "framework": "harm-minimization",
    "principles": [
      {"id": "no-harm", "text": "Do not cause harm", "severity": "critical", "enforcement": "hard"}
    ],
    "hard_constraints": ["no_illegal_guidance"],
    "soft_constraints": []
  },

  "desires": {
    "profile": [{"id": "trust", "weight": 1.0}],
    "health_signals": {
      "tension_thresholds": {"stressed": 0.6, "degraded": 0.8, "critical": 0.95}
    }
  },

  "authority": {
    "instruction": {"type": "human", "id": "user@example.com"},
    "oversight": {"type": "human", "id": "supervisor@example.com", "independent": true}
  },

  "io": {
    "input_formats": ["text"],
    "output_formats": ["text"]
  }
}
```

---

## 🔧 **Validation**

**Python:**
```python
from core.agent_standard.validation.manifest_validator import ManifestValidator

validator = ManifestValidator()
result = validator.validate_file("my_agent.json")

if result.is_valid:
    print("✅ Agent manifest is valid!")
else:
    print("❌ Validation errors:")
    for error in result.errors:
        print(f"  - {error}")
```

---

## 🚀 **Next Steps**

1. **Create your agent JSON** - Use the minimal example above
2. **Add your tools** - Define what your agent can do
3. **Configure ethics** - Set your ethical constraints
4. **Validate** - Make sure it's compliant
5. **Deploy** - Register in the marketplace

---

## 📖 **Resources**

- **[Complete Example](examples/complete_agent_example.json)** - All 14 sections
- **[Agent Anatomy](AGENT_ANATOMY.md)** - Quick reference guide
- **[Full Specification](README.md)** - Complete documentation
- **[Examples](examples/)** - More real-world examples

---

**Remember:** The JSON manifest is the source of truth. Your implementation (Python, JavaScript, n8n, Make.com, etc.) just executes what the manifest describes!

