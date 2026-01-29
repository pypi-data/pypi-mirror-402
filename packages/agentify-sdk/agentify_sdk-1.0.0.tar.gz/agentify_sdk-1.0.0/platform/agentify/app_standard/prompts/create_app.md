# 🚀 Create Agentify App - AI Prompt

**Use this prompt with Lovable, Cursor, Copilot, Augment, v0, or Bolt to generate a complete Agentify app**

---

## 📋 **Complete Prompt**

Copy and paste this prompt into your AI tool:

```
Create a complete Agentify-compliant React application with the following specifications:

## App Details
- App Name: {APP_NAME}
- Description: {APP_DESCRIPTION}
- Required Agent Capabilities: {CAPABILITIES}

## Technology Stack
- Framework: Vite + React 18+ (TypeScript)
- Styling: Tailwind CSS
- State Management: Zustand
- Routing: React Router v6
- UI Components: shadcn/ui (Tailwind-based)
- Icons: Lucide React
- HTTP Client: Axios

## Architecture Layers

### 1. Presentation Layer
- React components with shadcn/ui
- Responsive design (mobile-first)
- Two modes: Standalone & Integrated
- Dark mode support

### 2. Orchestrator Agent
Every app MUST include a built-in orchestrator agent that:
- Manages the app's agent team
- Discovers and books agents from marketplace
- Handles data access coordination
- Manages logging strategy
- Monitors team health

Create the orchestrator at: `src/agents/orchestrator/`

### 3. Data Access Layer (DAL)

Choose ONE of the following strategies:

**Option A: Own Database (Recommended for Lovable)**
- Use Supabase as the database
- Create Supabase client in `src/services/database.ts`
- Implement CRUD operations
- Use Supabase Auth for authentication
- Use Supabase Storage for file uploads

Environment variables needed:
```env
VITE_SUPABASE_URL=your-supabase-url
VITE_SUPABASE_ANON_KEY=your-supabase-anon-key
```

**Option B: Data Agent (Delegated)**
- Orchestrator discovers a data storage agent
- All data operations delegated to the agent
- Implement in `src/services/dataAgent.ts`

**Option C: External Data Service**
- Connect to existing enterprise API
- Implement in `src/services/dataService.ts`

**Default: Use Option A (Supabase) unless specified otherwise**

### 4. Logging Strategy

Choose ONE of the following strategies:

**Option A: Logging Service (Recommended for Production)**
- Use Supabase for persistent logs
- Create logs table in Supabase
- Implement structured logging in `src/services/logger.ts`
- Log levels: info, warn, error, debug

**Option B: Logging Agent (Delegated)**
- Orchestrator discovers a logging agent
- All logs sent to the agent
- Implement in `src/services/logger.ts`

**Option C: Local Logging (Development Only)**
- Console.log only
- Not recommended for production

**Default: Use Option A (Supabase) unless specified otherwise**

## Project Structure
```
my-app/
├── public/
│   └── agentify.json              # App manifest
├── src/
│   ├── agents/
│   │   └── orchestrator/
│   │       ├── manifest.json      # Orchestrator manifest (Agent Standard v1)
│   │       ├── orchestrator.ts    # Orchestrator implementation
│   │       └── tools/             # Orchestrator tools
│   │           ├── MarketplaceQuery.ts
│   │           ├── TeamBuilder.ts
│   │           ├── DataLayerConfig.ts    # Data layer configuration
│   │           └── LoggingConfig.ts      # Logging configuration
│   ├── components/
│   │   ├── layout/
│   │   │   ├── Standalone.tsx     # Standalone layout
│   │   │   ├── Integrated.tsx     # Integrated layout (sidebar + main)
│   │   │   └── Sidebar.tsx        # Sidebar component
│   │   ├── team/
│   │   │   ├── TeamBuilder.tsx    # Team building UI
│   │   │   ├── AgentCard.tsx      # Agent display card
│   │   │   └── TeamList.tsx       # Current team list
│   │   └── ui/                    # shadcn/ui components
│   ├── stores/
│   │   ├── appStore.ts            # App state (Zustand)
│   │   ├── agentStore.ts          # Agent team state (Zustand)
│   │   └── configStore.ts         # Configuration state (DAL, Logging)
│   ├── services/
│   │   ├── marketplace.ts         # Marketplace API client
│   │   ├── dataSharing.ts         # Data sharing API client
│   │   ├── orchestrator.ts        # Orchestrator service
│   │   ├── database.ts            # Database service (Supabase)
│   │   ├── dataAgent.ts           # Data agent service (if delegated)
│   │   ├── dataService.ts         # External data service (if external)
│   │   ├── logger.ts              # Logging service
│   │   └── storage.ts             # Storage abstraction
│   ├── types/
│   │   ├── agent.ts               # Agent types
│   │   ├── app.ts                 # App types
│   │   ├── team.ts                # Team types
│   │   └── config.ts              # Configuration types
│   ├── App.tsx
│   ├── main.tsx
│   └── index.css
├── .env.example                   # Environment variables template
├── package.json
├── vite.config.ts
├── tailwind.config.js
└── tsconfig.json
```

## Required Files

### 1. App Manifest (public/agentify.json)
```json
{
  "app_id": "app.company.{APP_ID}",
  "name": "{APP_NAME}",
  "version": "1.0.0",
  "description": "{APP_DESCRIPTION}",
  "author": {
    "name": "Your Company",
    "email": "dev@company.com"
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
    "resources": []
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

### 2. Orchestrator Manifest (src/agents/orchestrator/manifest.json)
```json
{
  "agent_id": "agent.{APP_ID}.orchestrator",
  "name": "{APP_NAME} Orchestrator",
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
      "description": "Build team from agents",
      "category": "orchestration"
    }
  ],
  "authority": {
    "instruction": {"type": "app", "id": "app.{APP_ID}"},
    "oversight": {"type": "human", "id": "user", "independent": true}
  }
}
```

### 3. App Store (src/stores/appStore.ts)
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

### 4. Agent Store (src/stores/agentStore.ts)
```typescript
import { create } from 'zustand';
import { Agent, Team } from '../types/agent';

interface AgentState {
  team: Agent[];
  orchestrator: any | null;
  addAgent: (agent: Agent) => void;
  removeAgent: (agentId: string) => void;
  setOrchestrator: (orchestrator: any) => void;
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

### 5. Marketplace Service (src/services/marketplace.ts)
```typescript
import axios from 'axios';
import { Agent } from '../types/agent';

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
}

export const marketplaceService = new MarketplaceService();
```

### 6. Layouts

**Standalone Layout (src/components/layout/Standalone.tsx):**
```typescript
import { Outlet } from 'react-router-dom';

export function StandaloneLayout() {
  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 py-6">
          <h1 className="text-3xl font-bold">{APP_NAME}</h1>
        </div>
      </header>
      <main className="max-w-7xl mx-auto px-4 py-6">
        <Outlet />
      </main>
    </div>
  );
}
```

**Integrated Layout (src/components/layout/Integrated.tsx):**
```typescript
import { Outlet } from 'react-router-dom';
import { Sidebar } from './Sidebar';

