# 🏗️ Agentify Platform - Architecture

**Detailed architecture of the Agentify platform layer**

---

## 📊 **System Overview**

Agentify is a **multi-layer platform** built on top of Agent Standard v1:

```
┌─────────────────────────────────────────────────────────────┐
│                    Layer 3: Applications                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  App 1       │  │  App 2       │  │  App N       │      │
│  │  (React)     │  │  (React)     │  │  (React)     │      │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      │
│         │                 │                  │              │
├─────────┼─────────────────┼──────────────────┼──────────────┤
│         │                 │                  │              │
│  Layer 2: Platform Services                                 │
│         │                 │                  │              │
│  ┌──────▼─────────────────▼──────────────────▼──────┐      │
│  │           Orchestrator Agents                     │      │
│  │  (One per app - Team Building & Management)       │      │
│  └──────┬────────────────────────────────────────────┘      │
│         │                                                    │
│  ┌──────▼────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │  Discovery    │  │  Data        │  │  Billing     │    │
│  │  Service      │  │  Sharing     │  │  Service     │    │
│  └──────┬────────┘  └──────┬───────┘  └──────┬───────┘    │
│         │                  │                  │            │
├─────────┼──────────────────┼──────────────────┼────────────┤
│         │                  │                  │            │
│  Layer 1: Agent Standard v1 (Foundation)                   │
│         │                  │                  │            │
│  ┌──────▼──────────────────▼──────────────────▼──────┐    │
│  │  Ethics │ Desires │ Tools │ Memory │ Authority    │    │
│  └──────────────────────────────────────────────────────┘  │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

---

## 🎯 **Core Components**

### **1. App Standard**

Every Agentify app is a **React application** with:

#### **Technology Stack:**
- **Framework**: Vite + React
- **Styling**: Tailwind CSS
- **State Management**: Zustand
- **Routing**: React Router
- **API Client**: Axios / Fetch

#### **App Architecture Layers:**

```
┌─────────────────────────────────────────────────────────┐
│                    Presentation Layer                    │
│              (React Components + UI)                     │
├─────────────────────────────────────────────────────────┤
│                   Orchestrator Agent                     │
│         (Team Building, Task Distribution)               │
├─────────────────────────────────────────────────────────┤
│                    Data Access Layer                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │ Own Database │  │ Data Agent   │  │ Data Service │  │
│  │ (Supabase)   │  │ (Delegated)  │  │ (External)   │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
├─────────────────────────────────────────────────────────┤
│                    Logging Layer                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │ Local Logs   │  │ Log Agent    │  │ Log Service  │  │
│  │ (Console)    │  │ (Delegated)  │  │ (Supabase)   │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
└─────────────────────────────────────────────────────────┘
```

#### **App Modes:**

**Standalone Mode:**
```
┌─────────────────────────────────────┐
│           App Header                │
├─────────────────────────────────────┤
│                                     │
│         Main Content Area           │
│                                     │
│                                     │
└─────────────────────────────────────┘
```

**Integrated Mode:**
```
┌──────────┬──────────────────────────┐
│          │     App Header           │
│          ├──────────────────────────┤
│ Sidebar  │                          │
│ (Left)   │   Main Content Area      │
│          │                          │
│          │                          │
└──────────┴──────────────────────────┘
```

#### **Built-in Orchestrator:**
Every app includes an orchestrator agent that:
- Manages the app's agent team
- Communicates with the marketplace
- Handles data sharing requests
- Monitors team health
- **Coordinates data access strategy**
- **Manages logging strategy**

---

### **2. Data Access Layer (DAL)**

Every app must decide on a **data persistence strategy**:

#### **Strategy 1: Own Database (Recommended for Lovable)**

**Use Case:** App needs full control over data schema and queries

**Default Stack:**
- **Database**: Supabase (PostgreSQL)
- **ORM**: Supabase Client
- **Auth**: Supabase Auth
- **Storage**: Supabase Storage

**Implementation:**
```typescript
// src/services/database.ts
import { createClient } from '@supabase/supabase-js';

const supabase = createClient(
  process.env.VITE_SUPABASE_URL!,
  process.env.VITE_SUPABASE_ANON_KEY!
);

