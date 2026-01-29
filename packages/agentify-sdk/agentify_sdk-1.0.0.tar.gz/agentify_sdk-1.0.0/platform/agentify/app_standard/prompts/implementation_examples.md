# 🛠️ Implementation Examples - Agentify App

**Complete implementation examples for Data Layer, Logging, and Orchestrator**

---

## 📦 **Data Access Layer Implementations**

### **Option A: Supabase Database (Recommended)**

**1. Install Dependencies:**
```bash
npm install @supabase/supabase-js
```

**2. Environment Variables (.env):**
```env
VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_ANON_KEY=your-anon-key
```

**3. Database Service (src/services/database.ts):**
```typescript
import { createClient } from '@supabase/supabase-js';

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL;
const supabaseKey = import.meta.env.VITE_SUPABASE_ANON_KEY;

export const supabase = createClient(supabaseUrl, supabaseKey);

export const db = {
  // Users
  async getUsers() {
    const { data, error } = await supabase.from('users').select('*');
    if (error) throw error;
    return data;
  },

  async createUser(user: { name: string; email: string }) {
    const { data, error } = await supabase.from('users').insert(user).select();
    if (error) throw error;
    return data[0];
  },

  async updateUser(id: string, updates: Partial<User>) {
    const { data, error } = await supabase
      .from('users')
      .update(updates)
      .eq('id', id)
      .select();
    if (error) throw error;
    return data[0];
  },

  async deleteUser(id: string) {
    const { error } = await supabase.from('users').delete().eq('id', id);
    if (error) throw error;
  },

  // Real-time subscriptions
  subscribeToUsers(callback: (payload: any) => void) {
    return supabase
      .channel('users')
      .on('postgres_changes', { event: '*', schema: 'public', table: 'users' }, callback)
      .subscribe();
  },
};
```

**4. Supabase Schema (SQL):**
```sql
-- Create users table
CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  name TEXT NOT NULL,
  email TEXT UNIQUE NOT NULL,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Enable Row Level Security
ALTER TABLE users ENABLE ROW LEVEL SECURITY;

-- Create policy for authenticated users
CREATE POLICY "Users can read all users" ON users
  FOR SELECT USING (auth.role() = 'authenticated');

CREATE POLICY "Users can insert their own data" ON users
  FOR INSERT WITH CHECK (auth.uid() = id);
```

---

### **Option B: Data Agent (Delegated)**

**1. Data Agent Service (src/services/dataAgent.ts):**
```typescript
import { orchestrator } from './orchestrator';

export const dataAgent = {
  async getUsers() {
    const agent = await orchestrator.findAgent({ capability: 'data_storage' });
    const result = await agent.execute({
      action: 'query',
      params: {
        table: 'users',
        operation: 'select',
        filters: {},
      },
    });
    return result.data;
  },

  async createUser(user: { name: string; email: string }) {
    const agent = await orchestrator.findAgent({ capability: 'data_storage' });
    const result = await agent.execute({
      action: 'insert',
      params: {
        table: 'users',
        data: user,
      },
    });
    return result.data;
  },

  async updateUser(id: string, updates: Partial<User>) {
    const agent = await orchestrator.findAgent({ capability: 'data_storage' });
    const result = await agent.execute({
      action: 'update',
      params: {
        table: 'users',
        id,
        data: updates,
      },
    });
    return result.data;
  },

  async deleteUser(id: string) {
    const agent = await orchestrator.findAgent({ capability: 'data_storage' });
    await agent.execute({
      action: 'delete',
      params: {
        table: 'users',
        id,
      },
    });
  },
};
```

---

### **Option C: External Data Service**

**1. Data Service (src/services/dataService.ts):**
```typescript
import axios from 'axios';

const api = axios.create({
  baseURL: import.meta.env.VITE_DATA_SERVICE_URL,
  headers: {
    'Authorization': `Bearer ${import.meta.env.VITE_API_KEY}`,
    'Content-Type': 'application/json',
  },
});

export const dataService = {
  async getUsers() {
    const { data } = await api.get('/users');
    return data;
  },

  async createUser(user: { name: string; email: string }) {
    const { data } = await api.post('/users', user);
    return data;
  },

  async updateUser(id: string, updates: Partial<User>) {
    const { data } = await api.patch(`/users/${id}`, updates);
    return data;
  },

  async deleteUser(id: string) {
    await api.delete(`/users/${id}`);
  },
};
```

---

## 📝 **Logging Implementations**

### **Option A: Supabase Logging (Recommended)**

