# 🏪 Agentify Marketplace - Requirements Specification

**Version: 1.0.0**  
**Date: 2026-01-16**  
**URL: marketplace.meet-harmony.ai**

---

## 🎯 **Overview**

The Agentify Marketplace is the **central discovery and distribution platform** for Agentify apps and agents. It enables:

- **Discovery**: Find agents and apps by capability, tags, or name
- **Registration**: Publish agents and apps with metadata
- **Billing**: Track usage and handle payments
- **Authentication**: Secure access via CoreSense IAM
- **Ratings**: Community-driven quality assessment
- **Visibility Control**: Public, team, project, or organization-only

---

## 🏗️ **Architecture**

The Marketplace is itself an **Agentify App** with:

- **Built-in Orchestrator Agent** (manages marketplace operations)
- **Data Layer**: Supabase (agents, apps, creators, ratings, billing)
- **Logging**: Supabase (audit logs, usage tracking)
- **Authentication**: CoreSense IAM
- **Frontend**: React + Vite + Tailwind + shadcn/ui

---

## 📋 **Core Features**

### **1. Agent & App Registration**

**Entities:**
- **Agents**: Specialized workers (e.g., calculation agent, email agent)
- **Apps**: Complete applications with orchestrators (e.g., email manager)

**Registration Data:**

```typescript
interface AgentRegistration {
  agent_id: string;                    // e.g., "agent.company.calculator"
  name: string;                        // e.g., "Calculator Agent"
  description: string;                 // What it does
  creator: {
    id: string;                        // Creator ID
    name: string;                      // Creator name
    type: 'user' | 'organization' | 'team';
  };
  capabilities: string[];              // e.g., ["math", "calculation"]
  pricing: {
    model: 'free' | 'usage-based' | 'subscription';
    rate?: number;                     // Price per unit
    unit?: string;                     // e.g., "per calculation", "per month"
    currency: string;                  // e.g., "EUR", "USD"
  };
  repository: string;                  // GitHub URL
  manifest_url: string;                // Agent manifest URL
  screenshots?: string[];              // Screenshot URLs
  tags: string[];                      // e.g., ["math", "finance", "education"]
  industries: string[];                // e.g., ["finance", "healthcare"]
  use_cases: string[];                 // e.g., ["invoice processing"]
  frequently_used_with: string[];      // Agent/App IDs
  visibility: 'public' | 'team' | 'project' | 'organization';
  status: 'active' | 'inactive' | 'deprecated';
  created_at: string;
  updated_at: string;
}

interface AppRegistration {
  app_id: string;                      // e.g., "app.company.email-manager"
  name: string;                        // e.g., "Email Manager"
  description: string;                 // What it does
  creator: {
    id: string;
    name: string;
    type: 'user' | 'organization' | 'team';
  };
  orchestrator_manifest_url: string;   // Orchestrator manifest URL
  pricing: {
    model: 'free' | 'subscription';
    rate?: number;
    currency: string;
  };
  repository: string;                  // GitHub URL
  screenshots?: string[];
  tags: string[];
  industries: string[];
  use_cases: string[];
  frequently_used_with: string[];      // Agent/App IDs
  visibility: 'public' | 'team' | 'project' | 'organization';
  status: 'active' | 'inactive' | 'deprecated';
  created_at: string;
  updated_at: string;
}
```

---

### **2. Ratings & Reviews**

**Rating System:**
- Scale: 1-10 (integer)
- Users can rate agents/apps they've used
- Average rating displayed
- Review text (optional)

```typescript
interface Rating {
  id: string;
  entity_type: 'agent' | 'app';
  entity_id: string;                   // Agent or App ID
  user_id: string;                     // Rater ID
  rating: number;                      // 1-10
  review?: string;                     // Optional review text
  created_at: string;
}
```

---

### **3. Visibility & Access Control**

**Visibility Levels:**

| Level | Description | Who Can See |
|-------|-------------|-------------|
| `public` | Everyone | All users |
| `organization` | Organization only | Members of the creator's organization |
| `team` | Team only | Members of the creator's team |
| `project` | Project only | Members of the specific project |

**Implementation:**
- Row-level security in Supabase
- CoreSense IAM for authentication
- Organization/Team/Project membership checks

---

### **4. Search & Discovery**

**Search Capabilities:**

