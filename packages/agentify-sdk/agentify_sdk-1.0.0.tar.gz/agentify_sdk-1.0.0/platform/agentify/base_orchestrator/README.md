# 🎯 Base Orchestrator Agent

**Standard orchestrator for all Agentify apps**

**Version:** 1.0.0  
**Status:** ✅ Active  
**Language:** Python 3.11+

---

## 🎯 **What is the Base Orchestrator?**

The Base Orchestrator is a **standard agent** that every Agentify app gets automatically. It provides:

- 🔍 **Marketplace Discovery** - Searches for agents by capability
- 🤝 **Team Building** - Proposes and manages agent teams
- 📡 **Agent Communication** - Handles Agent Communication Protocol
- 💾 **Data Layer Management** - Manages app data (Supabase/Agent/Service)
- 📊 **Logging** - Structured logging for debugging
- 🔐 **Authentication** - CoreSense IAM integration

---

## 🏗️ **Architecture**

```
┌─────────────────────────────────────────┐
│      Base Orchestrator Agent            │
├─────────────────────────────────────────┤
│                                         │
│  ┌─────────────────────────────────┐   │
│  │  Marketplace Discovery          │   │
│  │  - Search by capability         │   │
│  │  - Filter by rating/price       │   │
│  └─────────────────────────────────┘   │
│                                         │
│  ┌─────────────────────────────────┐   │
│  │  Team Builder                   │   │
│  │  - Propose team                 │   │
│  │  - Wait for confirmation        │   │
│  │  - Manage team lifecycle        │   │
│  └─────────────────────────────────┘   │
│                                         │
│  ┌─────────────────────────────────┐   │
│  │  Agent Communication            │   │
│  │  - Send/Receive messages        │   │
│  │  - Handle responses             │   │
│  │  - Track conversations          │   │
│  └─────────────────────────────────┘   │
│                                         │
│  ┌─────────────────────────────────┐   │
│  │  Data Layer                     │   │
│  │  - Supabase integration         │   │
│  │  - Data Agent delegation        │   │
│  │  - External service calls       │   │
│  └─────────────────────────────────┘   │
│                                         │
└─────────────────────────────────────────┘
```

---

## 🚀 **Quick Start**

### **Installation**

```bash
cd platform/agentify/base_orchestrator
pip install -r requirements.txt
```

### **Usage in Your App**

```python
from base_orchestrator import BaseOrchestrator

# Initialize orchestrator
orchestrator = BaseOrchestrator(
    app_id="app.calculator",
    app_name="Calculator App",
    marketplace_url="http://localhost:8080"  # or marketplace.meet-harmony.ai
)

# Discover agents
print("🔍 Searching for agents...")
team = orchestrator.discover_and_build_team(
    required_capabilities=["calculation", "formatting"]
)

# Confirm team
print(f"\n📋 Proposed Team:")
for agent in team:
    print(f"  - {agent['name']} ({agent['capability']})")
    
confirm = input("\n✅ Confirm team? (y/n): ")
if confirm.lower() == 'y':
    orchestrator.confirm_team(team)
    print("✅ Team confirmed!")
    
    # Use team
    result = orchestrator.execute_task(
        capability="calculation",
        action="calculate",
        params={"a": 5, "b": 3, "op": "+"}
    )
    print(f"Result: {result}")
```

---

## 📋 **Features**

### **1. Marketplace Discovery**

Search for agents by capability:

```python
agents = orchestrator.discover_agents(
    capability="calculation",
    min_rating=8.0,
    max_price=0.01
)
```

### **2. Team Building**

Build a team from discovered agents:

```python
team = orchestrator.build_team(
    required_capabilities=["calculation", "formatting"]
)
```

### **3. Agent Communication**

Send messages to agents:

```python
response = orchestrator.send_message(
    agent_id="agent.calculator.calculation",
    message_type="request",
    intent="calculate",
    payload={"a": 5, "b": 3, "op": "+"}
)
```

### **4. Data Layer**

Store and retrieve data:

```python
# Store data
orchestrator.store_data("calculations", {
    "input": {"a": 5, "b": 3, "op": "+"},
    "result": 8
})

# Retrieve data
data = orchestrator.get_data("calculations")
```

---

## 📦 **Project Structure**

```
platform/agentify/base_orchestrator/
├── base_orchestrator/
│   ├── __init__.py
│   ├── orchestrator.py          # Main orchestrator class
│   ├── marketplace.py            # Marketplace discovery
│   ├── team_builder.py           # Team building logic
│   ├── agent_protocol.py         # Agent Communication Protocol
│   ├── data_layer.py             # Data management
│   └── models.py                 # Pydantic models
├── tests/
│   ├── test_orchestrator.py
│   ├── test_marketplace.py
│   └── test_team_builder.py
├── examples/
│   └── calculator_app.py         # Example usage
├── manifest.json                 # Agent manifest
├── requirements.txt
└── README.md
```

---

## 🎯 **Next Steps**

1. ✅ Implement core orchestrator
2. ✅ Implement marketplace discovery
3. ✅ Implement team builder
4. ✅ Implement agent protocol
5. ✅ Add tests
6. ✅ Add example app

---

**Status:** 🚧 Ready to implement  
**Version:** 1.0.0  
**Date:** 2026-01-16

