# 📱 Agentify App Standard v1

**Specification for building Agentify-compliant applications**

---

## 🎯 **What is an Agentify App?**

An Agentify App is a **React-based application** with:
- ✅ Built-in **orchestrator agent**
- ✅ **Vite + Tailwind + Zustand** stack
- ✅ Two modes: **Standalone** & **Integrated**
- ✅ **Data sharing** capabilities
- ✅ **Marketplace integration**
- ✅ **Agent Standard v1** compliance

---

## 🏗️ **Technology Stack**

### **Required:**
- **Framework**: Vite + React 18+
- **Styling**: Tailwind CSS
- **State Management**: Zustand
- **Routing**: React Router v6+
- **API Client**: Axios or Fetch API

### **Recommended:**
- **UI Components**: shadcn/ui (Tailwind-based)
- **Forms**: React Hook Form + Zod
- **Icons**: Lucide React
- **Date/Time**: date-fns
- **HTTP**: Axios

---

## 📦 **App Structure**

```
my-agentify-app/
├── public/
│   └── agentify.json              # App manifest
├── src/
│   ├── agents/
│   │   └── orchestrator/
│   │       ├── manifest.json      # Orchestrator manifest
│   │       ├── orchestrator.ts    # Orchestrator implementation
│   │       └── tools/             # Orchestrator tools
│   ├── components/
│   │   ├── layout/
│   │   │   ├── Standalone.tsx     # Standalone layout
│   │   │   └── Integrated.tsx     # Integrated layout
│   │   └── ui/                    # UI components
│   ├── stores/
│   │   ├── appStore.ts            # App state (Zustand)
│   │   └── agentStore.ts          # Agent team state
│   ├── services/
│   │   ├── marketplace.ts         # Marketplace API client
│   │   ├── dataSharing.ts         # Data sharing API client
│   │   └── orchestrator.ts        # Orchestrator service
│   ├── App.tsx
│   ├── main.tsx
│   └── index.css
├── package.json
├── vite.config.ts
├── tailwind.config.js
└── tsconfig.json
```

---

## 📄 **App Manifest**

Every app must have an `agentify.json` manifest:

```json
{
  "app_id": "app.company.myapp",
  "name": "My Agentify App",
  "version": "1.0.0",
  "description": "A sample Agentify app",
  "author": {
    "name": "Acme Corp",
    "email": "dev@acme.com"
  },
  "orchestrator": {
    "manifest_path": "/src/agents/orchestrator/manifest.json",
    "enabled": true
  },
  "modes": {
    "standalone": true,
    "integrated": true
  },
  "data_sharing": {
    "enabled": true,
    "resources": [
      {
        "name": "users",
        "permissions": ["read", "write"]
      }
    ]
  },
  "marketplace": {
    "url": "https://marketplace.agentify.io",
    "auto_register": true
  },
  "storage": {
    "default": "cloud",
    "options": ["cloud", "edge", "local"],
    "configurable": true
  }
}
```

---

## 🤖 **Built-in Orchestrator**

Every app includes an orchestrator agent:

### **Orchestrator Manifest** (`src/agents/orchestrator/manifest.json`):

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
      {"id": "cost_optimization", "weight": 0.3}
    ]
  },
  "tools": [
    {
      "name": "query_marketplace",
      "description": "Query marketplace for agents",
      "category": "discovery",
      "executor": "agents.orchestrator.tools.MarketplaceQuery"
    },
    {
      "name": "build_team",
      "description": "Build team from agents",
      "category": "orchestration",
      "executor": "agents.orchestrator.tools.TeamBuilder"
    }
  ],
  "authority": {
    "instruction": {"type": "app", "id": "app.myapp"},
    "oversight": {"type": "human", "id": "user", "independent": true}
  }
}
```

### **Orchestrator Implementation** (`src/agents/orchestrator/orchestrator.ts`):

```typescript
import { Agent } from '@agentify/agent-standard';
import { agent_tool } from '@agentify/agent-standard/decorators';

export class MyAppOrchestrator extends Agent {
  @agent_tool({
    ethics: ['no_unauthorized_team_changes'],
    desires: ['team_efficiency']
  })
  async queryMarketplace(requirements: {
    capabilities: string[];
    maxPrice?: number;
    minRating?: number;
  }): Promise<Agent[]> {
    // Query marketplace for agents
    const response = await fetch('https://marketplace.agentify.io/api/search', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ requirements })
    });
    return response.json();
  }

  @agent_tool({
    ethics: ['no_budget_overrun'],
    desires: ['cost_optimization']
  })
  async buildTeam(agents: Agent[]): Promise<Team> {
    // Build team from selected agents
    // Human-in-the-loop review
    const approved = await this.requestHumanApproval(agents);
    if (!approved) {
      throw new Error('Team building cancelled by user');
    }
    
    // Book agents via marketplace
    const team = await this.bookAgents(agents);
    return team;
  }
}
```

---

## 🎨 **App Modes**

### **1. Standalone Mode**

Full-screen app with no external integration:

```tsx
// src/components/layout/Standalone.tsx
import { Outlet } from 'react-router-dom';