**1. Logging Service (src/services/logger.ts):**
```typescript
import { supabase } from './database';

type LogLevel = 'info' | 'warn' | 'error' | 'debug';

interface LogEntry {
  level: LogLevel;
  message: string;
  meta?: any;
  timestamp: string;
  app_id: string;
  user_id?: string;
}

export const logger = {
  async log(level: LogLevel, message: string, meta?: any) {
    const entry: LogEntry = {
      level,
      message,
      meta,
      timestamp: new Date().toISOString(),
      app_id: 'app.company.myapp',
      user_id: supabase.auth.getUser().then(u => u.data.user?.id),
    };

    // Log to console
    console[level === 'error' ? 'error' : level === 'warn' ? 'warn' : 'log'](
      `[${level.toUpperCase()}]`,
      message,
      meta
    );

    // Log to Supabase
    try {
      await supabase.from('logs').insert(entry);
    } catch (error) {
      console.error('Failed to log to Supabase:', error);
    }
  },

  info: (message: string, meta?: any) => logger.log('info', message, meta),
  warn: (message: string, meta?: any) => logger.log('warn', message, meta),
  error: (message: string, meta?: any) => logger.log('error', message, meta),
  debug: (message: string, meta?: any) => logger.log('debug', message, meta),
};
```

**2. Supabase Schema (SQL):**
```sql
-- Create logs table
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

-- Create index for faster queries
CREATE INDEX logs_timestamp_idx ON logs(timestamp DESC);
CREATE INDEX logs_level_idx ON logs(level);
CREATE INDEX logs_app_id_idx ON logs(app_id);

-- Enable Row Level Security
ALTER TABLE logs ENABLE ROW LEVEL SECURITY;

-- Policy: Users can read their own logs
CREATE POLICY "Users can read their own logs" ON logs
  FOR SELECT USING (auth.uid() = user_id);
```

---

### **Option B: Logging Agent (Delegated)**

**1. Logging Service (src/services/logger.ts):**
```typescript
import { orchestrator } from './orchestrator';

type LogLevel = 'info' | 'warn' | 'error' | 'debug';

export const logger = {
  async log(level: LogLevel, message: string, meta?: any) {
    // Log to console
    console[level === 'error' ? 'error' : level === 'warn' ? 'warn' : 'log'](
      `[${level.toUpperCase()}]`,
      message,
      meta
    );

    // Log to agent
    try {
      const agent = await orchestrator.findAgent({ capability: 'logging' });
      await agent.execute({
        action: 'log',
        params: {
          level,
          message,
          meta,
          timestamp: new Date().toISOString(),
          app_id: 'app.company.myapp',
        },
      });
    } catch (error) {
      console.error('Failed to log to agent:', error);
    }
  },

  info: (message: string, meta?: any) => logger.log('info', message, meta),
  warn: (message: string, meta?: any) => logger.log('warn', message, meta),
  error: (message: string, meta?: any) => logger.log('error', message, meta),
  debug: (message: string, meta?: any) => logger.log('debug', message, meta),
};
```

---

## 🤖 **Orchestrator Implementation**

**1. Orchestrator Service (src/services/orchestrator.ts):**
```typescript
import { marketplaceService } from './marketplace';
import { Agent } from '../types/agent';

class Orchestrator {
  private team: Agent[] = [];

  async findAgent(requirements: { capability: string }): Promise<Agent> {
    // Check if agent already in team
    const existing = this.team.find(a => 
      a.capabilities.includes(requirements.capability)
    );
    if (existing) return existing;

    // Search marketplace
    const agents = await marketplaceService.searchAgents({
      capabilities: [requirements.capability],
    });

    if (agents.length === 0) {
      throw new Error(`No agent found with capability: ${requirements.capability}`);
    }

    // Select best agent (highest rating)
    const bestAgent = agents.sort((a, b) => b.rating - a.rating)[0];

    // Add to team
    this.team.push(bestAgent);

    return bestAgent;
  }

  async configureDataLayer(strategy: 'database' | 'agent' | 'service') {
    if (strategy === 'agent') {
      await this.findAgent({ capability: 'data_storage' });
    }
    // Store configuration
    localStorage.setItem('data_layer_strategy', strategy);
  }

  async configureLogging(strategy: 'local' | 'service' | 'agent') {
    if (strategy === 'agent') {
      await this.findAgent({ capability: 'logging' });
    }
    // Store configuration
    localStorage.setItem('logging_strategy', strategy);
  }

  getTeam(): Agent[] {
    return this.team;
  }
}

export const orchestrator = new Orchestrator();
```

---

**Use these examples as templates for your Agentify app implementation!**

