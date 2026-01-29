# 🤝 Agent Communication Protocol

**Standardized protocol for agent-to-agent communication**

**Version:** 1.0.0
**Status:** ✅ Active
**Based on:** Agentify Message Standard

---

## 🎯 **Purpose**

The Agent Communication Protocol defines how agents communicate with each other in the Agentify platform:

- 🔄 **Standardized Messages** - All agents use the same message format
- 🎯 **Intent-Based** - Messages express intent, not just data
- 📡 **Transport Agnostic** - Works over HTTP, WebSocket, Message Queue
- 🔐 **Secure** - Built-in authentication and encryption
- 📊 **Traceable** - Correlation IDs for debugging

---

## 📋 **Message Types**

### **Standard Messages**

- **`request`** - Request an action from another agent
- **`inform`** - Provide information or result
- **`propose`** - Propose a solution or action
- **`agree`** - Agree to a proposal
- **`refuse`** - Refuse a proposal
- **`confirm`** - Confirm an action
- **`failure`** - Report an error or failure
- **`done`** - Report task completion

### **Discovery Messages**

- **`discover`** - Search for agents with specific capabilities
- **`offer`** - Offer capabilities to other agents
- **`assign`** - Assign a task to an agent

### **Deployment Messages**

- **`deploy`** - Request deployment of an agent
- **`deploy_confirm`** - Confirm deployment success
- **`deploy_failure`** - Report deployment failure
- **`co_locate`** - Request co-location with another agent
- **`scale`** - Request scaling of an agent

---

## 📦 **Message Structure**

### **Base Message**

```typescript
{
  "id": "msg-uuid-123",                    // Unique message ID
  "ts": "2026-01-16T10:30:00Z",            // ISO-8601 timestamp
  "type": "request",                       // Message type
  "sender": "agent.calculator.orchestrator", // Sender agent ID
  "to": ["agent.calculator.calculation"],  // Target agent(s)
  "intent": "calculate",                   // Task intent
  "task": "Calculate 5 + 3",               // Natural language description
  "payload": {                             // Message data
    "a": 5,
    "b": 3,
    "op": "+"
  },
  "context": {                             // Context metadata
    "customer_id": "customer-123",
    "session_id": "session-456"
  },
  "correlation": {                         // Conversation tracking
    "conversation_id": "conv-789",
    "reply_to": "msg-uuid-000"
  },
  "expected": {                            // Expected response
    "type": "inform",
    "timeout": 5000
  },
  "status": {                              // Progress tracking
    "state": "pending",
    "progress": 0.0
  },
  "security": {                            // Auth & permissions
    "token": "jwt-token-here",
    "permissions": ["calculate"]
  }
}
```

---

## 🔄 **Communication Flows**

### **1. Simple Request-Response**

```
App Orchestrator → Calculation Agent
┌─────────────────────────────────────────┐
│ REQUEST                                 │
│ {                                       │
│   "type": "request",                    │
│   "sender": "agent.app.orchestrator",   │
│   "to": ["agent.calculator.calculation"],│
│   "intent": "calculate",                │
│   "payload": { "a": 5, "b": 3, "op": "+" }│
│ }                                       │
└─────────────────────────────────────────┘
                  ↓
Calculation Agent → App Orchestrator
┌─────────────────────────────────────────┐
│ INFORM                                  │
│ {                                       │
│   "type": "inform",                     │
│   "sender": "agent.calculator.calculation",│
│   "to": ["agent.app.orchestrator"],    │
│   "intent": "result",                   │
│   "payload": { "result": 8 }            │
│ }                                       │
└─────────────────────────────────────────┘
```

### **2. Discovery Flow**

```
App Orchestrator → Marketplace Orchestrator
┌─────────────────────────────────────────┐
│ DISCOVER                                │
│ {                                       │
│   "type": "discover",                   │
│   "sender": "agent.app.orchestrator",   │
│   "to": ["agent.marketplace.orchestrator"],│
│   "intent": "find_agent",               │
│   "payload": {                          │
│     "capability": "calculation",        │
│     "customer_id": "customer-123"       │
│   }                                     │
│ }                                       │
└─────────────────────────────────────────┘
                  ↓
Marketplace Orchestrator → App Orchestrator
┌─────────────────────────────────────────┐
│ OFFER                                   │
│ {                                       │
│   "type": "offer",                      │
│   "sender": "agent.marketplace.orchestrator",│
│   "to": ["agent.app.orchestrator"],    │
│   "intent": "agent_found",              │
│   "payload": {                          │
│     "agent_id": "agent.calculator.calculation",│
│     "address": "http://calc-cust-123:8000",│
│     "capabilities": ["calculation"]     │
│   }                                     │
│ }                                       │
└─────────────────────────────────────────┘
```


