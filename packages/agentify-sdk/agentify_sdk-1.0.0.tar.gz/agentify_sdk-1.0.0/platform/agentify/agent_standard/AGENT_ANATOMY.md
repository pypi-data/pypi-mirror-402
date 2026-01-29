# 🧬 Agent Anatomy - The 14 Core Areas

**Quick Reference Guide for Agent Standard v1 Manifest Structure**

Every Agent Standard v1 agent consists of **14 core areas** defined in the manifest. This document provides a quick reference for each area.

---

## 📊 **Overview Table**

| # | Area | Purpose | Required |
|---|------|---------|----------|
| 1 | **Overview** | Agent identity & summary | ✅ Yes |
| 2 | **Ethics & Desires** | Compliance & health monitoring | ✅ Yes |
| 3 | **Pricing** | Commercial terms & revenue share | ⚠️ Optional |
| 4 | **Tools** | Agent capabilities & connections | ✅ Yes |
| 5 | **Memory** | State persistence | ⚠️ Optional |
| 6 | **Schedule** | Automated execution | ⚠️ Optional |
| 7 | **Activities** | Execution queue & state | ⚠️ Optional |
| 8 | **Prompt / Guardrails** | LLM configuration & safety | ⚠️ Optional |
| 9 | **Team** | Multi-agent collaboration | ⚠️ Optional |
| 10 | **Customers** | Customer assignments | ⚠️ Optional |
| 11 | **Knowledge** | RAG & data access | ⚠️ Optional |
| 12 | **IO** | Input/output contracts | ✅ Yes |
| 13 | **Revisions** | Version control | ✅ Yes |
| 14 | **Authority & Oversight** | Governance & escalation | ✅ Yes |

---

## 🔍 **Detailed Reference**

### **1. Overview** - Agent Identity & Summary

**Purpose:** Quick identification and high-level understanding

**Required Fields:**
- `agent_id` - Unique identifier (format: `agent.company.name`)
- `name` - Human-readable name
- `version` - Semantic version (e.g., `1.0.0`)
- `status` - Current status (`active`, `inactive`, `deprecated`)

**Optional Fields:**
- `overview.description` - What the agent does
- `overview.tags` - Categorization tags
- `overview.owner` - Who owns the agent
- `overview.lifecycle` - Lifecycle stage and SLA
- `capabilities` - List of capabilities with levels

**Example:**
```json
{
  "agent_id": "agent.company.email-sender",
  "name": "Email Sender",
  "version": "1.0.0",
  "status": "active",
  "overview": {
    "description": "Send emails via SMTP",
    "tags": ["email", "communication"],
    "owner": {"type": "human", "id": "developer"}
  },
  "capabilities": [
    {"name": "email_sending", "level": "high"}
  ]
}
```

---

### **2. Ethics & Desires** - Compliance & Health

**Purpose:** Runtime-active ethics enforcement and continuous health monitoring

**Required Fields:**
- `ethics.framework` - Ethics framework (e.g., `harm-minimization`)
- `ethics.principles` - List of ethical principles
- `ethics.hard_constraints` - Constraints that BLOCK execution
- `desires.profile` - List of desires with weights
- `desires.health_signals` - Health monitoring configuration

**Example:**
```json
{
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
    "soft_constraints": ["inform_before_action"]
  },
  "desires": {
    "profile": [
      {"id": "trust", "weight": 0.4},
      {"id": "helpfulness", "weight": 0.3}
    ],
    "health_signals": {
      "tension_thresholds": {"stressed": 0.55, "degraded": 0.75, "critical": 0.90}
    }
  }
}
```

---

### **3. Pricing** - Commercial Terms

**Purpose:** Define commercial terms and revenue sharing

**Optional Fields:**
- `pricing.model` - Pricing model (e.g., `usage-based`, `subscription`)
- `pricing.currency` - Currency (e.g., `USD`)
- `pricing.rates` - Pricing rates
- `customers.assignments` - Customer assignments with revenue share

**Example:**
```json
{
  "pricing": {
    "model": "usage-based",
    "currency": "USD",
    "rates": {
      "per_action": 0.01
    }
  }
}
```

---

### **4. Tools** - Agent Capabilities

**Purpose:** Define what the agent can do

**Required Fields:**
- `tools` - List of tool definitions

**Tool Fields:**
- `name` - Tool name
- `description` - What the tool does
- `category` - Tool category
- `executor` - Python path to executor class
- `input_schema` - JSON schema for input
- `output_schema` - JSON schema for output
- `connection` - Connection status and provider

**Example:**
```json
{
  "tools": [
    {
      "name": "send_email",
      "description": "Send email via SMTP",
      "category": "communication",
      "executor": "agents.email.EmailExecutor",
      "connection": {"status": "connected", "provider": "smtp"}
    }
  ]
}
```

---

### **5. Memory** - State Persistence

**Purpose:** Define how the agent stores and retrieves state

**Optional Fields:**
- `memory.slots` - Memory slot definitions
- `memory.implementation` - Memory provider configuration