export function StandaloneLayout() {
  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 py-6">
          <h1 className="text-3xl font-bold">My Agentify App</h1>
        </div>
      </header>
      <main className="max-w-7xl mx-auto px-4 py-6">
        <Outlet />
      </main>
    </div>
  );
}
```

### **2. Integrated Mode**

Sidebar (left) + Main content (right):

```tsx
// src/components/layout/Integrated.tsx
import { Outlet } from 'react-router-dom';
import { Sidebar } from './Sidebar';

export function IntegratedLayout() {
  return (
    <div className="flex min-h-screen">
      {/* Sidebar (left) */}
      <aside className="w-64 bg-gray-900 text-white">
        <Sidebar />
      </aside>
      
      {/* Main content (right) */}
      <main className="flex-1 bg-gray-50">
        <header className="bg-white shadow px-6 py-4">
          <h1 className="text-2xl font-bold">My Agentify App</h1>
        </header>
        <div className="p-6">
          <Outlet />
        </div>
      </main>
    </div>
  );
}
```

---

## 🗄️ **State Management (Zustand)**

### **App Store** (`src/stores/appStore.ts`):

```typescript
import { create } from 'zustand';

interface AppState {
  mode: 'standalone' | 'integrated';
  user: User | null;
  setMode: (mode: 'standalone' | 'integrated') => void;
  setUser: (user: User | null) => void;
}

export const useAppStore = create<AppState>((set) => ({
  mode: 'standalone',
  user: null,
  setMode: (mode) => set({ mode }),
  setUser: (user) => set({ user }),
}));
```

### **Agent Store** (`src/stores/agentStore.ts`):

```typescript
import { create } from 'zustand';

interface AgentState {
  team: Agent[];
  orchestrator: Orchestrator | null;
  addAgent: (agent: Agent) => void;
  removeAgent: (agentId: string) => void;
  setOrchestrator: (orchestrator: Orchestrator) => void;
}

export const useAgentStore = create<AgentState>((set) => ({
  team: [],
  orchestrator: null,
  addAgent: (agent) => set((state) => ({ team: [...state.team, agent] })),
  removeAgent: (agentId) => set((state) => ({
    team: state.team.filter((a) => a.agent_id !== agentId)
  })),
  setOrchestrator: (orchestrator) => set({ orchestrator }),
}));
```

---

## 🔌 **Marketplace Integration**

### **Marketplace Service** (`src/services/marketplace.ts`):

```typescript
import axios from 'axios';

const MARKETPLACE_URL = 'https://marketplace.agentify.io/api';

export class MarketplaceService {
  async searchAgents(requirements: {
    capabilities: string[];
    maxPrice?: number;
    minRating?: number;
  }): Promise<Agent[]> {
    const response = await axios.post(`${MARKETPLACE_URL}/search`, {
      requirements
    });
    return response.data;
  }

  async bookAgent(agentId: string, teamId: string): Promise<void> {
    await axios.post(`${MARKETPLACE_URL}/book`, {
      agent_id: agentId,
      team_id: teamId
    });
  }

  async rateAgent(agentId: string, rating: number, review?: string): Promise<void> {
    await axios.post(`${MARKETPLACE_URL}/rate`, {
      agent_id: agentId,
      rating,
      review
    });
  }
}
```

---

## 🔄 **Data Sharing**

### **Data Sharing Service** (`src/services/dataSharing.ts`):

```typescript
import axios from 'axios';

const DATA_SHARING_URL = 'https://data-sharing.agentify.io/api';

export class DataSharingService {
  async grantAccess(
    targetAppId: string,
    resource: string,
    permissions: string[]
  ): Promise<void> {
    await axios.post(`${DATA_SHARING_URL}/grant`, {
      app_id: 'app.myapp',
      target_app_id: targetAppId,
      resource,
      permissions
    });
  }

  async accessData(appId: string, resource: string): Promise<any> {
    const response = await axios.get(
      `${DATA_SHARING_URL}/data/${appId}/${resource}`
    );
    return response.data;
  }

  async revokeAccess(grantId: string): Promise<void> {
    await axios.delete(`${DATA_SHARING_URL}/grant/${grantId}`);
  }
}
```

---

## 💾 **Configurable Storage**

Apps can support multiple storage backends:

```typescript
// src/services/storage.ts
export interface StorageBackend {
  save(key: string, value: any): Promise<void>;
  load(key: string): Promise<any>;
  delete(key: string): Promise<void>;
}

export class CloudStorage implements StorageBackend {
  async save(key: string, value: any): Promise<void> {
    // Save to cloud (e.g., Supabase, Firebase)
  }
}

export class EdgeStorage implements StorageBackend {
  async save(key: string, value: any): Promise<void> {
    // Save to edge (e.g., Cloudflare KV)
  }
}

export class LocalStorage implements StorageBackend {
  async save(key: string, value: any): Promise<void> {
    // Save to local storage
    localStorage.setItem(key, JSON.stringify(value));
  }
}
```

**Note:** Developers must implement storage backends. The App Standard provides the interface.

---

**Next:** [template/](template/) - React template for quick start  
**See also:** [prompts/](prompts/) - AI prompts for app generation