export function IntegratedLayout() {
  return (
    <div className="flex min-h-screen">
      <aside className="w-64 bg-gray-900 text-white">
        <Sidebar />
      </aside>
      <main className="flex-1 bg-gray-50">
        <header className="bg-white shadow px-6 py-4">
          <h1 className="text-2xl font-bold">{APP_NAME}</h1>
        </header>
        <div className="p-6">
          <Outlet />
        </div>
      </main>
    </div>
  );
}
```

## Features to Implement

1. **Team Building UI**
   - Search agents by capability
   - Display agent cards (name, rating, price)
   - Human-in-the-loop approval before booking
   - Current team display

2. **Mode Switcher**
   - Toggle between standalone and integrated modes
   - Persist mode preference

3. **Orchestrator Integration**
   - Initialize orchestrator on app load
   - Query marketplace via orchestrator
   - Build teams via orchestrator
   - Configure data layer strategy
   - Configure logging strategy

4. **Responsive Design**
   - Mobile-friendly
   - Tailwind CSS utilities
   - Dark mode support (optional)

## Configuration & Defaults

### **Auto-Configuration (Recommended)**

The orchestrator should automatically configure the app on first run:

1. **Data Layer Auto-Config:**
   - Detect if Supabase credentials are present
   - If yes: Use Supabase database (Option A)
   - If no: Ask user to choose (Agent or External Service)
   - Store choice in localStorage

2. **Logging Auto-Config:**
   - Detect if Supabase credentials are present
   - If yes: Use Supabase logging (Option A)
   - If no: Use local logging (Option C)
   - Store choice in localStorage

3. **Environment Detection:**
   - Development: Use local logging by default
   - Production: Use Supabase logging by default

### **Developer Interaction (Human-in-the-Loop)**

When auto-config cannot determine the best strategy, prompt the developer:

```typescript
// Example: Data Layer Configuration Dialog
const configureDataLayer = async () => {
  const choice = await showDialog({
    title: 'Configure Data Layer',
    message: 'How should this app store data?',
    options: [
      { value: 'database', label: 'Own Database (Supabase)', recommended: true },
      { value: 'agent', label: 'Data Agent (Delegated)' },
      { value: 'service', label: 'External Service' },
    ],
  });

  await orchestrator.configureDataLayer(choice);
};
```

### **Default Stack (Lovable Apps)**

For apps built with Lovable, use these defaults:

- **Database**: Supabase (PostgreSQL)
- **Auth**: Supabase Auth
- **Storage**: Supabase Storage
- **Logging**: Supabase (logs table)
- **Real-time**: Supabase Realtime
- **Deployment**: Lovable hosting

### **Environment Variables Template (.env.example)**

```env
# App Configuration
VITE_APP_ID=app.company.myapp
VITE_APP_NAME=My Agentify App

