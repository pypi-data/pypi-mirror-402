# 🤖 Agent Standard v1 - Agentic Economy

**Version**: 1.0.0
**Status**: Production
**Last Updated**: 2026-01-19

> 🚀 **Quick Start:** [QUICKSTART_COMPLETE.md](QUICKSTART_COMPLETE.md) - Create your first agent in 5 minutes!
>
> 📖 **Agent Anatomy:** [AGENT_ANATOMY.md](AGENT_ANATOMY.md) - Complete reference for all 14 core areas
>
> 📊 **Implementation Status:** [../platform/agentify/agent_standard/IMPLEMENTATION_STATUS.md](../platform/agentify/agent_standard/IMPLEMENTATION_STATUS.md)
>
> 📝 **Complete Example:** [examples/complete_agent_example.json](examples/complete_agent_example.json) - All 14 sections

---

## 📋 Overview

This module implements the **Agentic Economy Agent Standard v1** - a comprehensive specification for autonomous agents with:

- ✅ **Ethics-First Design**: Ethical constraints as runtime-active control layer
- ✅ **Desire Profiles**: Health monitoring and alignment indicators
- ✅ **Four-Eyes Principle**: Mandatory separation of Instruction & Oversight
- ✅ **Framework Agnostic**: Works with LangChain, n8n, Make.com, custom runtimes
- ✅ **Universal Runtime**: Same agent definition works on Cloud, Edge, Desktop
- ✅ **Incident Reporting**: Non-punitive reporting without consequences
- ✅ **Recursive Oversight**: Oversight agents are themselves overseen
- ✅ **JSON-First**: Agents describe themselves purely via JSON manifest

---

## 🏗️ Architecture

```
core/agent_standard/
├── README.md                    # This file
├── __init__.py                  # Package exports
│
├── models/                      # Data models
│   ├── __init__.py
│   ├── manifest.py              # Agent Manifest (complete spec)
│   ├── ethics.py                # Ethics framework & principles
│   ├── desires.py               # Desire profiles & health
│   ├── authority.py             # Authority & oversight
│   ├── io_contracts.py          # Input/output contracts
│   └── schemas.py               # JSON schemas for validation
│
├── core/                        # Core agent implementation
│   ├── __init__.py
│   ├── agent.py                 # Universal Agent class
│   ├── ethics_engine.py         # Runtime ethics evaluation
│   ├── desire_monitor.py        # Health & desire monitoring
│   ├── oversight.py             # Oversight & escalation
│   └── runtime.py               # Runtime wrapper (Cloud/Edge/Desktop)
│
├── adapters/                    # Framework adapters
│   ├── __init__.py
│   ├── langchain_adapter.py     # LangChain compatibility
│   ├── n8n_adapter.py           # n8n workflow adapter
│   ├── make_adapter.py          # Make.com adapter
│   └── base_adapter.py          # Base adapter interface
│
├── validation/                  # Validation & compliance
│   ├── __init__.py
│   ├── manifest_validator.py   # Manifest validation
│   ├── authority_validator.py  # Authority separation checks
│   └── compliance_checker.py   # Full compliance validation
│
└── examples/                    # Example agents
    ├── meeting_assistant.json   # Meet Harmony example
    ├── risk_auditor.json        # Risk auditor example
    └── simple_agent.json        # Minimal compliant agent
```

---

## 🎯 Core Principles

### 1. **Ethics Override All**
Ethics are **not documentation**. They are **runtime-active constraints** evaluated on every decision.

### 2. **Desires as Health Indicators**
Desires serve as diagnostic signals. Persistent suppression triggers oversight review.

### 3. **Four-Eyes Principle (Mandatory)**
Every agent MUST have:
- **Instruction Authority** (assigns tasks)
- **Oversight Authority** (monitors, audits, escalates)

These MUST be different entities.

### 4. **Framework Agnostic**
Agents can use LangChain, n8n, Make.com, or custom runtimes - but the **manifest is the source of truth**.

### 5. **Universal Runtime**
Same agent definition works on:
- ☁️ **Cloud** (Railway, AWS, Azure)
- 🔌 **Edge** (IoT devices, local servers)
- 💻 **Desktop** (Windows, Mac, Linux)

---

## 📦 Required Manifest Fields

Every compliant agent MUST include:

```json
{
  "agent_id": "string (required)",
  "name": "string (required)",
  "version": "string (required)",
  "status": "draft|active|paused|retired (required)",
  "revisions": { ... } (required),
  "overview": { ... } (required),
  "capabilities": [ ... ] (required),
  "ethics": { ... } (required, runtime-active),
  "desires": { ... } (required, runtime-active),
  "authority": {
    "instruction": { ... } (required),
    "oversight": { ... } (required, must be independent)
  } (required),
  "escalation": { ... } (required),
  "io": { ... } (required)
}
```

---

## 🚀 Quick Start

### 1. Create Agent Manifest

```python
from core.agent_standard import AgentManifest, EthicsFramework, DesireProfile

manifest = AgentManifest(
    agent_id="agent.demo.my-agent",
    name="My First Agent",
    version="1.0.0",
    # ... see examples/
)
```

### 2. Validate Manifest

```python
from core.agent_standard import ManifestValidator

validator = ManifestValidator()
result = validator.validate(manifest)

if not result.is_valid:
    print(f"Validation errors: {result.errors}")
```

### 3. Create Agent Instance

```python
from core.agent_standard import Agent

agent = Agent(manifest=manifest)
await agent.start()
```

### 4. Execute Task

```python
result = await agent.execute({
    "task": "Summarize this meeting",
    "input": { ... }
})
```

---

## 📚 Documentation

- [Agent Manifest Specification](docs/manifest_spec.md)
- [Ethics Framework Guide](docs/ethics_guide.md)
- [Desire Profiles & Health](docs/desires_guide.md)
- [Authority & Oversight](docs/oversight_guide.md)
- [Framework Adapters](docs/adapters_guide.md)
- [Runtime Deployment](docs/runtime_guide.md)

---

## 🔒 Security & Compliance

- ✅ **Four-Eyes Principle** enforced at validation
- ✅ **Ethics evaluated** on every decision
- ✅ **Health monitoring** with automatic escalation
- ✅ **Incident reporting** without punishment
- ✅ **Recursive oversight** for oversight agents
- ✅ **Audit trails** for all actions

---

## 🌐 Universal Runtime

Agents run **identically** across environments:

| Environment | Runtime | Container | Oversight |
|-------------|---------|-----------|-----------|
| Cloud (Railway/AWS) | Docker | ✅ | Remote |
| Edge (IoT/Local) | Docker/Native | ✅ | Local + Remote |
| Desktop (Windows/Mac) | Native/Docker | Optional | Local |

---

## 📞 Support

For questions or issues, see the main documentation or create an issue.

---

**Created**: 2026-01-14  
**Authors**: HarmonyOS Team  
**License**: Proprietary