**Example:**
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
      }
    ]
  }
}
```

---

### **6. Schedule** - Automated Execution

**Purpose:** Define recurring tasks

**Optional Fields:**
- `schedule.jobs` - List of scheduled jobs with cron expressions

**Example:**
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
        "enabled": true
      }
    ]
  }
}
```

---

### **7. Activities** - Execution Queue

**Purpose:** Track current and pending activities

**Optional Fields:**
- `activities.queue` - Current activity queue
- `activities.execution_state` - Current execution state

**Example:**
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
      }
    ],
    "execution_state": {
      "current_activity": "activity-123",
      "queue_length": 1,
      "avg_execution_time_ms": 450
    }
  }
}
```

---

### **8. Prompt / Guardrails** - LLM Configuration

**Purpose:** Configure LLM behavior and safety

**Optional Fields:**
- `prompt.system` - System prompt
- `prompt.temperature` - LLM temperature
- `guardrails` - Input/output filters

**Example:**
```json
{
  "prompt": {
    "system": "You are a helpful email assistant.",
    "temperature": 0.7,
    "max_tokens": 4000
  },
  "guardrails": {
    "input_validation": {
      "max_length": 10000,
      "content_filters": ["profanity", "pii"]
    },
    "output_validation": {
      "max_length": 5000,
      "content_filters": ["pii", "sensitive_data"]
    }
  }
}
```

---

### **9. Team** - Multi-Agent Collaboration

**Purpose:** Define relationships with other agents

**Optional Fields:**
- `team.agent_team_graph_ref` - Reference to team graph
- `team.relationships` - List of agent relationships

**Example:**
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
      }
    ]
  }
}
```

---

### **10. Customers** - Customer Assignments

**Purpose:** Manage customer assignments and load balancing

**Optional Fields:**
- `customers.assignments` - List of customer assignments

**Example:**
```json
{
  "customers": {
    "assignments": [
      {
        "customer_id": "customer-123",
        "app_id": "app.company.crm",
        "status": "active",
        "load": {
          "requests_per_day": 150,
          "avg_response_time_ms": 450
        },
        "revenue_share": 0.90,
        "platform_fee": 0.10
      }
    ]
  }
}
```

---

### **11. Knowledge** - RAG & Data Access

**Purpose:** Define knowledge sources and data access

**Optional Fields:**
- `knowledge.rag.datasets` - RAG dataset definitions
- `knowledge.rag.retrieval_policies` - Retrieval configuration
- `knowledge.data_permissions` - Data access permissions

**Example:**
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
          "chunk_size": 512
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
      "forbidden_datasets": ["confidential"]
    }
  }
}
```

---

### **12. IO** - Input/Output Contracts

**Purpose:** Define how the agent communicates

**Required Fields:**
- `io.input_formats` - Supported input formats
- `io.output_formats` - Supported output formats

**Optional Fields:**
- `io.contracts` - IO contract definitions

**Example:**
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

### **13. Revisions** - Version Control

**Purpose:** Track changes and enable rollback

**Required Fields:**
- `revisions.current_revision` - Current revision ID
- `revisions.history` - List of past revisions

**Example:**
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
      }
    ]
  }
}
```

---

### **14. Authority & Oversight** - Governance

**Purpose:** Define who controls the agent

**Required Fields:**
- `authority.instruction` - Who instructs the agent
- `authority.oversight` - Who oversees the agent (must be different!)
- `authority.escalation` - Escalation configuration

**Optional Fields:**
- `observability` - Logging, tracing, incidents references

**Example:**
```json
{
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
  "observability": {
    "incidents_ref": "incidents://agent-123",
    "incidents": [
      {
        "id": "incident-001",
        "timestamp": "2024-01-15T10:30:00Z",
        "severity": "warning",
        "category": "ethics_violation",
        "message": "Soft constraint violated: inform_before_action"
      }
    ],
    "audit_signals": {
      "log_level": "info",
      "log_destination": "logs://agent-123",
      "trace_enabled": true
    }
  }
}
```

---

## 🎯 **Quick Tips**

### **Minimum Viable Manifest**

The absolute minimum required fields:

```json
{
  "agent_id": "agent.company.name",
  "name": "Agent Name",
  "version": "1.0.0",
  "status": "active",
  "ethics": {
    "framework": "harm-minimization",
    "hard_constraints": ["no_harm"]
  },
  "desires": {
    "profile": [{"id": "trust", "weight": 1.0}]
  },
  "tools": [],
  "io": {
    "input_formats": ["text"],
    "output_formats": ["text"]
  },
  "revisions": {
    "current_revision": "rev-001",
    "history": []
  },
  "authority": {
    "instruction": {"type": "human", "id": "user"},
    "oversight": {"type": "human", "id": "supervisor", "independent": true}
  }
}
```

---

## 📚 **Resources**

- **[Agent Standard v1 Spec](README.md)** - Complete specification
- **[Complete Implementation](../../../core/agent_standard/)** - Full source code and runtime
- **[Examples](../../../core/agent_standard/examples/)** - Real-world manifest examples

---

**Use this as a quick reference when building your agents! 🚀**

