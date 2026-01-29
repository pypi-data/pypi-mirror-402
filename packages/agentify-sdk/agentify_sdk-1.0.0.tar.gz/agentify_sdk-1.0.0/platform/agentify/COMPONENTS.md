# 🧩 Agentify Platform Components

**Complete overview of all platform components**

---

## 📦 **Component Overview**

```
platform/agentify/
├── app_standard/          # App Standard (React apps)
├── agent_standard/        # Agent Standard (autonomous agents)
├── marketplace/           # Marketplace (discovery & acquisition)
├── data_sharing/          # Data Sharing Protocol (RBAC)
├── orchestrator/          # Orchestrator Agent (team builder)
├── billing/               # Billing Service (revenue sharing)
├── ARCHITECTURE.md        # Platform architecture
├── QUICKSTART.md          # Quick start guide
└── README.md              # Main documentation
```

---

## 📱 **1. App Standard**

**React applications with built-in orchestrators**

### **Purpose**
Define how React apps integrate with the Agentify platform.

### **Key Features**
- ✅ Standalone & Integrated modes
- ✅ Built-in orchestrator agent
- ✅ Marketplace integration
- ✅ Team building UI
- ✅ Zustand state management

### **Documentation**
- [App Standard Spec](app_standard/README.md)
- [Quick Start](app_standard/QUICKSTART.md)
- [AI Prompts](app_standard/prompts/)
- [Examples](app_standard/examples/)

### **Use Cases**
- Build React apps with agent teams
- Integrate with marketplace
- Manage agent teams via UI

---

## 🤖 **2. Agent Standard**

**Autonomous agents that join teams**

### **Purpose**
Define how agents register, communicate, and join teams.

### **Key Features**
- ✅ Agent manifest (JSON)
- ✅ Capability declaration
- ✅ Pricing model
- ✅ Marketplace registration
- ✅ Team membership

### **Documentation**
- [Agent Standard Spec](agent_standard/README.md)
- [Quick Start](agent_standard/QUICKSTART.md)
- [AI Prompts](agent_standard/prompts/)
- [Examples](agent_standard/examples/)

### **Use Cases**
- Build autonomous agents
- Register in marketplace
- Join app teams

---

## 🏪 **3. Marketplace**

**Central hub for agent discovery and acquisition**

### **Purpose**
Enable discovery, acquisition, and team building.

### **Key Features**
- ✅ Agent discovery (search & filter)
- ✅ Pricing & billing
- ✅ Trust & ratings (1-10)
- ✅ LLM-guided team recommendations
- ✅ Creator verification

### **Documentation**
- [Marketplace Spec](marketplace/README.md)
- [API Reference](marketplace/API.md)

### **Use Cases**
- Discover agents by capability
- Get team recommendations
- Book agents for apps

---

## 🔄 **4. Data Sharing Protocol**

**Secure cross-app data access with RBAC**

### **Purpose**
Enable secure data exchange between apps.

### **Key Features**
- ✅ RBAC permissions (owner, admin, editor, viewer)
- ✅ REST + JSON API
- ✅ Audit trail
- ✅ Flexible storage (cloud, edge, local)
- ✅ Encryption (TLS 1.3 + E2E)

### **Documentation**
- [Data Sharing Spec](data_sharing/README.md)
- [API Reference](data_sharing/API.md)

### **Use Cases**
- Share data between apps
- Grant/revoke access
- Audit data access

---

## 🎯 **5. Orchestrator Agent**

**Every app's built-in team builder and manager**

### **Purpose**
Discover, build, and manage agent teams.

### **Key Features**
- ✅ Requirement analysis
- ✅ Marketplace discovery
- ✅ LLM-guided recommendations
- ✅ Human-in-the-loop review
- ✅ Team management

### **Documentation**
- [Orchestrator Spec](orchestrator/README.md)
- [Implementation Guide](orchestrator/IMPLEMENTATION.md)