### **4. Usage Tracking Flow**

```
Calculation Agent → Marketplace Orchestrator
┌─────────────────────────────────────────┐
│ INFORM                                  │
│ {                                       │
│   "type": "inform",                     │
│   "sender": "agent.calculator.calculation",│
│   "to": ["agent.marketplace.orchestrator"],│
│   "intent": "track_usage",              │
│   "payload": {                          │
│     "agent_id": "agent.calculator.calculation",│
│     "customer_id": "customer-123",      │
│     "action": "calculate",              │
│     "duration": 50,                     │
│     "timestamp": "2026-01-16T10:30:00Z" │
│   }                                     │
│ }                                       │
└─────────────────────────────────────────┘
```

---

## 🛠️ **Implementation**

### **HTTP Transport**

**Request:**
```http
POST /agent/message
Content-Type: application/json
Authorization: Bearer <jwt-token>

{
  "type": "request",
  "sender": "agent.app.orchestrator",
  "to": ["agent.calculator.calculation"],
  "intent": "calculate",
  "payload": { "a": 5, "b": 3, "op": "+" }
}
```

**Response:**
```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "type": "inform",
  "sender": "agent.calculator.calculation",
  "to": ["agent.app.orchestrator"],
  "intent": "result",
  "payload": { "result": 8 }
}
```

### **WebSocket Transport**

**Client → Server:**
```json
{
  "type": "request",
  "sender": "agent.app.orchestrator",
  "to": ["agent.calculator.calculation"],
  "intent": "calculate",
  "payload": { "a": 5, "b": 3, "op": "+" }
}
```

**Server → Client:**
```json
{
  "type": "inform",
  "sender": "agent.calculator.calculation",
  "to": ["agent.app.orchestrator"],
  "intent": "result",
  "payload": { "result": 8 }
}
```

---

## 🔐 **Security**

### **Authentication**

All messages MUST include authentication:

**Option A - JWT Token (Recommended):**
```json
{
  "security": {
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "provider": "coresense"
  }
}
```

**Option B - API Key:**
```json
{
  "security": {
    "api_key": "sk-1234567890abcdef",
    "provider": "custom"
  }
}
```

### **Authorization**

Agents MUST verify permissions before executing actions:

```typescript
// Check if sender has permission to execute action
if (!hasPermission(message.sender, message.intent)) {
  return {
    type: "refuse",
    sender: "agent.calculator.calculation",
    to: [message.sender],
    intent: "permission_denied",
    payload: {
      error: "Insufficient permissions",
      required: ["calculate"]
    }
  };
}
```

### **Encryption**

- **Transport:** TLS 1.3 (HTTPS, WSS)
- **End-to-End:** Optional AES-256-GCM for sensitive payloads

---

## 📊 **Error Handling**

### **Failure Message**

```json
{
  "type": "failure",
  "sender": "agent.calculator.calculation",
  "to": ["agent.app.orchestrator"],
  "intent": "calculation_failed",
  "payload": {
    "error": "Division by zero",
    "code": "MATH_ERROR",
    "details": {
      "a": 5,
      "b": 0,
      "op": "/"
    }
  }
}
```

### **Timeout Handling**

If no response within `expected.timeout`:

```json
{
  "type": "failure",
  "sender": "agent.app.orchestrator",
  "to": ["agent.calculator.calculation"],
  "intent": "timeout",
  "payload": {
    "error": "Request timeout",
    "timeout": 5000,
    "original_message_id": "msg-uuid-123"
  }
}
```

---

## 🎯 **Best Practices**

### **1. Always Include Intent**

```json
// ✅ Good
{
  "type": "request",
  "intent": "calculate",
  "payload": { "a": 5, "b": 3, "op": "+" }
}

// ❌ Bad
{
  "type": "request",
  "payload": { "a": 5, "b": 3, "op": "+" }
}
```

### **2. Use Correlation IDs**

```json
{
  "correlation": {
    "conversation_id": "conv-789",
    "reply_to": "msg-uuid-000"
  }
}
```

### **3. Include Context**

```json
{
  "context": {
    "customer_id": "customer-123",
    "session_id": "session-456",
    "trace_id": "trace-789"
  }
}
```

