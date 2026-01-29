# 🏠 Hosting Agent - Requirements

**Default Agentify Hosting Infrastructure**

**Version:** 1.0.0
**Status:** 🚧 In Development
**Deployment:** Railway (Cloud) / Local (Development)

---

## 🎯 **Purpose**

The **Hosting Agent** is the default infrastructure component that:

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

## 🤖 **Components**

### **1. Hosting Orchestrator Agent**

**Responsibilities:**
- Receive deployment requests from Marketplace
- Create/start/stop/delete containers
- Track container addresses
- Perform health checks
- Report status to Marketplace
- Handle auto-scaling

**Manifest:**
```json
{
  "agent_id": "agent.agentify.hosting-orchestrator",
  "name": "Hosting Orchestrator",
  "version": "1.0.0",
  "status": "active",
  "capabilities": [
    "container-management",
    "health-monitoring",
    "auto-scaling",
    "address-registry"
  ],
  "ethics": {
    "framework": "harm-minimization",
    "hard_constraints": [
      "no_unauthorized_access",
      "no_data_leakage",
      "customer_isolation"
    ]
  },
  "desires": {
    "profile": [
      {"id": "reliability", "weight": 0.4},
      {"id": "performance", "weight": 0.3},
      {"id": "security", "weight": 0.3}
    ]
  },
  "tools": [
    {
      "name": "create_container",
      "description": "Create and start a new agent container",
      "category": "container-management"
    },
    {
      "name": "stop_container",
      "description": "Stop a running container",
      "category": "container-management"
    },
    {
      "name": "delete_container",
      "description": "Delete a container",
      "category": "container-management"
    },
    {
      "name": "health_check",
      "description": "Check agent health",
      "category": "monitoring"
    },
    {
      "name": "get_address",
      "description": "Get agent address (IP, Port, URL)",
      "category": "registry"
    },
    {
      "name": "scale_agent",
      "description": "Scale agent instances",
      "category": "auto-scaling"
    }
  ],
  "authority": {
    "instruction": {
      "type": "agent",
      "id": "agent.marketplace.orchestrator"
    },
    "oversight": {
      "type": "human",
      "id": "admin@meet-harmony.ai",
      "independent": true
    }
  },
  "authentication": {
    "required": true,
    "provider": "coresense",
    "provider_url": "https://iam.meet-harmony.ai",
    "roles_required": ["hosting-admin"],
    "scopes_required": ["container:manage"]
  }
}
```

### **2. Hosting UI**

**Responsibilities:**
- Display all running containers/agents
- Show health status (green/yellow/red)
- Show resource usage (CPU, RAM, disk)
- Start/Stop/Restart buttons
- View logs
- Manual container creation (for testing)

**Features:**
- Real-time updates (WebSocket)
- Container list with filters
- Log viewer (tail -f style)
- Resource charts (CPU, RAM over time)
- Alert notifications (health issues)

---

## 📋 **Core Features**



### **5. Resource Management**

**Resource Tracking:**
- CPU usage (%)
- Memory usage (MB)
- Disk usage (MB)
- Network I/O (MB/s)

**Resource Limits:**
```typescript
{
  "resources": {
    "cpu": "0.5",      // 0.5 CPU cores
    "memory": "512Mi", // 512 MB RAM
    "disk": "1Gi"      // 1 GB disk
  }
}
```

**Resource Alerts:**
- CPU > 90% for 5 minutes → Alert
- Memory > 90% for 5 minutes → Alert
- Disk > 90% → Alert

---

## 🔄 **Communication Flow**

### **Deployment Flow**

```
1. Marketplace Orchestrator → Hosting Orchestrator (Agent Protocol)
   Action: "create_container"
   Params: { agent_id, customer_id, image, env, resources }

2. Hosting Orchestrator → Docker/K3s
   Create container with specified config

3. Hosting Orchestrator → Container
   Health check: GET /health

4. Hosting Orchestrator → Marketplace Orchestrator
   Response: { container_id, address, health_url }

5. Marketplace Orchestrator → Marketplace DB
   Store: agent_id → address mapping
```

### **Discovery Flow**

