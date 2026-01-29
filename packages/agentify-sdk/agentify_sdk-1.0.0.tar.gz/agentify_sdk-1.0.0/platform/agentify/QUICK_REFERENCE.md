# 🚀 Agentify Quick Reference

**Fast reference for building Agentify apps**

---

## 📦 **Data Access Layer**

| Strategy | When to Use | Setup Time | Code Example |
|----------|-------------|------------|--------------|
| **Supabase DB** | Lovable apps, production | 5 min | `db.getUsers()` |
| **Data Agent** | Multi-app ecosystems | 1 min | `dataAgent.getUsers()` |
| **External Service** | Enterprise integration | 10 min | `dataService.getUsers()` |

**Default:** Supabase DB (if credentials available)

---

## 📝 **Logging Strategy**

| Strategy | When to Use | Setup Time | Code Example |
|----------|-------------|------------|--------------|
| **Supabase Logs** | Production apps | 5 min | `logger.info('message')` |
| **Logging Agent** | Multi-app ecosystems | 1 min | `logger.info('message')` |
| **Local Logs** | Development only | 0 min | `console.log('message')` |

**Default:** Supabase Logs (production), Local Logs (development)

---

## 🤖 **Orchestrator Tools**

| Tool | Purpose | Example |
|------|---------|---------|
| `query_marketplace` | Find agents | `orchestrator.findAgent({ capability: 'email' })` |
| `build_team` | Build agent team | `orchestrator.buildTeam([agent1, agent2])` |
| `configure_data_layer` | Configure data | `orchestrator.configureDataLayer('database')` |
| `configure_logging` | Configure logging | `orchestrator.configureLogging('service')` |

---

## 🛠️ **Quick Setup**

### **1. Create App with Lovable**

```bash
# Copy AI prompt from:
platform/agentify/app_standard/prompts/create_app.md

# Paste into Lovable and customize:
- App Name: "My App"
- Description: "What it does"
- Capabilities: "email, scheduling"
```

### **2. Add Supabase (Recommended)**

```bash
# 1. Create project at supabase.com
# 2. Add to .env:
VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_ANON_KEY=your-anon-key

# 3. Install:
npm install @supabase/supabase-js
```

### **3. Run App**

```bash
npm install
npm run dev
```

---

## 📁 **Project Structure**

```
my-app/
├── public/
│   └── agentify.json              # App manifest
├── src/
│   ├── agents/orchestrator/       # Orchestrator agent
│   ├── components/                # React components
│   ├── services/
│   │   ├── database.ts            # Supabase DB
│   │   ├── logger.ts              # Logging
│   │   └── orchestrator.ts        # Orchestrator
│   ├── stores/                    # Zustand stores
│   └── types/                     # TypeScript types
└── .env                           # Environment variables
```

---

## 🔧 **Environment Variables**

```env
# App
VITE_APP_ID=app.company.myapp
VITE_APP_NAME=My App

# Supabase (Recommended)
VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_ANON_KEY=your-anon-key

# Marketplace
VITE_MARKETPLACE_URL=https://marketplace.agentify.dev

# Configuration
VITE_DATA_LAYER_STRATEGY=database
VITE_LOGGING_STRATEGY=service
```

---

## 📊 **Decision Trees**

### **Data Layer**

```
Do you have Supabase credentials?
├─ Yes → Use Supabase DB ✅
└─ No → Choose:
    ├─ Data Agent (multi-app)
    ├─ External Service (enterprise)
    └─ Setup Supabase (recommended)
```

### **Logging**

```
Is this production?
├─ Yes → Use Supabase Logs ✅
└─ No (Development) → Use Local Logs
```

---

## 🎯 **Common Tasks**

### **Add Database Table**

```sql
-- In Supabase SQL Editor:
CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  name TEXT NOT NULL,
  email TEXT UNIQUE NOT NULL,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### **Query Database**

```typescript
// src/services/database.ts
export const db = {
  async getUsers() {
    const { data, error } = await supabase.from('users').select('*');
    if (error) throw error;
    return data;
  }
};
```

### **Log Event**

```typescript
// src/services/logger.ts
import { logger } from './logger';

logger.info('User logged in', { userId: '123' });
logger.error('Failed to save', { error: 'Network error' });
```

### **Find Agent**

```typescript
// src/services/orchestrator.ts
const agent = await orchestrator.findAgent({ 
  capability: 'email_sending' 
});

await agent.execute({
  action: 'send_email',
  params: { to: 'user@example.com', subject: 'Hello' }
});
```

---

## 📚 **Resources**

| Document | Purpose |
|----------|---------|
| `ARCHITECTURE.md` | Complete architecture |
| `DATA_AND_LOGGING.md` | Data & logging guide |
| `implementation_examples.md` | Code examples |
| `create_app.md` | AI prompt for app creation |
| `CHANGELOG_ARCHITECTURE.md` | What's new |

---

## ✅ **Checklist**

### **Before Starting:**
- [ ] Read `ARCHITECTURE.md`
- [ ] Choose data strategy
- [ ] Choose logging strategy
- [ ] Setup Supabase (if using)

### **During Development:**
- [ ] Implement orchestrator
- [ ] Implement data layer
- [ ] Implement logging
- [ ] Test auto-configuration

### **Before Deployment:**
- [ ] Test all features
- [ ] Configure production logging
- [ ] Setup environment variables
- [ ] Test marketplace integration

---

**Quick Start:** Copy AI prompt → Paste in Lovable → Add Supabase → Run!