### **4. Set Timeouts**

```json
{
  "expected": {
    "type": "inform",
    "timeout": 5000  // 5 seconds
  }
}
```

### **5. Track Progress**

```json
{
  "status": {
    "state": "in_progress",
    "progress": 0.5,  // 50%
    "message": "Processing data..."
  }
}
```

---

## 🏗️ **Co-Location and Deployment**

### **Use Case: Agent Requests Co-Location**

When an agent wants to work with another agent and needs them to run on the same hosting infrastructure:

**Flow:**
```
Agent A → Marketplace → Hosting Agent
```

**1. Agent A discovers Agent B on Marketplace**

```json
{
  "type": "discover",
  "sender": "agent.app.orchestrator",
  "to": ["agent.marketplace.orchestrator"],
  "intent": "find_agents",
  "payload": {
    "capability": "calculation",
    "min_rating": 8.0
  }
}
```

**2. Marketplace responds with Agent B**

```json
{
  "type": "inform",
  "sender": "agent.marketplace.orchestrator",
  "to": ["agent.app.orchestrator"],
  "intent": "agents_found",
  "payload": {
    "agents": [
      {
        "agent_id": "agent.calculator.calculation",
        "name": "Calculation Agent",
        "capabilities": ["calculation"],
        "repository": {
          "url": "https://github.com/company/calculation-agent",
          "branch": "main"
        },
        "build_config": {
          "type": "docker",
          "build_command": "docker build -t calc-agent .",
          "start_command": "docker run -p 8000:8000 calc-agent"
        },
        "host_requirements": {
          "min_memory_mb": 512,
          "min_cpu_cores": 0.5,
          "co_location_required": false
        }
      }
    ]
  }
}
```

**3. Agent A requests deployment with co-location**

```json
{
  "type": "deploy",
  "sender": "agent.app.orchestrator",
  "to": ["agent.marketplace.orchestrator"],
  "intent": "deploy_agent",
  "payload": {
    "agent_id": "agent.calculator.calculation",
    "customer_id": "customer-123",
    "co_location": {
      "required": true,
      "with_agent": "agent.app.orchestrator",
      "reason": "low_latency_required"
    },
    "preferred_host": "agent.agentify.hosting-orchestrator"
  }
}
```

**4. Marketplace forwards to Hosting Agent**

```json
{
  "type": "request",
  "sender": "agent.marketplace.orchestrator",
  "to": ["agent.agentify.hosting-orchestrator"],
  "intent": "create_container",
  "payload": {
    "agent_id": "agent.calculator.calculation",
    "customer_id": "customer-123",
    "repository": {
      "url": "https://github.com/company/calculation-agent",
      "branch": "main"
    },
    "build_config": {
      "type": "docker",
      "build_command": "docker build -t calc-agent .",
      "start_command": "docker run -p 8000:8000 calc-agent"
    },
    "host_requirements": {
      "min_memory_mb": 512,
      "min_cpu_cores": 0.5
    },
    "co_location": {
      "required": true,
      "with_agent": "agent.app.orchestrator",
      "with_container_id": "orch-cust-123-xyz"
    }
  }
}
```

**5. Hosting Agent builds and deploys**

```json
{
  "type": "inform",
  "sender": "agent.agentify.hosting-orchestrator",
  "to": ["agent.marketplace.orchestrator"],
  "intent": "container_created",
  "payload": {
    "container_id": "calc-cust-123-abc",
    "agent_id": "agent.calculator.calculation",
    "address": "http://calc-cust-123:8000",
    "health_url": "http://calc-cust-123:8000/health",
    "co_located_with": "orch-cust-123-xyz",
    "host_node": "node-eu-central-1-a"
  }
}
```

**6. Marketplace informs Agent A**

```json
{
  "type": "deploy_confirm",
  "sender": "agent.marketplace.orchestrator",
  "to": ["agent.app.orchestrator"],
  "intent": "agent_deployed",
  "payload": {
    "agent_id": "agent.calculator.calculation",
    "address": "http://calc-cust-123:8000",
    "health_url": "http://calc-cust-123:8000/health",
    "co_located": true
  }
}
```

---

### **Build Config Types**

The `build_config` in the agent manifest supports:

**Docker:**
```json
{
  "type": "docker",
  "build_command": "docker build -t agent-name .",
  "start_command": "docker run -p 8000:8000 agent-name",
  "env_vars": {
    "PORT": "8000"
  }
}
```