export const db = {
  async getUsers() {
    const { data, error } = await supabase.from('users').select('*');
    if (error) throw error;
    return data;
  },
  // ... more methods
};
```

**Pros:**
- ✅ Full control over schema
- ✅ Fast queries (no network overhead)
- ✅ Built-in auth & storage
- ✅ Real-time subscriptions

**Cons:**
- ❌ App-specific data (not shared)
- ❌ Requires database management

---

#### **Strategy 2: Data Agent (Delegated)**

**Use Case:** App wants to delegate data management to a specialized agent

**Implementation:**
```typescript
// src/services/dataAgent.ts
import { orchestrator } from './orchestrator';

export const dataAgent = {
  async getUsers() {
    const agent = await orchestrator.findAgent({ capability: 'data_storage' });
    const result = await agent.execute({
      action: 'query',
      params: { table: 'users', operation: 'select' }
    });
    return result.data;
  },
  // ... more methods
};
```

**Pros:**
- ✅ Centralized data management
- ✅ Data sharing across apps
- ✅ No database setup needed

**Cons:**
- ❌ Network latency
- ❌ Depends on agent availability

---

#### **Strategy 3: External Data Service**

**Use Case:** App integrates with existing enterprise data services

**Implementation:**
```typescript
// src/services/dataService.ts
import axios from 'axios';

const api = axios.create({
  baseURL: process.env.VITE_DATA_SERVICE_URL,
  headers: { 'Authorization': `Bearer ${process.env.VITE_API_KEY}` }
});

export const dataService = {
  async getUsers() {
    const { data } = await api.get('/users');
    return data;
  },
  // ... more methods
};
```

**Pros:**
- ✅ Enterprise integration
- ✅ Existing data governance
- ✅ Compliance & security

**Cons:**
- ❌ External dependency
- ❌ Requires API credentials

---

### **3. Logging Strategy**

Every app must decide on a **logging strategy**:

#### **Strategy 1: Local Logging (Development)**

**Use Case:** Development and debugging

**Implementation:**
```typescript
// src/services/logger.ts
export const logger = {
  info: (message: string, meta?: any) => console.log('[INFO]', message, meta),
  error: (message: string, meta?: any) => console.error('[ERROR]', message, meta),
  warn: (message: string, meta?: any) => console.warn('[WARN]', message, meta),
};
```

**Pros:**
- ✅ Simple & fast
- ✅ No setup needed

**Cons:**
- ❌ Not persistent
- ❌ No centralized monitoring

---

#### **Strategy 2: Logging Service (Recommended for Production)**

**Use Case:** Production apps with monitoring requirements

**Default Stack:**
- **Service**: Supabase (logs table) or Sentry
- **Format**: Structured JSON logs
- **Retention**: Configurable

**Implementation:**
```typescript
// src/services/logger.ts
import { createClient } from '@supabase/supabase-js';

const supabase = createClient(
  process.env.VITE_SUPABASE_URL!,
  process.env.VITE_SUPABASE_ANON_KEY!
);

export const logger = {
  async info(message: string, meta?: any) {
    await supabase.from('logs').insert({
      level: 'info',
      message,
      meta,
      timestamp: new Date().toISOString(),
      app_id: 'app.company.myapp',
    });
    console.log('[INFO]', message, meta);
  },
  // ... more methods
};
```

**Pros:**
- ✅ Persistent logs
- ✅ Centralized monitoring
- ✅ Query & analytics

**Cons:**
- ❌ Requires setup
- ❌ Storage costs

---

#### **Strategy 3: Logging Agent (Delegated)**

**Use Case:** App delegates logging to a specialized agent

**Implementation:**
```typescript
// src/services/logger.ts
import { orchestrator } from './orchestrator';

