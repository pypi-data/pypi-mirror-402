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

---

### **6. Schedule** - Automated Execution

**Purpose:** Define recurring tasks

**Optional Fields:**
- `schedule.jobs` - List of scheduled jobs with cron expressions

---

### **7. Activities** - Execution Queue

**Purpose:** Track current and pending activities

**Optional Fields:**
- `activities.queue` - Current activity queue
- `activities.execution_state` - Current execution state

---

### **8. Prompt / Guardrails** - LLM Configuration

**Purpose:** Configure LLM behavior and safety

**Optional Fields:**
- `prompt.system` - System prompt
- `prompt.temperature` - LLM temperature
- `guardrails` - Input/output filters

---

### **9. Team** - Multi-Agent Collaboration

**Purpose:** Define relationships with other agents

**Optional Fields:**
- `team.agent_team_graph_ref` - Reference to team graph
- `team.relationships` - List of agent relationships

---

### **10. Customers** - Customer Assignments

**Purpose:** Manage customer assignments and load balancing

**Optional Fields:**
- `customers.assignments` - List of customer assignments

---

### **11. Knowledge** - RAG & Data Access

**Purpose:** Define knowledge sources and data access

**Optional Fields:**
- `knowledge.rag.datasets` - RAG dataset definitions
- `knowledge.rag.retrieval_policies` - Retrieval configuration
- `knowledge.data_permissions` - Data access permissions

---

### **12. IO** - Input/Output Contracts

**Purpose:** Define how the agent communicates

**Required Fields:**
- `io.input_formats` - Supported input formats
- `io.output_formats` - Supported output formats

**Optional Fields:**
- `io.contracts` - IO contract definitions

---

### **13. Revisions** - Version Control

**Purpose:** Track changes and enable rollback

**Required Fields:**
- `revisions.current_revision` - Current revision ID
- `revisions.history` - List of past revisions

---

### **14. Authority & Oversight** - Governance

**Purpose:** Define who controls the agent

**Required Fields:**
- `authority.instruction` - Who instructs the agent
- `authority.oversight` - Who oversees the agent (must be different!)
- `authority.escalation` - Escalation configuration

**Optional Fields:**
- `observability` - Logging, tracing, incidents references

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
- **[Architecture](../../ARCHITECTURE.md)** - Detailed architecture with 14 areas
- **[Examples](examples/)** - Real-world manifest examples

---

**Use this as a quick reference when building your agents! 🚀**