# Supabase (Recommended)
VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_ANON_KEY=your-anon-key

# Marketplace
VITE_MARKETPLACE_URL=https://marketplace.agentify.dev
VITE_MARKETPLACE_API_KEY=your-api-key

# Data Layer Strategy (database | agent | service)
VITE_DATA_LAYER_STRATEGY=database

# Logging Strategy (local | service | agent)
VITE_LOGGING_STRATEGY=service

# External Data Service (if using)
VITE_DATA_SERVICE_URL=https://api.company.com
VITE_DATA_SERVICE_API_KEY=your-api-key
```

## Additional Requirements

- Use TypeScript for all files
- Include proper error handling
- Add loading states for async operations
- Include basic form validation
- Follow Agentify App Standard v1 specification
- Ensure all components are accessible (ARIA labels)
- **Implement auto-configuration for data layer and logging**
- **Include developer prompts for manual configuration**
- **Use Supabase as default for Lovable apps**

## Expected Output

Generate a complete, working Agentify app with:
- All files in the project structure
- Working orchestrator integration
- Team building UI
- Both standalone and integrated layouts
- Proper TypeScript types
- Tailwind CSS styling
- Zustand state management
- **Auto-configuration for data layer and logging**
- **Supabase integration (if credentials provided)**
- **Developer configuration dialogs (if needed)**

The app should be ready to run with `npm install && npm run dev`.

## Implementation Examples

For detailed implementation examples, see:
- `platform/agentify/app_standard/prompts/implementation_examples.md`
- Data Layer: Supabase, Data Agent, External Service
- Logging: Supabase, Logging Agent, Local
- Orchestrator: Team building, configuration
```

---

## 🎯 **Customization**

Replace these placeholders:

- `{APP_NAME}` - Your app name (e.g., "Email Manager")
- `{APP_DESCRIPTION}` - What your app does (e.g., "Manages email campaigns")
- `{APP_ID}` - Unique app ID (e.g., "email-manager")
- `{CAPABILITIES}` - Required capabilities (e.g., "email_sending, scheduling")

---

## 📝 **Example**

```
Create a complete Agentify-compliant React application with the following specifications:

## App Details
- App Name: Email Campaign Manager
- Description: Manage and automate email marketing campaigns
- Required Agent Capabilities: email_sending, scheduling, analytics

[... rest of prompt ...]
```

---

## ✅ **Verification**

After generation, verify:

1. ✅ All files created
2. ✅ `npm install` works
3. ✅ `npm run dev` starts the app
4. ✅ Both layouts render correctly
5. ✅ Orchestrator initializes
6. ✅ Marketplace integration works

---

**Next:** Test your app and iterate with additional prompts!

