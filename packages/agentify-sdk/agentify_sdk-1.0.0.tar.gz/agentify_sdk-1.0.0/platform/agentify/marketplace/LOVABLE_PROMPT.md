# 🏪 Agentify Marketplace - Lovable Prompt

**Copy this complete prompt into Lovable to generate the Agentify Marketplace**

---

```
Create a complete Agentify Marketplace application following the Agentify standards.

## App Details
- App Name: Agentify Marketplace
- App ID: app.meet-harmony.marketplace
- Description: Central discovery and distribution platform for Agentify apps and agents
- URL: marketplace.meet-harmony.ai

## Architecture Standards

This app MUST follow the Agentify standards documented here:
- **Agent Standard**: https://github.com/your-org/agentify/blob/main/platform/agentify/agent_standard/AGENT_STANDARD.md
- **App Standard**: https://github.com/your-org/agentify/blob/main/platform/agentify/app_standard/README.md
- **Communication Standard**: https://github.com/your-org/agentify/blob/main/platform/agentify/agent_standard/COMMUNICATION.md
- **Authentication Standard**: https://github.com/your-org/agentify/blob/main/platform/agentify/agent_standard/AUTHENTICATION.md
- **Architecture**: https://github.com/your-org/agentify/blob/main/platform/agentify/ARCHITECTURE.md

## Technology Stack
- Framework: Vite + React 18+ (TypeScript)
- Styling: Tailwind CSS
- UI Components: shadcn/ui
- Icons: Lucide React
- State Management: Zustand
- Routing: React Router v6
- Database: Supabase (PostgreSQL)
- Auth: CoreSense IAM (https://iam.meet-harmony.ai)
- Logging: Supabase (logs table)
- HTTP Client: Axios

## Core Features

### 1. Agent & App Registration

Create registration forms for:

**Agent Registration:**
- Agent ID (e.g., "agent.company.calculator")
- Name
- Description (rich text editor)
- Creator (auto-filled from logged-in user)
- Capabilities (multi-select tags)
- Pricing:
  - Model: free | usage-based | subscription
  - Rate (number)
  - Unit (text, e.g., "per calculation")
  - Currency (dropdown: EUR, USD, GBP)
- Repository URL (GitHub)
- Manifest URL
- Screenshots (file upload, multiple)
- Tags (multi-select, autocomplete)
- Industries (multi-select: finance, healthcare, education, etc.)
- Use Cases (multi-select)
- Frequently Used With (search other agents/apps)
- Visibility: public | organization | team | project
- Status: active | inactive | deprecated

**App Registration:**
- Same fields as Agent, but with:
  - Orchestrator Manifest URL instead of Agent Manifest URL
  - Pricing: free | subscription (no usage-based)

### 2. Search & Discovery

Create a powerful search interface:

**Search Bar:**
- Full-text search on name and description
- Real-time search results
- Search suggestions

**Filters (Sidebar):**
- Entity Type: All | Agents | Apps
- Tags (multi-select with checkboxes)
- Capabilities (multi-select)
- Industries (multi-select)
- Use Cases (multi-select)
- Pricing Model: All | Free | Usage-Based | Subscription
- Max Price (slider)
- Min Rating (slider, 1-10)
- Visibility: All | Public | Organization | Team | Project

**Results Display:**
- Grid view (cards) or List view (toggle)
- Each card shows:
  - Name
  - Description (truncated)
  - Creator name
  - Rating (stars, 1-10 scale)
  - Price
  - Tags (first 3)
  - Screenshot (first one)
  - "View Details" button

**Sorting:**
- Relevance (default)
- Rating (high to low)
- Price (low to high)
- Recently Added
- Most Used

### 3. Agent/App Detail Page

When clicking on an agent/app, show:

**Header:**
- Name
- Creator name and logo
- Rating (stars + number)
- Price
- Status badge (active/inactive/deprecated)
- "Use This Agent/App" button

**Tabs:**
1. **Overview**
   - Full description
   - Screenshots (carousel)
   - Tags
   - Industries
   - Use Cases
   - Frequently Used With (clickable links)

2. **Manifest**
   - Display manifest JSON (syntax highlighted)
   - Link to manifest URL
   - "Copy Manifest" button

3. **Ratings & Reviews**
   - Average rating (large display)
   - Rating distribution (bar chart)
   - List of reviews:
     - User name
     - Rating (stars)
     - Review text
     - Date
   - "Write a Review" button (if user has used this agent/app)

4. **Usage & Billing**
   - Current usage (if user has used it)
   - Cost this month
   - Usage chart (last 30 days)

5. **Documentation**
   - Link to repository
   - README content (fetched from GitHub)

### 4. Ratings & Reviews

**Write Review Form:**
- Rating (1-10, star selector)
- Review text (textarea, optional)
- Submit button

**Display Reviews:**
- Sort by: Most Recent | Highest Rating | Lowest Rating
- Pagination (10 per page)

### 5. Active Agents Display

Create a "Live Status" page showing:

**Active Agents Table:**
- Agent Name
- Status (active/inactive/busy/error) with color-coded badge
- Last Heartbeat (time ago)
- Current Load (progress bar, 0-100%)
- Availability (percentage)
- Running Instances (number)
- "View Details" button

**Real-time Updates:**
- Use Supabase Realtime to update status every 5 seconds
- Show "Last updated: X seconds ago"

### 6. User Dashboard

Create a dashboard for logged-in users:

**My Agents & Apps:**
- List of agents/apps created by user
- Quick stats: Total views, Total uses, Total revenue
- "Create New Agent" button
- "Create New App" button

**My Usage:**
- List of agents/apps used this month
- Usage count
- Cost
- "View Invoice" button

**My Reviews:**
- List of reviews written by user
- Edit/Delete buttons

### 7. Billing & Invoices

**Invoices Page:**
- List of invoices (table)
- Columns: Invoice #, Period, Total, Status, Due Date
- Filter by: Status (All | Pending | Paid | Overdue)
- "Download PDF" button for each invoice

**Invoice Detail:**
- Invoice header (number, date, due date)
- Line items table:
  - Agent/App Name
  - Usage Count
  - Unit Price
  - Total
- Subtotal
- Tax (if applicable)
- Total
- Payment status
- "Pay Now" button (if pending)

### 8. Authentication (CoreSense)

Implement CoreSense authentication:

**Login Page:**
- Email input
- Password input
- "Login" button
- "Forgot Password" link
- "Sign Up" link

**Sign Up Page:**
- Name
- Email
- Password
- Confirm Password
- Organization (optional, create new or join existing)
- "Sign Up" button

**Authentication Flow:**
1. User logs in via CoreSense
2. CoreSense returns JWT token
3. Store token in localStorage
4. Include token in all API requests (Authorization header)
5. Validate token on every request

**Protected Routes:**
- Dashboard
- Create Agent/App
- Write Review
- Billing

**Environment Variables:**
```env
VITE_CORESENSE_URL=https://iam.meet-harmony.ai
VITE_CORESENSE_CLIENT_ID=marketplace-client-id
VITE_CORESENSE_CLIENT_SECRET=marketplace-client-secret
```

### 9. Orchestrator Agent

Create a built-in orchestrator agent at `src/agents/orchestrator/`:

**Responsibilities:**
- Manage marketplace operations
- Validate agent/app registrations
- Calculate ratings
- Generate invoices
- Send notifications

**Manifest** (`src/agents/orchestrator/manifest.json`):
```json
{
  "agent_id": "agent.marketplace.orchestrator",
  "name": "Marketplace Orchestrator",
  "version": "1.0.0",
  "status": "active",
  "capabilities": ["orchestration", "validation", "billing"],
  "authentication": {
    "required": true,
    "provider": "coresense",
    "provider_url": "https://iam.meet-harmony.ai"
  },
  "tools": [
    {
      "name": "validate_registration",
      "description": "Validate agent/app registration data"
    },
    {
      "name": "calculate_rating",
      "description": "Calculate average rating"
    },
    {
      "name": "generate_invoice",
      "description": "Generate monthly invoice"
    }
  ]
}
```

## Database Schema (Supabase)

Create these tables:

### agents
```sql
CREATE TABLE agents (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  agent_id TEXT UNIQUE NOT NULL,
  name TEXT NOT NULL,
  description TEXT,
  creator_id UUID REFERENCES auth.users(id),
  creator_name TEXT,
  creator_type TEXT CHECK (creator_type IN ('user', 'organization', 'team')),
  capabilities TEXT[],
  pricing_model TEXT CHECK (pricing_model IN ('free', 'usage-based', 'subscription')),
  pricing_rate DECIMAL,
  pricing_unit TEXT,
  pricing_currency TEXT,
  repository TEXT,
  manifest_url TEXT,
  screenshots TEXT[],
  tags TEXT[],
  industries TEXT[],
  use_cases TEXT[],
  frequently_used_with TEXT[],
  visibility TEXT CHECK (visibility IN ('public', 'organization', 'team', 'project')),
  status TEXT CHECK (status IN ('active', 'inactive', 'deprecated')),
  average_rating DECIMAL DEFAULT 0,
  total_ratings INTEGER DEFAULT 0,
  total_uses INTEGER DEFAULT 0,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX agents_agent_id_idx ON agents(agent_id);
CREATE INDEX agents_creator_id_idx ON agents(creator_id);
CREATE INDEX agents_tags_idx ON agents USING GIN(tags);
CREATE INDEX agents_capabilities_idx ON agents USING GIN(capabilities);
```

### apps
```sql
CREATE TABLE apps (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  app_id TEXT UNIQUE NOT NULL,
  name TEXT NOT NULL,
  description TEXT,
  creator_id UUID REFERENCES auth.users(id),
  creator_name TEXT,
  creator_type TEXT CHECK (creator_type IN ('user', 'organization', 'team')),
  orchestrator_manifest_url TEXT,
  pricing_model TEXT CHECK (pricing_model IN ('free', 'subscription')),
  pricing_rate DECIMAL,
  pricing_currency TEXT,
  repository TEXT,
  screenshots TEXT[],
  tags TEXT[],
  industries TEXT[],
  use_cases TEXT[],
  frequently_used_with TEXT[],
  visibility TEXT CHECK (visibility IN ('public', 'organization', 'team', 'project')),
  status TEXT CHECK (status IN ('active', 'inactive', 'deprecated')),
  average_rating DECIMAL DEFAULT 0,
  total_ratings INTEGER DEFAULT 0,
  total_uses INTEGER DEFAULT 0,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### ratings
```sql
CREATE TABLE ratings (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  entity_type TEXT CHECK (entity_type IN ('agent', 'app')),
  entity_id TEXT NOT NULL,
  user_id UUID REFERENCES auth.users(id),
  rating INTEGER CHECK (rating >= 1 AND rating <= 10),
  review TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  UNIQUE(entity_type, entity_id, user_id)
);
```

### usage_records
```sql
CREATE TABLE usage_records (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  entity_type TEXT CHECK (entity_type IN ('agent', 'app')),
  entity_id TEXT NOT NULL,
  user_id UUID REFERENCES auth.users(id),
  organization_id UUID,
  usage_count INTEGER DEFAULT 1,
  cost DECIMAL,
  currency TEXT,
  period_start TIMESTAMP WITH TIME ZONE,
  period_end TIMESTAMP WITH TIME ZONE,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### invoices
```sql
CREATE TABLE invoices (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  invoice_number TEXT UNIQUE NOT NULL,
  user_id UUID REFERENCES auth.users(id),
  organization_id UUID,
  total_amount DECIMAL,
  currency TEXT,
  status TEXT CHECK (status IN ('pending', 'paid', 'overdue')),
  line_items JSONB,
  period_start TIMESTAMP WITH TIME ZONE,
  period_end TIMESTAMP WITH TIME ZONE,
  due_date TIMESTAMP WITH TIME ZONE,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### agent_status
```sql
CREATE TABLE agent_status (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  agent_id TEXT NOT NULL,
  status TEXT CHECK (status IN ('active', 'inactive', 'busy', 'error')),
  last_heartbeat TIMESTAMP WITH TIME ZONE,
  current_load INTEGER CHECK (current_load >= 0 AND current_load <= 100),
  availability INTEGER CHECK (availability >= 0 AND availability <= 100),
  instances INTEGER DEFAULT 0,
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### logs
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

## Row-Level Security (RLS)

Enable RLS on all tables and create policies:

```sql
-- Agents: Public can read public agents, creators can manage their own
ALTER TABLE agents ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Public agents are viewable by everyone" ON agents
  FOR SELECT USING (visibility = 'public');

CREATE POLICY "Users can view their organization's agents" ON agents
  FOR SELECT USING (
    visibility = 'organization' AND 
    creator_id IN (SELECT id FROM auth.users WHERE organization_id = auth.jwt()->>'organization_id')
  );

CREATE POLICY "Creators can insert their own agents" ON agents
  FOR INSERT WITH CHECK (auth.uid() = creator_id);

CREATE POLICY "Creators can update their own agents" ON agents
  FOR UPDATE USING (auth.uid() = creator_id);

-- Similar policies for apps, ratings, etc.
```

## Project Structure
```
marketplace/
├── public/
│   └── agentify.json              # App manifest
├── src/
│   ├── agents/
│   │   └── orchestrator/
│   │       ├── manifest.json
│   │       ├── orchestrator.ts
│   │       └── tools/
│   ├── components/
│   │   ├── layout/
│   │   │   ├── Header.tsx
│   │   │   ├── Sidebar.tsx
│   │   │   └── Footer.tsx
│   │   ├── agents/
│   │   │   ├── AgentCard.tsx
│   │   │   ├── AgentDetail.tsx
│   │   │   ├── AgentForm.tsx
│   │   │   └── AgentList.tsx
│   │   ├── apps/
│   │   │   ├── AppCard.tsx
│   │   │   ├── AppDetail.tsx
│   │   │   ├── AppForm.tsx
│   │   │   └── AppList.tsx
│   │   ├── search/
│   │   │   ├── SearchBar.tsx
│   │   │   ├── Filters.tsx
│   │   │   └── Results.tsx
│   │   ├── ratings/
│   │   │   ├── RatingDisplay.tsx
│   │   │   ├── ReviewForm.tsx
│   │   │   └── ReviewList.tsx
│   │   ├── billing/
│   │   │   ├── InvoiceList.tsx
│   │   │   ├── InvoiceDetail.tsx
│   │   │   └── UsageChart.tsx
│   │   ├── auth/
│   │   │   ├── LoginForm.tsx
│   │   │   └── SignUpForm.tsx
│   │   └── ui/                    # shadcn/ui components
│   ├── pages/
│   │   ├── Home.tsx
│   │   ├── Search.tsx
│   │   ├── AgentDetail.tsx
│   │   ├── AppDetail.tsx
│   │   ├── Dashboard.tsx
│   │   ├── CreateAgent.tsx
│   │   ├── CreateApp.tsx
│   │   ├── Billing.tsx
│   │   ├── LiveStatus.tsx
│   │   ├── Login.tsx
│   │   └── SignUp.tsx
│   ├── services/
│   │   ├── database.ts            # Supabase client
│   │   ├── auth.ts                # CoreSense auth
│   │   ├── logger.ts              # Logging service
│   │   ├── orchestrator.ts        # Orchestrator service
│   │   └── api.ts                 # API client
│   ├── stores/
│   │   ├── authStore.ts           # Auth state
│   │   ├── searchStore.ts         # Search state
│   │   └── agentStore.ts          # Agent/App state
│   ├── types/
│   │   ├── agent.ts
│   │   ├── app.ts
│   │   ├── rating.ts
│   │   ├── billing.ts
│   │   └── auth.ts
│   ├── App.tsx
│   ├── main.tsx
│   └── index.css
├── .env.example
├── package.json
├── vite.config.ts
├── tailwind.config.js
└── tsconfig.json
```

## Environment Variables (.env.example)
```env
# App
VITE_APP_ID=app.meet-harmony.marketplace
VITE_APP_NAME=Agentify Marketplace

# Supabase
VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_ANON_KEY=your-anon-key

# CoreSense IAM
VITE_CORESENSE_URL=https://iam.meet-harmony.ai
VITE_CORESENSE_CLIENT_ID=marketplace-client-id
VITE_CORESENSE_CLIENT_SECRET=marketplace-client-secret

# Marketplace
VITE_MARKETPLACE_URL=https://marketplace.meet-harmony.ai
```

## Design Requirements

- Modern, clean UI with Tailwind CSS
- Responsive design (mobile-first)
- Dark mode support
- Accessible (ARIA labels, keyboard navigation)
- Fast loading (code splitting, lazy loading)
- SEO-friendly (meta tags, sitemap)

## Additional Requirements

- Use TypeScript for all files
- Include proper error handling
- Add loading states for async operations
- Include form validation
- Follow Agentify App Standard v1
- Implement CoreSense authentication
- Use Supabase for data and logging
- Include orchestrator agent
- Add comprehensive comments

## Expected Output

Generate a complete, working Agentify Marketplace with:
- All files in the project structure
- Working authentication (CoreSense)
- Agent/App registration and search
- Ratings and reviews
- Billing and invoices
- Live agent status
- User dashboard
- Orchestrator agent
- Supabase integration
- Proper TypeScript types
- Tailwind CSS styling
- shadcn/ui components

The app should be ready to run with `npm install && npm run dev`.
```

---

**Next Steps:**
1. Copy this prompt
2. Paste into Lovable
3. Wait for generation
4. Add Supabase credentials
5. Add CoreSense credentials
6. Run `npm install && npm run dev`
7. Test all features