```
1. App Orchestrator → Marketplace Orchestrator (Agent Protocol)
   Action: "discover_agent"
   Params: { capability: "calculation" }

2. Marketplace Orchestrator → Marketplace DB
   Search: agents with capability "calculation"

3. Marketplace Orchestrator → Hosting Orchestrator (Agent Protocol)
   Action: "get_address"
   Params: { agent_id, customer_id }

4. Hosting Orchestrator → Marketplace Orchestrator
   Response: { address: "http://calc-customer-123:8000" }

5. Marketplace Orchestrator → App Orchestrator
   Response: { agent_id, address, capabilities }

6. App Orchestrator → Calculation Agent (Direct, Agent Protocol)
   Action: "calculate"
   Params: { a: 5, b: 3, op: "+" }
```

### **Usage Tracking Flow**

```
1. Calculation Agent → Marketplace Orchestrator (Agent Protocol)
   Action: "track_usage"
   Params: { agent_id, customer_id, action: "calculate", duration: 50 }

2. Marketplace Orchestrator → Marketplace DB
   Store: usage event for billing
```

---

## 📊 **Database Schema**

### **Containers Table**

```sql
CREATE TABLE containers (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  container_id TEXT UNIQUE NOT NULL,
  agent_id TEXT NOT NULL,
  customer_id TEXT NOT NULL,
  image TEXT NOT NULL,
  address TEXT NOT NULL,
  health_url TEXT NOT NULL,
  status TEXT NOT NULL, -- 'running', 'stopped', 'error'
  health TEXT NOT NULL, -- 'healthy', 'degraded', 'unhealthy'
  cpu_usage FLOAT,
  memory_usage FLOAT,
  disk_usage FLOAT,
  load FLOAT,
  uptime INTEGER,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_containers_agent_customer ON containers(agent_id, customer_id);
CREATE INDEX idx_containers_status ON containers(status);
CREATE INDEX idx_containers_health ON containers(health);
```

### **Health Checks Table**

```sql
CREATE TABLE health_checks (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  container_id TEXT NOT NULL REFERENCES containers(container_id),
  status TEXT NOT NULL, -- 'ok', 'error'
  response_time INTEGER, -- milliseconds
  load FLOAT,
  error_message TEXT,
  checked_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_health_checks_container ON health_checks(container_id);
CREATE INDEX idx_health_checks_checked_at ON health_checks(checked_at);
```

### **Scaling Events Table**

```sql
CREATE TABLE scaling_events (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  agent_id TEXT NOT NULL,
  customer_id TEXT NOT NULL,
  action TEXT NOT NULL, -- 'scale_up', 'scale_down'
  from_instances INTEGER NOT NULL,
  to_instances INTEGER NOT NULL,
  reason TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_scaling_events_agent_customer ON scaling_events(agent_id, customer_id);
```

---

## 🎨 **UI Design**

### **Dashboard View**

