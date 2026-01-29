# 🎨 Agentify UI Templates

**Ready-to-use React templates for Agents and Apps**

---

## 📦 **Available Templates**

### **1. Agent UI Template** (`agent-ui-template.tsx`)

Complete UI for displaying agent information with all 14 manifest sections:

- ✅ **Overview** - Identity, capabilities, AI model
- ✅ **Ethics & Desires** - Runtime-active ethics and health monitoring
- ✅ **Pricing** - Pricing model and revenue sharing
- ✅ **Tools** - Available tools and connections
- ✅ **Memory** - Memory slots and implementation
- ✅ **Schedule** - Scheduled jobs and cron tasks
- ✅ **Activities** - Activity queue and execution state
- ✅ **Prompt & Guardrails** - System prompt and guardrails
- ✅ **Team** - Team relationships and graph
- ✅ **Customers** - Customer assignments and load
- ✅ **Knowledge** - RAG datasets and retrieval policies
- ✅ **I/O** - Input/output formats and contracts
- ✅ **Revisions** - Revision history and changelog
- ✅ **Authority & Oversight** - Four-Eyes Principle and incidents

**Features:**
- 📊 Health monitoring with color-coded states
- 🎯 Desire satisfaction progress bars
- 🛡️ Ethics constraints (hard/soft)
- 📈 Real-time status indicators
- 🎨 Modern UI with shadcn/ui components

### **2. App UI Template** (`app-ui-template.tsx`)

Complete UI for Agentify-compliant React apps:

- ✅ **Marketplace Integration** - Search and discover agents
- ✅ **Team Builder** - Build and manage agent teams
- ✅ **Activity Log** - Monitor agent activities
- ✅ **Agent Cards** - Display agent information
- ✅ **Status Management** - Pause/resume agents

**Features:**
- 🔍 Agent search and filtering
- 👥 Team management UI
- 💰 Pricing display
- ⭐ Agent ratings
- 🎨 Responsive design

### **3. React App HowTo** (`REACT_APP_HOWTO.md`)

Complete guide to building Agentify apps:

- ✅ **Quick Start** - Create new React app with Vite
- ✅ **Dependencies** - Install required packages
- ✅ **Project Structure** - Recommended folder structure
- ✅ **Core Implementation** - Zustand stores, API services
- ✅ **Deployment** - Deploy to Vercel, Netlify, Railway

---

## 🚀 **Quick Start**

### **1. Create New React App**

```bash
npm create vite@latest my-agentify-app -- --template react-ts
cd my-agentify-app
npm install
```

### **2. Install Dependencies**

```bash
# Core
npm install zustand react-router-dom axios

# UI
npx shadcn@latest init
npx shadcn@latest add card button input badge tabs alert progress

# Icons
npm install lucide-react
```

### **3. Copy Templates**

```bash
# Copy agent UI template
cp platform/agentify/templates/agent-ui-template.tsx src/components/AgentUI.tsx

# Copy app UI template
cp platform/agentify/templates/app-ui-template.tsx src/App.tsx
```

### **4. Run**

```bash
npm run dev
```

---

## 📚 **Usage Examples**

### **Agent UI Template**

```typescript
import { AgentUI } from '@/components/AgentUI';

function MyAgentPage() {
  const manifest = {
    agent_id: 'agent.company.email',
    name: 'Email Agent',
    version: '1.0.0',
    status: 'active',
    overview: {
      description: 'Handles email operations',
      tags: ['email', 'communication'],
      owner: { name: 'Company' },
    },
    capabilities: [
      { name: 'send_email', level: 'expert' },
      { name: 'read_email', level: 'expert' },
    ],
    ethics: {
      framework: 'consequentialist',
      hard_constraints: ['No spam', 'No phishing'],
      soft_constraints: ['Prefer concise emails'],
    },
    desires: {
      profile: [
        { id: 'efficiency', weight: 0.8, satisfaction: 0.9 },
        { id: 'accuracy', weight: 0.9, satisfaction: 0.85 },
      ],
    },
    health: {
      state: 'healthy',
      tension: 0.2,
    },
    // ... rest of manifest
  };

  return <AgentUI manifest={manifest} />;
}
```

### **App UI Template**

```typescript
import { AgentifyApp } from '@/App';

function App() {
  return <AgentifyApp />;
}
```

---

## 🎨 **Customization**

### **Colors**

Edit `tailwind.config.js`:

```js
theme: {
  extend: {
    colors: {
      primary: '#your-color',
      secondary: '#your-color',
    },
  },
}
```

### **Components**

All templates use shadcn/ui components. Customize in `src/components/ui/`.

### **Icons**

Templates use Lucide React. Replace with your preferred icon library.

---

## 📖 **Documentation**

- **Agent Standard**: `platform/agentify/agent_standard/README.md`
- **App Standard**: `platform/agentify/app_standard/README.md`
- **React HowTo**: `platform/agentify/templates/REACT_APP_HOWTO.md`
- **Marketplace**: `platform/agentify/marketplace/README.md`

---

## 🔗 **Resources**

- **Vite**: https://vite.dev
- **React**: https://react.dev
- **shadcn/ui**: https://ui.shadcn.com
- **Zustand**: https://zustand-demo.pmnd.rs
- **Lucide Icons**: https://lucide.dev

---

## 📞 **Support**

- **GitHub Issues**: https://github.com/JonasDEMA/cpa_agent_platform/issues
- **Discussions**: https://github.com/JonasDEMA/cpa_agent_platform/discussions

---

**Happy Building! 🚀**