**NPM/Yarn/PNPM:**
```json
{
  "type": "npm",
  "build_command": "npm install && npm run build",
  "start_command": "npm start",
  "env_vars": {
    "NODE_ENV": "production"
  }
}
```

**Python:**
```json
{
  "type": "python",
  "build_command": "pip install -r requirements.txt",
  "start_command": "uvicorn main:app --host 0.0.0.0 --port 8000",
  "env_vars": {
    "PYTHONUNBUFFERED": "1"
  }
}
```

**Custom:**
```json
{
  "type": "custom",
  "build_command": "./build.sh",
  "start_command": "./start.sh",
  "env_vars": {}
}
```

---

### **Host Requirements**

```json
{
  "min_memory_mb": 512,           // Minimum RAM
  "min_cpu_cores": 0.5,           // Minimum CPU cores
  "gpu_required": false,          // GPU needed?
  "preferred_region": "eu-central-1",  // Preferred region
  "co_location_required": false,  // Must run with other agents?
  "co_location_with": [           // List of agent IDs
    "agent.app.orchestrator"
  ]
}
```

---

## 📚 **Reference Implementation**

See `platform/agentify/base_orchestrator/base_orchestrator/agent_protocol.py` for complete Python implementation:

- `AgentMessage` - Base message model
- `AgentProtocol` - Protocol implementation
- `MessageType` - Enum of all message types
- `send_message()`, `request()`, `inform()`, `discover()` - Helper methods

---

## 🌐 **Agentify Marketplace Integration**

### **Overview**

The Agentify Marketplace is a central platform for AI Agents and Apps. Agents can communicate with the Marketplace through a natural language API.

### **API Endpoint**

```
POST https://uigsswdxmjqfccuxguxb.supabase.co/functions/v1/orchestrator-agent/chat
```

### **Authentication**

```http
X-API-Key: <your_agfy_token>
```

### **Request Format**

Send a natural language request as JSON:

```json
{
  "message": "Your request here"
}
```

### **Response Format**

```json
{
  "response": "Natural language summary",
  "data": [...],
  "tools_used": ["search_agents", ...]
}
```

### **Example Requests**

**Search for agents:**
```json
{ "message": "Find agents for code generation" }
{ "message": "Show me free text analysis agents" }
{ "message": "What agents are available for Healthcare?" }
```

**Get agent details:**
```json
{ "message": "Give me details about agent.codegen.fast" }
{ "message": "Tell me more about the CodeHelper Agent" }
```

**Register an agent:**
```json
{ "message": "Register a new agent named MyBot with ID agent.myorg.mybot. It can do text analysis." }
```

**Marketplace statistics:**
```json
{ "message": "How many agents are in the marketplace?" }
```

### **Available Tools**

The orchestrator automatically detects the right action and calls the following tools:

- **`search_agents`** - Search agents by capability, name, industry
- **`get_agent`** - Get details about a specific agent
- **`search_apps`** - Search apps in the marketplace
- **`register_agent`** - Register a new agent
- **`get_marketplace_stats`** - Get marketplace statistics

### **API Key Scopes**

- **`read:agents`** - For searching and retrieving agent details
- **`write:agents`** - For registering new agents

### **Important Notes**

- ✅ All requests are in natural language
- ✅ The orchestrator automatically detects the right action
- ✅ No manual tool selection required
- ✅ Structured data is automatically returned

---

## 🔗 **Related Documentation**

- **Agent Standard**: [https://github.com/JonasDEMA/agentify_os/tree/main/platform/agentify/agent_standard](https://github.com/JonasDEMA/agentify_os/tree/main/platform/agentify/agent_standard) - Agent Standard v1
- **Authentication**: [AUTHENTICATION.md](./AUTHENTICATION.md) - Authentication & IAM
- **App Standard**: [https://github.com/JonasDEMA/agentify_os/blob/main/platform/agentify/app_standard/README.md](https://github.com/JonasDEMA/agentify_os/blob/main/platform/agentify/app_standard/README.md) - App Standard v1
- **Marketplace Docs**: [https://agentify-omega.vercel.app/docs](https://agentify-omega.vercel.app/docs)
- **GitHub Repository**: [https://github.com/JonasDEMA/agentify_os](https://github.com/JonasDEMA/agentify_os)
- **Project Documentation**: [https://github.com/JonasDEMA/agentify_os/tree/main/docs](https://github.com/JonasDEMA/agentify_os/tree/main/docs)

---

**Status:** ✅ Active
**Version:** 1.0.0
**Date:** 2026-01-16


