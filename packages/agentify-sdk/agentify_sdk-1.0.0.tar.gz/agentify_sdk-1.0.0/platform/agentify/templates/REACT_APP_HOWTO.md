# 🚀 React App HowTo - Agentify Platform

**Complete guide to building Agentify-compliant React applications**

---

## 📋 **Quick Start**

### **1. Create New React App with Vite**

```bash
# Create new Vite + React + TypeScript project
npm create vite@latest my-agentify-app -- --template react-ts

# Navigate to project
cd my-agentify-app

# Install dependencies
npm install
```

### **2. Install Required Dependencies**

```bash
# Core dependencies
npm install zustand react-router-dom axios

# UI Components (shadcn/ui)
npm install tailwindcss postcss autoprefixer
npx tailwindcss init -p

# shadcn/ui components
npx shadcn@latest init
npx shadcn@latest add card button input badge tabs alert progress

# Icons
npm install lucide-react

# Forms (optional)
npm install react-hook-form zod @hookform/resolvers

# Date handling (optional)
npm install date-fns
```

### **3. Configure Tailwind CSS**

**`tailwind.config.js`:**
```js
/** @type {import('tailwindcss').Config} */
export default {
  darkMode: ["class"],
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {},
  },
  plugins: [require("tailwindcss-animate")],
}
```

**`src/index.css`:**
```css
@tailwind base;
@tailwind components;
@tailwind utilities;
```

---

## 📦 **Project Structure**

```
my-agentify-app/
├── src/
│   ├── components/          # React components
│   │   ├── ui/             # shadcn/ui components
│   │   ├── AgentCard.tsx   # Agent display component
│   │   ├── TeamBuilder.tsx # Team building UI
│   │   └── Marketplace.tsx # Marketplace integration
│   │
│   ├── stores/             # Zustand stores
│   │   ├── agentStore.ts   # Agent state management
│   │   └── teamStore.ts    # Team state management
│   │
│   ├── services/           # API services
│   │   ├── marketplace.ts  # Marketplace API
│   │   └── orchestrator.ts # Orchestrator API
│   │
│   ├── types/              # TypeScript types
│   │   ├── agent.ts        # Agent types
│   │   └── manifest.ts     # Manifest types
│   │
│   ├── App.tsx             # Main app component
│   ├── main.tsx            # Entry point
│   └── index.css           # Global styles
│
├── public/                 # Static assets
├── package.json
├── tsconfig.json
├── vite.config.ts
└── tailwind.config.js
```

---

## 🎯 **Core Implementation**

### **1. Agent Store (Zustand)**

**`src/stores/agentStore.ts`:**
```typescript
import { create } from 'zustand';

interface Agent {
  agent_id: string;
  name: string;
  capabilities: string[];
  status: 'available' | 'busy' | 'offline';
}

interface AgentStore {
  agents: Agent[];
  selectedAgent: Agent | null;
  setAgents: (agents: Agent[]) => void;
  selectAgent: (agent: Agent) => void;
}

export const useAgentStore = create<AgentStore>((set) => ({
  agents: [],
  selectedAgent: null,
  setAgents: (agents) => set({ agents }),
  selectAgent: (agent) => set({ selectedAgent: agent }),
}));
```

### **2. Marketplace Service**

**`src/services/marketplace.ts`:**
```typescript
import axios from 'axios';

const MARKETPLACE_URL = 'https://marketplace.agentify.dev/api/v1';

export const marketplaceService = {
  // Search agents
  async searchAgents(query: string) {
    const response = await axios.get(`${MARKETPLACE_URL}/agents/search`, {
      params: { q: query },
    });
    return response.data;
  },

  // Get agent details
  async getAgent(agentId: string) {
    const response = await axios.get(`${MARKETPLACE_URL}/agents/${agentId}`);
    return response.data;
  },

  // Discover agents by capability
  async discoverByCapability(capability: string) {
    const response = await axios.post(`${MARKETPLACE_URL}/agents/discover`, {
      capability,
    });
    return response.data;
  },
};
```

### **3. Main App Component**

**`src/App.tsx`:**
```typescript
import { useState } from 'react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Marketplace } from '@/components/Marketplace';
import { TeamBuilder } from '@/components/TeamBuilder';
import { Bot } from 'lucide-react';

function App() {
  return (
    <div className="min-h-screen bg-background">
      <header className="border-b">
        <div className="container mx-auto px-4 py-4">
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <Bot className="w-6 h-6" />
            My Agentify App
          </h1>
        </div>
      </header>

      <main className="container mx-auto px-4 py-8">
        <Tabs defaultValue="marketplace">
          <TabsList>
            <TabsTrigger value="marketplace">Marketplace</TabsTrigger>
            <TabsTrigger value="team">My Team</TabsTrigger>
          </TabsList>

          <TabsContent value="marketplace">
            <Marketplace />
          </TabsContent>

          <TabsContent value="team">
            <TeamBuilder />
          </TabsContent>
        </Tabs>
      </main>
    </div>
  );
}

export default App;
```

---

## 🎨 **Using the Templates**

### **Copy Agent UI Template**

```bash
# Copy the agent UI template
cp platform/agentify/templates/agent-ui-template.tsx src/components/AgentUI.tsx
```

### **Copy App UI Template**

```bash
# Copy the app UI template
cp platform/agentify/templates/app-ui-template.tsx src/App.tsx
```

---

## 🚀 **Run the App**

```bash
# Development mode
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

---

## 📚 **Next Steps**

1. ✅ **Customize UI** - Modify templates for your use case
2. ✅ **Add Marketplace Integration** - Connect to Agentify Marketplace
3. ✅ **Implement Orchestrator** - Build agent team logic
4. ✅ **Add Authentication** - Secure your app
5. ✅ **Deploy** - Deploy to Vercel, Netlify, or Railway

---

## 🔗 **Resources**

- **Vite Docs**: https://vite.dev
- **React Docs**: https://react.dev
- **shadcn/ui**: https://ui.shadcn.com
- **Zustand**: https://zustand-demo.pmnd.rs
- **Agentify Docs**: `platform/agentify/README.md`

---

**Happy Building! 🚀**

