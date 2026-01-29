# 📊 Data Access & Logging Guide

**Complete guide for implementing data persistence and logging in Agentify apps**

---

## 🎯 **Overview**

Every Agentify app needs to make two critical decisions:

1. **How to store data?** (Data Access Layer)
2. **How to log events?** (Logging Layer)

This guide helps you choose the right strategy for your app.

---

## 📦 **Data Access Layer (DAL)**

### **Decision Matrix**

| Strategy | Use Case | Pros | Cons | Recommended For |
|----------|----------|------|------|-----------------|
| **Own Database** | Full control over data | Fast, real-time, built-in auth | App-specific data | Lovable apps, production apps |
| **Data Agent** | Centralized data management | Data sharing, no setup | Network latency | Multi-app ecosystems |
| **External Service** | Enterprise integration | Compliance, governance | External dependency | Enterprise apps |

---

### **Option A: Own Database (Supabase)**

**Best for:** Lovable apps, production apps, apps with complex data models

**Setup:**

1. Create a Supabase project at [supabase.com](https://supabase.com)
2. Add credentials to `.env`:
   ```env
   VITE_SUPABASE_URL=https://your-project.supabase.co
   VITE_SUPABASE_ANON_KEY=your-anon-key
   ```
3. Install Supabase client:
   ```bash
   npm install @supabase/supabase-js
   ```
4. Implement database service (see `implementation_examples.md`)

**Features:**
- ✅ PostgreSQL database
- ✅ Real-time subscriptions
- ✅ Built-in authentication
- ✅ File storage
- ✅ Row-level security

---

### **Option B: Data Agent (Delegated)**

**Best for:** Multi-app ecosystems, apps that share data

**Setup:**

1. Orchestrator discovers a data storage agent from marketplace
2. All data operations delegated to the agent
3. No database setup needed

**Features:**
- ✅ Centralized data management
- ✅ Data sharing across apps
- ✅ No database setup
- ❌ Network latency
- ❌ Depends on agent availability

---

### **Option C: External Data Service**

**Best for:** Enterprise apps, apps integrating with existing systems

**Setup:**

1. Add API credentials to `.env`:
   ```env
   VITE_DATA_SERVICE_URL=https://api.company.com
   VITE_DATA_SERVICE_API_KEY=your-api-key
   ```
2. Implement data service (see `implementation_examples.md`)

**Features:**
- ✅ Enterprise integration
- ✅ Existing data governance
- ✅ Compliance & security
- ❌ External dependency
- ❌ Requires API credentials

---

## 📝 **Logging Layer**

### **Decision Matrix**

| Strategy | Use Case | Pros | Cons | Recommended For |
|----------|----------|------|------|-----------------|
| **Logging Service** | Production monitoring | Persistent, centralized | Requires setup | Production apps |
| **Logging Agent** | Centralized logging | No setup, agent handles retention | Network latency | Multi-app ecosystems |
| **Local Logging** | Development | Simple, fast | Not persistent | Development only |

---

### **Option A: Logging Service (Supabase)**

**Best for:** Production apps, apps with monitoring requirements

**Setup:**

1. Create logs table in Supabase:
   ```sql
   CREATE TABLE logs (
     id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
     level TEXT NOT NULL,
     message TEXT NOT NULL,
     meta JSONB,
     timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
     app_id TEXT NOT NULL,
     user_id UUID REFERENCES auth.users(id),
     created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
   );
   ```
2. Implement logging service (see `implementation_examples.md`)

**Features:**
- ✅ Persistent logs
- ✅ Centralized monitoring
- ✅ Query & analytics
- ✅ Real-time log streaming

---

### **Option B: Logging Agent (Delegated)**

**Best for:** Multi-app ecosystems, apps that share logging infrastructure

**Setup:**

1. Orchestrator discovers a logging agent from marketplace
2. All logs sent to the agent
3. No logging setup needed

**Features:**
- ✅ Centralized logging
- ✅ No setup needed
- ✅ Agent handles retention
- ❌ Network latency
- ❌ Depends on agent availability

---

### **Option C: Local Logging (Console)**

**Best for:** Development and debugging

**Setup:**

1. Use console.log, console.warn, console.error
2. No setup needed

**Features:**
- ✅ Simple & fast
- ✅ No setup needed
- ❌ Not persistent
- ❌ No centralized monitoring

---

## 🤖 **Auto-Configuration**

The orchestrator can automatically configure data and logging layers:

### **Data Layer Auto-Config**

```typescript
async function autoConfigureDataLayer() {
  // Check if Supabase credentials are present
  if (hasSupabaseCredentials()) {
    return 'database'; // Use Supabase
  }
  
  // Ask developer
  const choice = await promptDeveloper({
    title: 'Configure Data Layer',
    options: ['database', 'agent', 'service'],
  });
  
  return choice;
}
```

### **Logging Auto-Config**

```typescript
async function autoConfigureLogging() {
  // Check environment
  if (isProduction() && hasSupabaseCredentials()) {
    return 'service'; // Use Supabase logging
  }
  
  if (isDevelopment()) {
    return 'local'; // Use console.log
  }
  
  // Ask developer
  const choice = await promptDeveloper({
    title: 'Configure Logging',
    options: ['service', 'agent', 'local'],
  });
  
  return choice;
}
```

---

## 📚 **Resources**

- **Implementation Examples**: `implementation_examples.md`
- **Architecture**: `../ARCHITECTURE.md`
- **AI Prompt**: `prompts/create_app.md`

---

**Next Steps:**
1. Choose your data access strategy
2. Choose your logging strategy
3. Implement the corresponding services
4. Test your configuration