1. **By Name**: Full-text search on name and description
2. **By Tags**: Filter by tags (e.g., "math", "email")
3. **By Capability**: Find agents with specific capabilities
4. **By Industry**: Filter by industry (e.g., "finance")
5. **By Use Case**: Filter by use case (e.g., "invoice processing")
6. **By Rating**: Filter by minimum rating
7. **By Price**: Filter by pricing model or max price

**Search API:**

```typescript
interface SearchRequest {
  query?: string;                      // Text search
  tags?: string[];                     // Filter by tags
  capabilities?: string[];             // Filter by capabilities
  industries?: string[];               // Filter by industries
  use_cases?: string[];                // Filter by use cases
  min_rating?: number;                 // Minimum rating
  max_price?: number;                  // Maximum price
  pricing_model?: 'free' | 'usage-based' | 'subscription';
  entity_type?: 'agent' | 'app';       // Filter by type
  visibility?: 'public' | 'organization' | 'team' | 'project';
}

interface SearchResponse {
  results: (AgentRegistration | AppRegistration)[];
  total: number;
  page: number;
  per_page: number;
}
```

---

### **5. Active Agents Display**

**Real-time Status:**
- Show which agents are currently active/running
- Display agent health status
- Show current load/usage
- Indicate availability

```typescript
interface AgentStatus {
  agent_id: string;
  status: 'active' | 'inactive' | 'busy' | 'error';
  last_heartbeat: string;              // ISO timestamp
  current_load: number;                // 0-100%
  availability: number;                // 0-100%
  instances: number;                   // Number of running instances
}
```

---

### **6. Billing & Usage Tracking**

**Billing Features:**
- Track usage per agent/app
- Generate invoices
- Support multiple pricing models
- Integration with payment providers (Stripe)

```typescript
interface UsageRecord {
  id: string;
  entity_type: 'agent' | 'app';
  entity_id: string;
  user_id: string;
  organization_id?: string;
  usage_count: number;                 // Number of calls/uses
  cost: number;                        // Total cost
  currency: string;
  period_start: string;
  period_end: string;
  created_at: string;
}

interface Invoice {
  id: string;
  user_id: string;
  organization_id?: string;
  total_amount: number;
  currency: string;
  status: 'pending' | 'paid' | 'overdue';
  line_items: {
    entity_type: 'agent' | 'app';
    entity_id: string;
    entity_name: string;
    usage_count: number;
    unit_price: number;
    total: number;
  }[];
  period_start: string;
  period_end: string;
  due_date: string;
  created_at: string;
}
```

---

### **7. Authentication & IAM**

**Default IAM Provider: CoreSense**

**Authentication Flow:**
1. User logs in via CoreSense
2. CoreSense returns JWT token
3. Token includes user ID, organization ID, team IDs, project IDs
4. Marketplace validates token for all requests
5. Row-level security enforces visibility rules

**Required Environment Variables:**
```env
VITE_CORESENSE_URL=https://iam.meet-harmony.ai
VITE_CORESENSE_CLIENT_ID=marketplace-client-id
VITE_CORESENSE_CLIENT_SECRET=marketplace-client-secret
```

**Integration:**
```typescript
import { CoreSenseAuth } from '@meet-harmony/coresense-sdk';

const auth = new CoreSenseAuth({
  url: process.env.VITE_CORESENSE_URL,
  clientId: process.env.VITE_CORESENSE_CLIENT_ID,
  clientSecret: process.env.VITE_CORESENSE_CLIENT_SECRET,
});

// Login
const { token, user } = await auth.login(email, password);

// Validate token
const { valid, user } = await auth.validateToken(token);
```

---

## 📊 **Database Schema**

See: `platform/agentify/marketplace/SCHEMA.md`

---

## 🔗 **API Endpoints**

See: `platform/agentify/marketplace/API.md`

---

## 📚 **References**

- **Agent Standard**: https://github.com/your-org/agentify/blob/main/platform/agentify/agent_standard/AGENT_STANDARD.md
- **App Standard**: https://github.com/your-org/agentify/blob/main/platform/agentify/app_standard/README.md
- **Agent Communication**: https://github.com/your-org/agentify/blob/main/platform/agentify/agent_standard/COMMUNICATION.md
- **Architecture**: https://github.com/your-org/agentify/blob/main/platform/agentify/ARCHITECTURE.md

---

**Next:** See `LOVABLE_PROMPT.md` for complete Lovable prompt to build this marketplace.

