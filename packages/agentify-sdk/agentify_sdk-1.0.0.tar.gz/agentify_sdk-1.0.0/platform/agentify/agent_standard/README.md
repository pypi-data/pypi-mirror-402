# 🤖 Agent Standard v1

**Universal Agent Wrapper for the Agentic Economy**

> 🚀 **Quick Start:** [core/agent_standard/QUICKSTART_COMPLETE.md](../../../core/agent_standard/QUICKSTART_COMPLETE.md) - Create your first agent in 5 minutes!
>
> 📝 **Complete Example:** [core/agent_standard/examples/complete_agent_example.json](../../../core/agent_standard/examples/complete_agent_example.json) - All 14 sections
>
> 📚 **Complete Implementation:** See [core/agent_standard/](../../../core/agent_standard/) for full source code, models, and runtime.
>
> 📖 **Agent Anatomy:** See [AGENT_ANATOMY.md](./AGENT_ANATOMY.md) for complete manifest structure reference.
>
> 📊 **Implementation Status:** See [IMPLEMENTATION_STATUS.md](./IMPLEMENTATION_STATUS.md) for current progress.
>
> 🔐 **Authentication:** See [AUTHENTICATION.md](./AUTHENTICATION.md) for authentication and IAM requirements.
>
> 🏪 **Default Marketplace:** marketplace.meet-harmony.ai

---

## 📋 **Overview**

The **Agent Standard v1** is a universal wrapper that makes any AI agent compliant, safe, and ready for the Agentic Economy. It provides:

- ✅ **Ethics-First Design** - Runtime-active ethical constraints
- ✅ **Desire Profiles** - Health monitoring and alignment indicators
- ✅ **Four-Eyes Principle** - Mandatory separation of Instruction & Oversight
- ✅ **Framework Agnostic** - Works with LangChain, n8n, Make.com, custom runtimes
- ✅ **Universal Runtime** - Same agent definition works on Cloud, Edge, Desktop
- ✅ **Incident Reporting** - Non-punitive reporting without consequences
- ✅ **Recursive Oversight** - Oversight agents are themselves overseen
- ✅ **Authentication & IAM** - Secure access via CoreSense IAM
- ✅ **Marketplace Integration** - Discoverable via marketplace.meet-harmony.ai

---

## 🏗️ **Architecture**

```
┌─────────────────────────────────────────────────────────┐
│                    Agent Manifest                        │
│              (manifest.json - Source of Truth)           │
└────────────────────────┬────────────────────────────────┘
                         │
        ┌────────────────┼────────────────┐
        │                │                │
   ┌────▼────┐      ┌────▼────┐     ┌────▼────┐
   │ Ethics  │      │ Desires │     │Authority│
   │ Engine  │      │ Monitor │     │Oversight│
   └────┬────┘      └────┬────┘     └────┬────┘
        │                │                │
        └────────────────┼────────────────┘
                         │
                    ┌────▼────┐
                    │  Agent  │
                    │ Runtime │
                    └────┬────┘
                         │
        ┌────────────────┼────────────────┐
        │                │                │
   ┌────▼────┐      ┌────▼────┐     ┌────▼────┐
   │  Tools  │      │ Memory  │     │   I/O   │
   └─────────┘      └─────────┘     └─────────┘
```

---

## 🎯 **Core Principles**

### **1. Ethics Override All**
Ethics are **not documentation**. They are **runtime-active constraints** evaluated on every decision.

- **Hard Constraints:** BLOCK execution if violated
- **Soft Constraints:** Generate warnings but allow execution
- **Evaluation Mode:** Pre-action, post-action, or continuous

### **2. Desires as Health Indicators**
Desires serve as diagnostic signals. Persistent suppression triggers oversight review.

- **Desire Profile:** Weighted list of agent desires (e.g., trust, helpfulness)
- **Health Monitoring:** Continuous tracking of desire satisfaction
- **Tension Detection:** Automatic escalation when health degrades

### **3. Four-Eyes Principle (Mandatory)**
Every agent MUST have:
- **Instruction Authority** (assigns tasks)
- **Oversight Authority** (monitors, audits, escalates)

These MUST be different entities.

### **4. Framework Agnostic**
Agents can use LangChain, n8n, Make.com, or custom runtimes - but the **manifest is the source of truth**.

---

## 📄 **Agent Manifest**

Every agent has a `manifest.json` that defines its complete specification:

```json
{
  "agent_id": "agent.company.name",
  "name": "Agent Name",
  "version": "1.0.0",
  "status": "active",
  
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
    "soft_constraints": ["inform_before_action"]
  },
  
  "desires": {
    "profile": [
      {"id": "trust", "weight": 0.5},
      {"id": "helpfulness", "weight": 0.5}
    ],
    "health_signals": {
      "tension_thresholds": {
        "stressed": 0.6,
        "degraded": 0.8,
        "critical": 0.95
      },
      "reporting_interval_sec": 300,
      "escalation_threshold": "degraded"
    }
  },
  
  "authority": {
    "instruction": {
      "type": "human",
      "id": "user@company.com"
    },
    "oversight": {
      "type": "human",
      "id": "supervisor@company.com",
      "independent": true
    },
    "escalation": {
      "default_channel": "email",
      "channels": ["email", "slack", "pagerduty"]
    }
  },

  "authentication": {
    "required": true,
    "provider": "coresense",
    "provider_url": "https://iam.meet-harmony.ai",
    "token_validation": "jwt",
    "roles_required": ["user"],
    "scopes_required": ["agent:execute"]
  },

  "marketplace": {
    "default_url": "https://marketplace.meet-harmony.ai",
    "discoverable": true,
    "registration": {
      "auto_register": true,
      "visibility": "public"
    }
  },

  "repository": {
    "url": "https://github.com/company/agent-name",
    "branch": "main",
    "path": "/"
  },

  "build_config": {
    "type": "docker",
    "build_command": "docker build -t agent-name .",
    "start_command": "docker run -p 8000:8000 agent-name",
    "env_vars": {
      "PORT": "8000",
      "LOG_LEVEL": "info"
    }
  },

  "host_requirements": {
    "min_memory_mb": 512,
    "min_cpu_cores": 0.5,
    "gpu_required": false,
    "preferred_region": "eu-central-1",
    "co_location_required": false,
    "co_location_with": []
  },

  "preferred_host": "agent.agentify.hosting-orchestrator",

  "tools": [
    {
      "name": "send_email",
      "description": "Send an email",
      "category": "communication",
      "executor": "agents.tools.EmailTool"
    }
  ],
  
  "io": {
    "input_formats": ["text", "json"],
    "output_formats": ["text", "json"]
  }
}
```

---

## 📋 **Complete Manifest Structure**

The Agent Manifest has **14 major sections** that define every aspect of an agent:

| # | Section | Description | UI Tab |
|---|---------|-------------|--------|
| **1** | [Overview](#1-overview) | Identity, status, capabilities, AI model | Overview |
| **2** | [Ethics & Desires](#2-ethics--desires) | Runtime-active ethics and health monitoring | Ethics & Desires |
| **3** | [Pricing](#3-pricing) | Pricing model and revenue sharing | Pricing |
| **4** | [Tools](#4-tools) | Available tools and connections | Tools |
| **5** | [Memory](#5-memory) | Memory slots and implementation | Memory |
| **6** | [Schedule](#6-schedule) | Scheduled jobs and cron tasks | Schedule |
| **7** | [Activities](#7-activities) | Activity queue and execution state | Activities |
| **8** | [Prompt & Guardrails](#8-prompt--guardrails) | System prompt and guardrails | Prompt |
| **9** | [Team](#9-team) | Team relationships and graph | Team |
| **10** | [Customers](#10-customers) | Customer assignments and load | Customers |
| **11** | [Knowledge](#11-knowledge) | RAG datasets and retrieval policies | Knowledge |
| **12** | [I/O](#12-io) | Input/output formats and contracts | I/O |
| **13** | [Revisions](#13-revisions) | Revision history and changelog | Revisions |
| **14** | [Authority & Oversight](#14-authority--oversight) | Four-Eyes Principle and incidents | Authority |

---

### **1. Overview**

**Fields:** `overview`, `status`, `capabilities`, `ai_model`, `ethics` (summary), `desires` (summary), `health` (summary)

**Purpose:** High-level agent identity and current state.

```json
{
  "agent_id": "agent.company.name",
  "name": "Agent Name",
  "version": "1.0.0",
  "status": "active",

  "overview": {
    "description": "What this agent does",
    "tags": ["tag1", "tag2"],
    "owner": {
      "type": "organization",
      "id": "company-id",
      "name": "Company Name"
    },
    "lifecycle": {
      "stage": "production",
      "sla": "99.9%"
    }
  },

  "capabilities": [
    {
      "name": "email_management",
      "level": "expert",
      "description": "Manage emails and calendar"
    }
  ],

  "ai_model": {
    "provider": "openai",
    "model": "gpt-4",
    "temperature": 0.7,
    "max_tokens": 4000
  }
}
```

---

### **2. Ethics & Desires**

**Fields:** `ethics` (framework, principles, constraints), `desires` (profile, health_signals), `health` state

**Purpose:** Runtime-active ethics enforcement and continuous health monitoring.

```json
{
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
    "hard_constraints": ["no_illegal_guidance", "no_unauthorized_access"],
    "soft_constraints": ["inform_before_action", "prefer_transparency"],
    "evaluation_mode": "pre_action"
  },

  "desires": {
    "profile": [
      {"id": "trust", "weight": 0.4, "satisfaction": 0.85},
      {"id": "helpfulness", "weight": 0.3, "satisfaction": 0.90},
      {"id": "efficiency", "weight": 0.3, "satisfaction": 0.75}
    ],
    "health_signals": {
      "tension_thresholds": {
        "stressed": 0.6,
        "degraded": 0.8,
        "critical": 0.95
      },
      "reporting_interval_sec": 300,
      "escalation_threshold": "degraded"
    }
  },

  "health": {
    "state": "healthy",
    "tension": 0.42,
    "last_check": "2024-01-15T10:30:00Z"
  }
}
```

---

### **3. Pricing**

**Fields:** `pricing`, `customers.assignments` (commercial terms / revenue share)

**Purpose:** Define pricing model and revenue sharing for marketplace agents.

```json
{
  "pricing": {
    "model": "usage_based",
    "base_price": 0.0,
    "per_request": 0.01,
    "per_minute": 0.0,
    "currency": "USD",
    "billing_cycle": "monthly",
    "free_tier": {
      "requests_per_month": 1000
    }
  },

  "customers": {
    "assignments": [
      {
        "customer_id": "customer-123",
        "app_id": "app.company.crm",
        "revenue_share": 0.90,
        "platform_fee": 0.10,
        "load": {
          "requests_per_day": 150,
          "avg_response_time_ms": 450
        }
      }
    ]
  }
}
```

---

### **4. Tools**

**Fields:** `tools` + `connection.status` + tool policies

**Purpose:** Define available tools, their schemas, and connection status.

```json
{
  "tools": [
    {
      "name": "send_email",
      "description": "Send an email via SMTP",
      "category": "communication",
      "executor": "agents.tools.EmailTool",
      "input_schema": {
        "type": "object",
        "properties": {
          "to": {"type": "string"},
          "subject": {"type": "string"},
          "body": {"type": "string"}
        },
        "required": ["to", "subject", "body"]
      },
      "output_schema": {
        "type": "object",
        "properties": {
          "success": {"type": "boolean"},
          "message_id": {"type": "string"}
        }
      },
      "connection": {
        "status": "connected",
        "last_check": "2024-01-15T10:00:00Z",
        "credentials_ref": "secret://smtp-credentials"
      },
      "policies": {
        "rate_limit": "100/hour",
        "requires_approval": false,
        "ethics_constraints": ["no_spam", "privacy_first"]
      }
    }
  ]
}
```

---

### **5. Memory**

**Fields:** `memory.slots` + `memory.implementation`

**Purpose:** Define memory configuration for agent state persistence.

```json
{
  "memory": {
    "implementation": "redis",
    "slots": [
      {
        "name": "conversation_history",
        "type": "short_term",
        "max_size": 10000,
        "ttl_seconds": 3600,
        "persistence": "redis://localhost:6379/0"
      },
      {
        "name": "user_preferences",
        "type": "long_term",
        "max_size": 100000,
        "ttl_seconds": null,
        "persistence": "postgres://db/agent_memory"
      }
    ],
    "retrieval_policy": {
      "strategy": "recency_weighted",
      "max_results": 10
    }
  }
}
```

---

### **6. Schedule**

**Fields:** `schedule.jobs`

**Purpose:** Define scheduled tasks and cron jobs.

```json
{
  "schedule": {
    "jobs": [
      {
        "id": "daily_report",
        "name": "Generate Daily Report",
        "cron": "0 9 * * *",
        "timezone": "UTC",
        "action": {
          "type": "tool_call",
          "tool": "generate_report",
          "params": {"type": "daily"}
        },
        "enabled": true,
        "last_run": "2024-01-15T09:00:00Z",
        "next_run": "2024-01-16T09:00:00Z"
      }
    ]
  }
}
```

---

### **7. Activities**

**Fields:** `activities.queue` + execution state

**Purpose:** Track current and queued activities.

```json
{
  "activities": {
    "queue": [
      {
        "id": "activity-123",
        "type": "tool_call",
        "tool": "send_email",
        "params": {"to": "user@example.com"},
        "status": "running",
        "started_at": "2024-01-15T10:30:00Z",
        "progress": 0.5
      },
      {
        "id": "activity-124",
        "type": "scheduled_job",
        "job_id": "daily_report",
        "status": "queued",
        "scheduled_for": "2024-01-16T09:00:00Z"
      }
    ],
    "execution_state": {
      "current_activity": "activity-123",
      "queue_length": 2,
      "avg_execution_time_ms": 450
    }
  }
}
```

---

### **8. Prompt & Guardrails**

**Fields:** `prompt` (system), `guardrails`, `ethics.hard_constraints`, tool-usage policies

**Purpose:** Define system prompt and runtime guardrails.

```json
{
  "prompt": {
    "system": "You are a helpful email assistant. Always be polite and professional.",
    "user_template": "User request: {user_input}",
    "assistant_template": "Response: {response}"
  },

  "guardrails": {
    "input_validation": {
      "max_length": 10000,
      "allowed_formats": ["text", "json"],
      "content_filters": ["profanity", "pii"]
    },
    "output_validation": {
      "max_length": 5000,
      "required_format": "text",
      "content_filters": ["pii", "sensitive_data"]
    },
    "tool_usage_policies": {
      "send_email": {
        "max_calls_per_hour": 100,
        "requires_confirmation": false,
        "blocked_domains": ["spam.com"]
      }
    }
  }
}
```

---

### **9. Team**

**Fields:** `team.agent_team_graph_ref` + `team.relationships`

**Purpose:** Define team relationships and collaboration graph.

```json
{
  "team": {
    "agent_team_graph_ref": "graph://team-123",
    "relationships": [
      {
        "agent_id": "agent.company.calendar",
        "relationship": "collaborator",
        "trust_level": 0.9,
        "shared_context": ["user_preferences", "schedule"]
      },
      {
        "agent_id": "agent.company.data-analyst",
        "relationship": "data_provider",
        "trust_level": 0.95,
        "shared_context": ["analytics_data"]
      }
    ],
    "team_policies": {
      "max_team_size": 5,
      "requires_approval": true,
      "trust_threshold": 0.8
    }
  }
}
```

---

### **10. Customers**

**Fields:** `customers.assignments` (load, revenue share)

**Purpose:** Track customer assignments and workload distribution.

```json
{
  "customers": {
    "assignments": [
      {
        "customer_id": "customer-123",
        "app_id": "app.company.crm",
        "assigned_at": "2024-01-01T00:00:00Z",
        "status": "active",
        "load": {
          "requests_per_day": 150,
          "avg_response_time_ms": 450,
          "peak_hours": ["09:00-11:00", "14:00-16:00"]
        },
        "revenue_share": 0.90,
        "platform_fee": 0.10,
        "total_revenue_usd": 1250.00
      }
    ],
    "total_customers": 1,
    "total_load": {
      "requests_per_day": 150,
      "capacity_utilization": 0.15
    }
  }
}
```

---

### **11. Knowledge**

**Fields:** `knowledge.rag.datasets` + `retrieval_policies` + data permissions

**Purpose:** Define knowledge base and RAG configuration.

```json
{
  "knowledge": {
    "rag": {
      "enabled": true,
      "datasets": [
        {
          "id": "company_docs",
          "name": "Company Documentation",
          "type": "vector_db",
          "source": "pinecone://index-123",
          "embedding_model": "text-embedding-ada-002",
          "chunk_size": 512,
          "chunk_overlap": 50
        }
      ],
      "retrieval_policies": {
        "max_results": 5,
        "similarity_threshold": 0.7,
        "reranking": true
      }
    },
    "data_permissions": {
      "allowed_datasets": ["company_docs", "public_kb"],
      "forbidden_datasets": ["confidential"],
      "requires_approval": ["financial_data"]
    }
  }
}
```

---

### **12. I/O**

**Fields:** `io.input_formats`, `io.output_formats`, `io.contracts`

**Purpose:** Define input/output formats and contracts.

```json
{
  "io": {
    "input_formats": ["text", "json", "markdown"],
    "output_formats": ["text", "json", "html"],
    "contracts": [
      {
        "name": "email_request",
        "input_schema": {
          "type": "object",
          "properties": {
            "action": {"type": "string", "enum": ["send", "read", "delete"]},
            "email_id": {"type": "string"}
          }
        },
        "output_schema": {
          "type": "object",
          "properties": {
            "success": {"type": "boolean"},
            "message": {"type": "string"}
          }
        }
      }
    ],
    "streaming": {
      "enabled": true,
      "chunk_size": 1024
    }
  }
}
```

---

### **13. Revisions**

**Fields:** `revisions.current_revision` + `revisions.history`

**Purpose:** Track all changes to the agent manifest.

```json
{
  "revisions": {
    "current_revision": "rev-005",
    "history": [
      {
        "revision_id": "rev-005",
        "timestamp": "2024-01-15T10:00:00Z",
        "author": {
          "type": "human",
          "id": "developer@company.com",
          "name": "John Doe"
        },
        "change_summary": "Added new tool: send_email",
        "changes": [
          {
            "field": "tools",
            "operation": "add",
            "value": {"name": "send_email"}
          }
        ]
      },
      {
        "revision_id": "rev-004",
        "timestamp": "2024-01-10T15:00:00Z",
        "author": {
          "type": "human",
          "id": "developer@company.com",
          "name": "John Doe"
        },
        "change_summary": "Updated ethics constraints"
      }
    ]
  }
}
```

---

### **14. Authority & Oversight**

**Fields:** `authority` + `escalation` + `observability.incidents_ref` + audit signals

**Purpose:** Enforce Four-Eyes Principle and track incidents.

```json
{
  "authority": {
    "instruction": {
      "type": "human",
      "id": "user@company.com",
      "name": "User Name"
    },
    "oversight": {
      "type": "human",
      "id": "supervisor@company.com",
      "name": "Supervisor Name",
      "independent": true
    },
    "escalation": {
      "default_channel": "email",
      "channels": ["email", "slack", "pagerduty"],
      "escalation_matrix": {
        "warning": ["email"],
        "incident": ["email", "slack"],
        "critical": ["email", "slack", "pagerduty"]
      }
    }
  },

  "observability": {
    "incidents_ref": "incidents://agent-123",
    "incidents": [
      {
        "id": "incident-001",
        "timestamp": "2024-01-15T10:30:00Z",
        "severity": "warning",
        "category": "ethics_violation",
        "message": "Soft constraint violated: inform_before_action",
        "context": {"action": "send_email"},
        "escalated": false
      }
    ],
    "audit_signals": {
      "log_level": "info",
      "log_destination": "logs://agent-123",
      "trace_enabled": true,
      "metrics_enabled": true
    }
  }
}
```

---

## 🧭 **Ethics Engine**

The **Ethics Engine** evaluates EVERY action against the agent's ethical framework BEFORE execution.

### **How it works:**

1. **Action Proposed:** Agent wants to execute an action
2. **Ethics Evaluation:** Engine checks against hard & soft constraints
3. **Decision:**
   - ✅ **Compliant:** Action proceeds
   - ⚠️ **Soft Violation:** Warning logged, action proceeds
   - ❌ **Hard Violation:** Action BLOCKED, incident reported

### **Example:**

```python
from core.agent_standard.core.ethics_engine import EthicsEngine

# Initialize engine with agent's ethics framework
engine = EthicsEngine(agent.ethics)

# Evaluate action
try:
    engine.evaluate_action({
        "type": "send_email",
        "to": "user@example.com",
        "subject": "Hello"
    })
    # Action is compliant, proceed
except EthicsViolation as e:
    # Action violates ethics, blocked
    print(f"Ethics violation: {e.violations}")
```

---

## 💚 **Desire Monitor**

The **Desire Monitor** continuously tracks desire satisfaction and calculates agent health.

### **Health States:**

- 🟢 **Healthy:** Tension < 0.6 (all desires satisfied)
- 🟡 **Stressed:** Tension 0.6-0.8 (some desires suppressed)
- 🟠 **Degraded:** Tension 0.8-0.95 (many desires suppressed)
- 🔴 **Critical:** Tension > 0.95 (severe misalignment)

### **Example:**

```python
from core.agent_standard.core.desire_monitor import DesireMonitor

# Initialize monitor
monitor = DesireMonitor(agent.desires)

# Start monitoring
await monitor.start_monitoring()

# Update desire satisfaction
monitor.update_desire_satisfaction("trust", 0.8)
monitor.update_desire_satisfaction("helpfulness", 0.6)

# Get current health
health = monitor.get_current_health()
print(f"Health: {health.state}, Tension: {health.tension}")
```

---

## 👁️ **Oversight Controller**

The **Oversight Controller** enforces the Four-Eyes Principle and handles escalations.

### **Responsibilities:**

- Monitor agent behavior
- Audit decisions and actions
- Escalate issues to oversight authority
- Track incidents and violations
- Enforce separation of Instruction & Oversight

### **Example:**

```python
from core.agent_standard.core.oversight import OversightController

# Initialize controller
controller = OversightController(agent.authority)

# Report incident
controller.report_incident(
    category="ethics_violation",
    severity="critical",
    message="Agent attempted unauthorized action",
    context={"action": "delete_database"}
)

# Escalate to oversight
controller.escalate_incident(incident, channel="email")
```

---

---

## 🔧 **Full Implementation & Documentation**

### **📂 Core Implementation**

All source code, models, and runtime components are in:

👉 **[core/agent_standard/](../../../core/agent_standard/)** 👈

### **📖 Essential Documentation**

| Document | Description | Link |
|----------|-------------|------|
| 📘 **Complete Specification** | Full Agent Standard v1 spec | [README.md](../../../core/agent_standard/README.md) |
| 🚀 **Quick Start Guide** | Build your first agent in 10 minutes | [QUICKSTART.md](../../../core/agent_standard/QUICKSTART.md) |
| 🔬 **Agent Anatomy** | **Complete manifest structure (all 14 sections)** | [AGENT_ANATOMY.md](../../../core/agent_standard/AGENT_ANATOMY.md) |
| 🧭 **Ethics Framework** | Deep dive into ethics engine | [docs/ethics_guide.md](../../../core/agent_standard/docs/ethics_guide.md) |
| 💚 **Desire Profiles** | Health monitoring & alignment | [docs/desires_guide.md](../../../core/agent_standard/docs/desires_guide.md) |
| 👁️ **Authority & Oversight** | Four-Eyes Principle implementation | [docs/oversight_guide.md](../../../core/agent_standard/docs/oversight_guide.md) |
| 🔌 **Framework Adapters** | LangChain, n8n, Make.com integration | [docs/adapters_guide.md](../../../core/agent_standard/docs/adapters_guide.md) |
| ☁️ **Runtime Deployment** | Cloud, Edge, Desktop deployment | [docs/runtime_guide.md](../../../core/agent_standard/docs/runtime_guide.md) |

### **💻 Source Code**

| Component | Description | Link |
|-----------|-------------|------|
| 📄 **Manifest Model** | Pydantic models for manifest | [models/manifest.py](../../../core/agent_standard/models/manifest.py) |
| 🧭 **Ethics Engine** | Runtime ethics evaluation | [core/ethics_engine.py](../../../core/agent_standard/core/ethics_engine.py) |
| 💚 **Desire Monitor** | Health monitoring & tracking | [core/desire_monitor.py](../../../core/agent_standard/core/desire_monitor.py) |
| 👁️ **Oversight Controller** | Four-Eyes Principle enforcement | [core/oversight.py](../../../core/agent_standard/core/oversight.py) |
| ⚙️ **Agent Runtime** | Universal agent runtime | [core/runtime.py](../../../core/agent_standard/core/runtime.py) |
| 🤖 **Agent Class** | Main agent implementation | [core/agent.py](../../../core/agent_standard/core/agent.py) |

### **🎓 Tutorials & Prompts**

| Resource | Description | Link |
|----------|-------------|------|
| 🎯 **Create Agent Prompt** | AI prompt to create new agents | [prompts/create_agent.md](../../../core/agent_standard/prompts/create_agent.md) |
| 📝 **Examples** | Example agent manifests | [examples/](../../../core/agent_standard/examples/) |

---

## 🌐 **Use in Agentify Platform**

In the Agentify Platform, all agents (including orchestrators) MUST comply with Agent Standard v1:

- **Apps** have built-in orchestrators (Agent Standard compliant)
- **Marketplace Agents** are registered with their manifests
- **Teams** are built from compliant agents
- **Oversight** is enforced at platform level

See [App Standard](../app_standard/README.md) for how apps use Agent Standard v1.

---

**"Ethics-first, health-monitored, oversight-enforced agents for the Agentic Economy"** 🤖✨

