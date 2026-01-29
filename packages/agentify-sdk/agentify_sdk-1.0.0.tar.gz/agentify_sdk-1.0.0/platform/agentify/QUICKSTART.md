# 🚀 Agentify Platform - Quick Start

**Build your first Agentify app in 10 minutes**

---

## 🎯 **What You'll Build**

A simple **Task Manager App** with:
- ✅ Built-in orchestrator agent
- ✅ Marketplace integration
- ✅ Team building UI
- ✅ Standalone & Integrated modes

---

## 📋 **Prerequisites**

- Node.js 18+ and npm
- Basic React knowledge
- (Optional) Lovable account for AI-assisted development

---

## 🚀 **Option 1: AI-Assisted (Recommended)**

### **Using Lovable**

1. Go to [lovable.dev](https://lovable.dev)
2. Copy this prompt:

```
Create an Agentify-compliant React application with the following specifications:

## App Details
- App Name: Task Manager
- Description: Manage tasks with AI agent assistance
- Required Agent Capabilities: task_scheduling, reminders, analytics

[Copy the full prompt from: platform/agentify/app_standard/prompts/create_app.md]
```

3. Paste into Lovable and click "Generate"
4. Wait for generation (2-3 minutes)
5. Download and run:

```bash
npm install
npm run dev
```

**Done!** Your app is running at `http://localhost:5173`

---

## 🛠️ **Option 2: Manual Setup**

### **Step 1: Create Vite Project**

```bash
npm create vite@latest task-manager -- --template react-ts
cd task-manager
npm install
```

### **Step 2: Install Dependencies**

```bash
npm install zustand react-router-dom axios lucide-react
npm install -D tailwindcss postcss autoprefixer
npx tailwindcss init -p
```

### **Step 3: Configure Tailwind**

```js
// tailwind.config.js
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {},
  },
  plugins: [],
}
```

```css
/* src/index.css */
@tailwind base;
@tailwind components;
@tailwind utilities;
```

### **Step 4: Create App Manifest**

```json
// public/agentify.json
{
  "app_id": "app.mycompany.task-manager",
  "name": "Task Manager",
  "version": "1.0.0",
  "description": "Manage tasks with AI agent assistance",
  "orchestrator": {
    "manifest_path": "/src/agents/orchestrator/manifest.json",
    "enabled": true
  },
  "modes": {
    "standalone": true,
    "integrated": true
  },
  "marketplace": {
    "url": "https://marketplace.agentify.io",
    "auto_register": true
  }
}
```

### **Step 5: Create Orchestrator Manifest**

```bash
mkdir -p src/agents/orchestrator
```

```json
// src/agents/orchestrator/manifest.json
{
  "agent_id": "agent.task-manager.orchestrator",
  "name": "Task Manager Orchestrator",
  "version": "1.0.0",
  "status": "active",
  "ethics": {
    "framework": "harm-minimization",
    "hard_constraints": ["no_unauthorized_team_changes"]
  },
  "desires": {
    "profile": [
      {"id": "team_efficiency", "weight": 0.5},
      {"id": "cost_optimization", "weight": 0.5}
    ]
  },
  "tools": [
    {
      "name": "query_marketplace",
      "description": "Query marketplace for agents",
      "category": "discovery"
    }
  ],
  "authority": {
    "instruction": {"type": "app", "id": "app.mycompany.task-manager"},
    "oversight": {"type": "human", "id": "user", "independent": true}
  }
}
```

### **Step 6: Create Zustand Stores**

```typescript
// src/stores/appStore.ts
import { create } from 'zustand';

interface AppState {
  mode: 'standalone' | 'integrated';
  setMode: (mode: 'standalone' | 'integrated') => void;
}

export const useAppStore = create<AppState>((set) => ({
  mode: 'standalone',
  setMode: (mode) => set({ mode }),
}));
```

```typescript
// src/stores/agentStore.ts
import { create } from 'zustand';

interface Agent {
  agent_id: string;
  name: string;
  rating: number;
}

interface AgentState {
  team: Agent[];
  addAgent: (agent: Agent) => void;
}

export const useAgentStore = create<AgentState>((set) => ({
  team: [],
  addAgent: (agent) => set((state) => ({ team: [...state.team, agent] })),
}));
```

### **Step 7: Create Layouts**

```tsx
// src/components/layout/Standalone.tsx
import { Outlet } from 'react-router-dom';

export function StandaloneLayout() {
  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 py-6">
          <h1 className="text-3xl font-bold">Task Manager</h1>
        </div>
      </header>
      <main className="max-w-7xl mx-auto px-4 py-6">
        <Outlet />
      </main>
    </div>
  );
}
```

### **Step 8: Create Main App**

```tsx
// src/App.tsx
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { StandaloneLayout } from './components/layout/Standalone';
import { HomePage } from './pages/Home';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<StandaloneLayout />}>
          <Route path="/" element={<HomePage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
```

```tsx
// src/pages/Home.tsx
export function HomePage() {
  return (
    <div>
      <h2 className="text-2xl font-bold mb-4">Welcome to Task Manager</h2>
      <p>Your Agentify app is ready!</p>
    </div>
  );
}
```

### **Step 9: Run the App**

```bash
npm run dev
```

Visit `http://localhost:5173` - Your Agentify app is running! 🎉

---

## 🎨 **Next Steps**

### **1. Add Team Building UI**

See [app_standard/examples/team-builder/](app_standard/examples/team-builder/) for a complete example.

### **2. Integrate Marketplace**

```typescript
// src/services/marketplace.ts
import axios from 'axios';

export async function searchAgents(capabilities: string[]) {
  const response = await axios.post(
    'https://marketplace.agentify.io/api/search',
    { requirements: { capabilities } }
  );
  return response.data;
}
```

### **3. Add Integrated Mode**

Create `src/components/layout/Integrated.tsx` with sidebar + main layout.

### **4. Deploy**

Deploy to Vercel, Netlify, or Railway:

```bash
npm run build
# Deploy dist/ folder
```

---

## 📚 **Resources**

- **[App Standard](app_standard/README.md)** - Complete specification
- **[AI Prompts](app_standard/prompts/)** - AI-assisted development
- **[Examples](app_standard/examples/)** - Real-world examples
- **[Architecture](ARCHITECTURE.md)** - Platform architecture

---

## 🆘 **Troubleshooting**

### **Issue: Marketplace not responding**

The marketplace is not yet deployed. For development, use mock data:

```typescript
// src/services/marketplace.ts
export async function searchAgents(capabilities: string[]) {
  // Mock data for development
  return [
    {
      agent_id: "agent.example.task-scheduler",
      name: "Task Scheduler",
      rating: 8.5,
      price: 0.01
    }
  ];
}
```

### **Issue: Tailwind not working**

Make sure you imported `index.css` in `main.tsx`:

```typescript
import './index.css';
```

---

**Congratulations! You've built your first Agentify app! 🎉**

**Next:** [Add more features](app_standard/README.md) or [deploy to production](../../DEPLOYMENT.md)