export const logger = {
  async info(message: string, meta?: any) {
    const agent = await orchestrator.findAgent({ capability: 'logging' });
    await agent.execute({
      action: 'log',
      params: { level: 'info', message, meta }
    });
    console.log('[INFO]', message, meta);
  },
  // ... more methods
};
```

**Pros:**
- ✅ Centralized logging
- ✅ No setup needed
- ✅ Agent handles retention

**Cons:**
- ❌ Network latency
- ❌ Depends on agent availability

---

### **4. Orchestrator Agent**

The orchestrator is an **Agent Standard v1 compliant agent** with additional capabilities:

#### **Core Responsibilities:**

1. **Requirement Analysis**
   - Parse user/app requirements
   - Identify needed capabilities
   - Determine budget constraints

2. **Team Discovery**
   - Query marketplace for agents
   - Filter by capability, price, rating
   - Get LLM recommendations

3. **Team Building**
   - Select agents for team
   - Present options to user (Human-in-the-Loop)
   - Book agents via marketplace

4. **Team Management**
   - Monitor team health
   - Scale team (add/remove agents)
   - Handle agent failures

5. **Communication**
   - Route tasks to team members
   - Aggregate results
   - Log all activities (Agent Standard)

6. **Data Access Coordination**
   - Determine data access strategy (own DB vs. agent vs. service)
   - Configure data layer based on app requirements
   - Manage data agent discovery if delegated
   - Handle data sharing requests

7. **Logging Coordination**
   - Determine logging strategy (local vs. service vs. agent)
   - Configure logging layer
   - Manage log agent discovery if delegated
   - Ensure compliance with logging requirements

#### **Orchestrator Manifest:**

```json
{
  "agent_id": "agent.myapp.orchestrator",
  "name": "MyApp Orchestrator",
  "version": "1.0.0",
  "status": "active",
  "ethics": {
    "framework": "harm-minimization",
    "hard_constraints": [
      "no_unauthorized_team_changes",
      "no_budget_overrun"
    ]
  },
  "desires": {
    "profile": [
      {"id": "team_efficiency", "weight": 0.4},
      {"id": "cost_optimization", "weight": 0.3},
      {"id": "user_satisfaction", "weight": 0.3}
    ]
  },
  "tools": [
    {
      "name": "query_marketplace",
      "description": "Query marketplace for agents",
      "category": "discovery"
    },
    {
      "name": "build_team",
      "description": "Build team from selected agents",
      "category": "orchestration"
    },
    {
      "name": "monitor_team",
      "description": "Monitor team health and performance",
      "category": "monitoring"
    },
    {
      "name": "configure_data_layer",
      "description": "Configure data access strategy (own DB, agent, or service)",
      "category": "data"
    },
    {
      "name": "discover_data_agent",
      "description": "Find and connect to data storage agent",
      "category": "data"
    },
    {
      "name": "configure_logging",
      "description": "Configure logging strategy (local, service, or agent)",
      "category": "logging"
    },
    {
      "name": "discover_logging_agent",
      "description": "Find and connect to logging agent",
      "category": "logging"
    }
  ]
}
```

---

### **3. Discovery Service**

The Discovery Service enables agents to find each other:

#### **Registration:**

Agents register with the Discovery Service:

```json
{
  "agent_id": "agent.company.email-sender",
  "name": "Email Sender",
  "capabilities": ["email_sending", "smtp"],
  "pricing": {
    "model": "usage-based",
    "rate": 0.01
  },
  "rating": 8.5,
  "creator": {
    "name": "Acme Corp",
    "id": "creator-123"
  },
  "repository": "https://github.com/acme/email-sender",
  "manifest_url": "https://github.com/acme/email-sender/manifest.json"
}
```

#### **Discovery API:**

```typescript
// Query agents by capability
GET /api/discovery/agents?capability=email_sending

// Get agent details
GET /api/discovery/agents/{agent_id}

// Register agent
POST /api/discovery/agents
```

#### **GitHub Integration:**

Agents can auto-register from GitHub:

```yaml
# .github/agentify.yml
agent:
  auto_register: true
  marketplace: "https://marketplace.agentify.io"
  manifest: "manifest.json"
```

---

### **4. Marketplace**

The Marketplace is a **system default app** with its own orchestrator:

#### **Marketplace Orchestrator Responsibilities:**

1. **Agent Discovery**
   - Maintain agent registry
   - Search and filter agents
   - Recommend agents based on requirements

2. **Team Matching**
   - Analyze requirements
   - Suggest agent combinations
   - Optimize for cost and capability

3. **Billing & Revenue Sharing**
   - Track agent usage
   - Calculate costs
   - Distribute revenue to creators

4. **Trust & Ratings**
   - Collect user ratings
   - Verify agent creators
   - Monitor agent health

#### **Marketplace API:**

```typescript
// Search agents
POST /api/marketplace/search
{
  "requirements": {
    "capabilities": ["email_sending", "scheduling"],
    "max_price_per_action": 0.05,
    "min_rating": 7.0
  }
}