### **Use Cases**
- Build agent teams
- Monitor team health
- Scale teams

---

## 💰 **6. Billing Service**

**Automatic billing and revenue sharing**

### **Purpose**
Track usage and distribute revenue.

### **Key Features**
- ✅ Usage tracking
- ✅ Automatic billing
- ✅ Revenue sharing (90/10 split)
- ✅ Creator payouts
- ✅ Marketplace fees

### **Documentation**
- [Billing Spec](billing/README.md)
- [API Reference](billing/API.md)

### **Use Cases**
- Track agent usage
- Bill users
- Pay creators

---

## 🔗 **Component Interactions**

```
┌─────────────────────────────────────────────────────────────┐
│                      Agentify Platform                       │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │                    App (React)                       │  │
│  │  ┌────────────────────────────────────────────────┐ │  │
│  │  │         Orchestrator Agent                     │ │  │
│  │  │  - Discovers agents via Marketplace            │ │  │
│  │  │  - Builds teams with LLM guidance              │ │  │
│  │  │  - Manages team health                         │ │  │
│  │  └────────────┬───────────────────────────────────┘ │  │
│  │               │                                      │  │
│  │  ┌────────────▼────────────┐  ┌──────────────────┐ │  │
│  │  │  Team of Agents         │  │  Data Sharing    │ │  │
│  │  │  - Agent A              │  │  - RBAC          │ │  │
│  │  │  - Agent B              │  │  - Audit         │ │  │
│  │  │  - Agent C              │  │                  │ │  │
│  │  └─────────────────────────┘  └──────────────────┘ │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │                    Marketplace                       │  │
│  │  - Agent Registry                                    │  │
│  │  - Search & Discovery                                │  │
│  │  - Team Recommendations                              │  │
│  │  - Billing & Revenue Sharing                         │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 🎯 **Component Dependencies**

| Component | Depends On | Used By |
|-----------|------------|---------|
| **App Standard** | Agent Standard, Marketplace | - |
| **Agent Standard** | - | App Standard, Marketplace |
| **Marketplace** | Agent Standard, Billing | App Standard, Orchestrator |
| **Data Sharing** | - | App Standard |
| **Orchestrator** | Marketplace, Agent Standard | App Standard |
| **Billing** | - | Marketplace |

---

## 📊 **Component Maturity**

| Component | Status | Version | Stability |
|-----------|--------|---------|-----------|
| **App Standard** | ✅ Stable | 1.0.0 | Production-ready |
| **Agent Standard** | ✅ Stable | 1.0.0 | Production-ready |
| **Marketplace** | 🚧 Beta | 0.9.0 | Testing |
| **Data Sharing** | ✅ Stable | 1.0.0 | Production-ready |
| **Orchestrator** | ✅ Stable | 1.0.0 | Production-ready |
| **Billing** | 🚧 Beta | 0.8.0 | Testing |

---

## 🚀 **Getting Started**

### **For App Developers**
1. Read [App Standard](app_standard/README.md)
2. Follow [Quick Start](QUICKSTART.md)
3. Build your first app

### **For Agent Developers**
1. Read [Agent Standard](agent_standard/README.md)
2. Follow [Quick Start](agent_standard/QUICKSTART.md)
3. Register in marketplace

### **For Platform Operators**
1. Read [Architecture](ARCHITECTURE.md)
2. Deploy marketplace
3. Configure billing

---

## 📚 **Additional Resources**

- **[Architecture](ARCHITECTURE.md)** - Platform architecture
- **[Deployment](../../DEPLOYMENT.md)** - Deploy to Cloud/Edge/Desktop
- **[Contributing](../../CONTRIBUTING.md)** - How to contribute
- **[License](../../LICENSE.md)** - Dual License (MIT + Commercial)

---

**Next:** [Architecture](ARCHITECTURE.md) - Deep dive into platform architecture