```
┌─────────────────────────────────────────────────────────────┐
│  🏠 Hosting Agent - Container Management                    │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  📊 Overview                                                 │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐        │
│  │ 🟢 Running   │ │ 🔴 Stopped   │ │ 📦 Total     │        │
│  │    12        │ │     3        │ │    15        │        │
│  └──────────────┘ └──────────────┘ └──────────────┘        │
│                                                              │
│  🐳 Containers                                               │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ Filter: [All ▼] [Healthy ▼] [Customer ▼]  [🔍 Search] │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ Container ID          Agent           Status   Actions  │ │
│  ├────────────────────────────────────────────────────────┤ │
│  │ 🟢 calc-cust-123     Calculation      Healthy  [⏸][🗑]│ │
│  │    CPU: 45% | RAM: 256MB | Load: 0.3                   │ │
│  │    http://calc-cust-123:8000                           │ │
│  ├────────────────────────────────────────────────────────┤ │
│  │ 🟢 format-cust-123   Formatting       Healthy  [⏸][🗑]│ │
│  │    CPU: 12% | RAM: 128MB | Load: 0.1                   │ │
│  │    http://format-cust-123:8001                         │ │
│  ├────────────────────────────────────────────────────────┤ │
│  │ 🟡 email-cust-456    Email            Degraded [⏸][🗑]│ │
│  │    CPU: 89% | RAM: 512MB | Load: 0.8                   │ │
│  │    http://email-cust-456:8002                          │ │
│  ├────────────────────────────────────────────────────────┤ │
│  │ 🔴 data-cust-789     Data Pipeline    Unhealthy[▶][🗑]│ │
│  │    Error: Connection timeout                           │ │
│  │    http://data-cust-789:8003                           │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
│  [+ Create Container]                                        │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### **Container Details View**

```
┌─────────────────────────────────────────────────────────────┐
│  🐳 Container: calc-cust-123                                 │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  📋 Details                                                  │
│  Agent ID:      agent.calculator.calculation                │
│  Customer ID:   customer-123                                │
│  Image:         local/calculation-agent:1.0.0               │
│  Address:       http://calc-cust-123:8000                   │
│  Status:        🟢 Running (Healthy)                        │
│  Uptime:        2h 34m                                      │
│                                                              │
│  📊 Resources                                                │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ CPU Usage (%)                                         │  │
│  │ 50 ┤                                    ╭─╮           │  │
│  │ 40 ┤                          ╭─╮     ╭╯ ╰╮          │  │
│  │ 30 ┤                ╭─╮     ╭╯ ╰─╮ ╭╯   ╰╮         │  │
│  │ 20 ┤      ╭─╮     ╭╯ ╰─╮ ╭╯     ╰─╯     ╰╮        │  │
│  │ 10 ┤╭─╮ ╭╯ ╰─╮ ╭╯     ╰─╯                ╰─       │  │
│  │  0 ┴┴─┴─┴─────┴─────────────────────────────────   │  │
│  │    10m  20m  30m  40m  50m  60m                      │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
│  Current: CPU 45% | RAM 256MB | Disk 128MB | Load 0.3      │
│                                                              │
│  📜 Logs (last 100 lines)                                   │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ [2026-01-16 10:23:45] [INFO] Agent started            │  │
│  │ [2026-01-16 10:23:46] [INFO] Listening on port 8000   │  │
│  │ [2026-01-16 10:24:12] [INFO] Received calculation     │  │
│  │ [2026-01-16 10:24:12] [INFO] Result: 8                │  │
│  │ [2026-01-16 10:25:33] [INFO] Health check: OK         │  │
│  │ ...                                                    │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
│  [⏸ Stop] [🔄 Restart] [🗑 Delete] [📥 Download Logs]      │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 🛠️ **Technology Stack**

### **Frontend (UI)**
- Framework: Vite + React 18+ (TypeScript)
- Styling: Tailwind CSS
- UI Components: shadcn/ui
- Charts: Recharts
- Real-time: Socket.io Client
- HTTP Client: Axios

### **Backend (Orchestrator)**
- Runtime: Node.js + Express (TypeScript)
- Container Runtime: Dockerode (Docker SDK)
- Real-time: Socket.io Server
- Database: Supabase (PostgreSQL)
- Auth: CoreSense IAM
- Logging: Supabase

### **Container Runtime**
- Development: Docker Compose
- Production: K3s (Kubernetes light)
- Platform: linux/amd64, linux/arm64

---

## 📦 **Project Structure**

```
platform/agentify/hosting/
├── ui/                          # React frontend
│   ├── src/
│   │   ├── pages/
│   │   │   ├── Dashboard.tsx
│   │   │   └── ContainerDetails.tsx
│   │   ├── components/
│   │   │   ├── ContainerList.tsx
│   │   │   ├── ResourceChart.tsx
│   │   │   └── LogViewer.tsx
│   │   ├── services/
│   │   │   └── hosting.ts
│   │   └── main.tsx
│   └── package.json
├── orchestrator/                # Hosting Orchestrator
│   ├── src/
│   │   ├── index.ts
│   │   ├── container-manager.ts
│   │   ├── health-monitor.ts
│   │   ├── auto-scaler.ts
│   │   └── agent-protocol.ts
│   ├── manifest.json
│   └── package.json
├── docker-compose.yml
└── README.md
```

---

## 🚀 **Next Steps**

1. ✅ Implement Hosting Orchestrator
2. ✅ Implement Hosting UI
3. ✅ Implement Container Manager
4. ✅ Implement Health Monitor
5. ✅ Implement Auto-Scaler
6. ✅ Test with Calculator PoC agents
7. ✅ Deploy to Railway
8. ✅ Integrate with Marketplace

---

**Status:** 🚧 Ready to implement
**Version:** 1.0.0
**Date:** 2026-01-16