// Book agent for team
POST /api/marketplace/book
{
  "agent_id": "agent.company.email-sender",
  "team_id": "team-123",
  "duration": "30d"
}

// Submit rating
POST /api/marketplace/rate
{
  "agent_id": "agent.company.email-sender",
  "rating": 9,
  "review": "Excellent email agent!"
}
```

---

### **5. Data Sharing Protocol**

Enables secure cross-app data access:

#### **Technology:**
- **Protocol**: REST + JSON
- **Authentication**: OAuth 2.0 / API Keys
- **Permissions**: RBAC (Role-Based Access Control)
- **Storage**: Configurable (Cloud/Edge/Local)

#### **Data Sharing Flow:**

```
App A (Data Owner)
    │
    │ 1. Grant access to App B
    ▼
Data Sharing Service
    │
    │ 2. Verify permissions (RBAC)
    ▼
App B (Data Consumer)
    │
    │ 3. Access data via API
    ▼
Audit Log (All access logged)
```

#### **API:**

```typescript
// Grant access
POST /api/data-sharing/grant
{
  "app_id": "app.myapp",
  "target_app_id": "app.otherapp",
  "resource": "users",
  "permissions": ["read"]
}

// Access data
GET /api/data-sharing/data/{app_id}/{resource}
Headers: Authorization: Bearer <token>

// Revoke access
DELETE /api/data-sharing/grant/{grant_id}
```

---

## 🔄 **Data Flow**

### **Team Building Flow:**

```
1. User Request
   │
   ▼
2. App Orchestrator
   │ Analyze requirements
   ▼
3. Query Marketplace
   │ Search agents
   ▼
4. Marketplace Orchestrator
   │ Recommend agents (LLM-guided)
   ▼
5. Human-in-the-Loop Review
   │ User approves team
   ▼
6. Book Agents
   │ Marketplace books agents
   ▼
7. Team Active
   │ Orchestrator manages team
   ▼
8. Billing
   │ Automatic revenue sharing
```

---

## 📊 **Deployment Architecture**

### **Cloud Deployment (Default):**

```
┌─────────────────────────────────────────┐
│         Cloud Infrastructure            │
├─────────────────────────────────────────┤
│                                         │
│  ┌──────────┐  ┌──────────┐           │
│  │  Apps    │  │Marketplace│           │
│  │ (Vercel) │  │ (Railway) │           │
│  └────┬─────┘  └────┬──────┘           │
│       │             │                   │
│  ┌────▼─────────────▼──────┐           │
│  │  Discovery Service      │           │
│  │  (Railway)              │           │
│  └────┬────────────────────┘           │
│       │                                │
│  ┌────▼────────────────────┐           │
│  │  Data Sharing Service   │           │
│  │  (Railway)              │           │
│  └─────────────────────────┘           │
│                                         │
└─────────────────────────────────────────┘
```

### **Private Deployment:**

Organizations can deploy private instances:
- Private marketplace
- Private discovery service
- On-premise or private cloud

---

## 🔒 **Security**

### **1. Agent Authentication**
- API keys for agent-to-service communication
- OAuth 2.0 for user authentication
- JWT tokens for session management

### **2. Data Encryption**
- TLS 1.3 for all communication
- Encryption at rest (configurable)
- End-to-end encryption for sensitive data

### **3. Access Control**
- RBAC for data sharing
- Agent-level permissions
- Audit trail for all actions

### **4. Ethics Enforcement**
- All agents must be Agent Standard v1 compliant
- Ethics violations logged and escalated
- Automatic team suspension on critical violations

---

## 📈 **Scalability**

### **Horizontal Scaling:**
- Apps: Scale independently
- Discovery Service: Stateless, scale horizontally
- Marketplace: Database sharding
- Data Sharing: CDN + caching

### **Performance:**
- Agent discovery: < 100ms
- Team building: < 5s (including LLM)
- Data sharing: < 50ms (cached)

---

**Next:** [QUICKSTART.md](QUICKSTART.md) - Build your first Agentify app!

