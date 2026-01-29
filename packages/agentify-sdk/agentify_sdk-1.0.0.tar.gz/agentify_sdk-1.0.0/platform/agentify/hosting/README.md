# 🏠 Agentify Hosting Agent

**Default infrastructure for container management and agent deployment**

**Version:** 1.0.0  
**Status:** 🚧 In Development  
**Deployment:** Railway (Cloud) / Local (Development)

---

## 🎯 **What is the Hosting Agent?**

The Hosting Agent is the **default infrastructure component** that:

- 🐳 **Manages Containers** - Creates, starts, stops, deletes agent containers
- 📍 **Tracks Addresses** - Knows where each agent runs (IP, Port, URL)
- 💚 **Health Monitoring** - Continuous health checks for all agents
- 📊 **Resource Management** - CPU, RAM, disk usage tracking
- 🔄 **Auto-Scaling** - Automatic scaling based on load
- 🔐 **Authentication** - CoreSense IAM integration
- 📡 **Agent Protocol** - Communicates via Agent Communication Protocol

---

## 🏗️ **Architecture**

The Hosting Agent is itself an **Agentify App** with:

- **Frontend (UI)**: React + Vite + Tailwind + shadcn/ui
- **Backend (Orchestrator)**: Node.js + Express (TypeScript)
- **Container Runtime**: Docker / K3s
- **Auth**: CoreSense IAM
- **Communication**: Agent Communication Protocol

---

## 📋 **Quick Start**

### **Option 1: Local Development**

```bash
# Clone repository
cd platform/agentify/hosting

# Install dependencies
cd ui && npm install
cd ../orchestrator && npm install

# Start services
docker-compose up -d

# Access UI
open http://localhost:3001
```

### **Option 2: Deploy to Railway**

1. Connect GitHub repository
2. Deploy `platform/agentify/hosting`
3. Add environment variables (see `.env.example`)
4. Access at your Railway URL

---

## 🤖 **Components**

### **1. Hosting Orchestrator**

**Agent ID:** `agent.agentify.hosting-orchestrator`

**Capabilities:**
- Container management (create, start, stop, delete)
- Health monitoring
- Auto-scaling
- Address registry

**Communication:**
- Receives deployment requests from Marketplace
- Sends container status to Marketplace
- Provides agent addresses to App Orchestrators

### **2. Hosting UI**

**Features:**
- Container list with real-time status
- Resource usage charts (CPU, RAM, disk)
- Log viewer (tail -f style)
- Start/Stop/Restart buttons
- Manual container creation (for testing)

---

## 📡 **Communication Examples**

### **Deploy Agent**

**Marketplace → Hosting:**
```json
{
  "type": "request",
  "sender": "agent.marketplace.orchestrator",
  "to": ["agent.hosting.orchestrator"],
  "intent": "create_container",
  "payload": {
    "agent_id": "agent.calculator.calculation",
    "customer_id": "customer-123",
    "image": "local/calculation-agent:1.0.0",
    "env": { "PORT": "8000" },
    "resources": { "cpu": "0.5", "memory": "512Mi" }
  }
}
```

**Hosting → Marketplace:**
```json
{
  "type": "inform",
  "sender": "agent.hosting.orchestrator",
  "to": ["agent.marketplace.orchestrator"],
  "intent": "container_created",
  "payload": {
    "container_id": "calc-cust-123-abc",
    "address": "http://calc-cust-123:8000",
    "health_url": "http://calc-cust-123:8000/health"
  }
}
```

### **Get Agent Address**

**App Orchestrator → Marketplace → Hosting:**
```json
{
  "type": "request",
  "sender": "agent.app.orchestrator",
  "to": ["agent.hosting.orchestrator"],
  "intent": "get_address",
  "payload": {
    "agent_id": "agent.calculator.calculation",
    "customer_id": "customer-123"
  }
}
```

**Hosting → Marketplace → App Orchestrator:**
```json
{
  "type": "inform",
  "sender": "agent.hosting.orchestrator",
  "to": ["agent.app.orchestrator"],
  "intent": "agent_address",
  "payload": {
    "address": "http://calc-cust-123:8000",
    "health": "healthy",
    "uptime": 3600
  }
}
```

---

## 📚 **Documentation**

- **Requirements**: `HOSTING_AGENT_REQUIREMENTS.md` - Complete requirements
- **Agent Standard**: `../agent_standard/README.md` - Agent Standard v1
- **Communication**: `../agent_standard/COMMUNICATION.md` - Agent Protocol
- **Authentication**: `../agent_standard/AUTHENTICATION.md` - Auth & IAM

---

## 🚀 **Next Steps**

1. **Implement Hosting Orchestrator**
2. **Implement Hosting UI**
3. **Test with Calculator PoC agents**
4. **Deploy to Railway**
5. **Integrate with Marketplace**

---

**Status:** 🚧 Ready to implement  
**Version:** 1.0.0  
**Date:** 2026-01-16

