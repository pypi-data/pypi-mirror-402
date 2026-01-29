# 🎯 Agentify Orchestrator Agent

**Every app's built-in team builder and manager**

---

## 🎯 **What is an Orchestrator?**

Every Agentify app includes an **orchestrator agent** that:

- 🔍 **Discovers Agents** - Queries marketplace for capabilities
- 🤝 **Builds Teams** - LLM-guided team selection
- 👤 **Human-in-the-Loop** - User approval before booking
- 📊 **Manages Teams** - Monitors health, scales, handles failures
- 💰 **Optimizes Costs** - Balances capability and price
- 📝 **Logs Everything** - All activities logged (Agent Standard)

---

## 🏗️ **Architecture**

```
┌─────────────────────────────────────────────────────────────┐
│                  Orchestrator Agent                          │
│              (Agent Standard v1 Compliant)                   │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │         Requirement Analyzer                         │  │
│  │  - Parse user/app requirements                       │  │
│  │  - Identify needed capabilities                      │  │
│  │  - Determine budget constraints                      │  │
│  └──────────────┬───────────────────────────────────────┘  │
│                 │                                           │
│  ┌──────────────▼──────────┐  ┌──────────────────────┐    │
│  │  Team Discovery         │  │  LLM Recommender     │    │
│  │  - Query Marketplace    │  │  - Analyze Options   │    │
│  │  - Filter Agents        │  │  - Suggest Teams     │    │
│  └──────────────┬──────────┘  └──────┬───────────────┘    │
│                 │                     │                     │
│  ┌──────────────▼─────────────────────▼──────────────┐    │
│  │         Human-in-the-Loop Review                  │    │
│  │  - Present options to user                        │    │
│  │  - Get approval before booking                    │    │
│  └──────────────┬────────────────────────────────────┘    │
│                 │                                           │
│  ┌──────────────▼──────────┐  ┌──────────────────────┐    │
│  │  Team Builder           │  │  Team Manager        │    │
│  │  - Book Agents          │  │  - Monitor Health    │    │
│  │  - Initialize Team      │  │  - Scale Team        │    │
│  └─────────────────────────┘  └──────────────────────┘    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 📄 **Orchestrator Manifest**

Every orchestrator is an **Agent Standard v1 compliant agent**:

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
      "no_budget_overrun",
      "no_unreviewed_bookings"
    ],
    "soft_constraints": [
      "prefer_verified_creators",
      "prefer_high_rated_agents"
    ]
  },
  
  "desires": {
    "profile": [
      {"id": "team_efficiency", "weight": 0.4},
      {"id": "cost_optimization", "weight": 0.3},
      {"id": "user_satisfaction", "weight": 0.3}
    ],
    "health_signals": {
      "tension_thresholds": {
        "stressed": 0.55,
        "degraded": 0.75,
        "critical": 0.90
      }
    }
  },
  
  "tools": [
    {
      "name": "query_marketplace",
      "description": "Query marketplace for agents by capability",
      "category": "discovery",
      "executor": "agents.orchestrator.tools.MarketplaceQuery",
      "input_schema": {
        "type": "object",
        "properties": {
          "capabilities": {"type": "array", "items": {"type": "string"}},
          "maxPrice": {"type": "number"},
          "minRating": {"type": "number"}
        },
        "required": ["capabilities"]
      }
    },
    {
      "name": "recommend_team",
      "description": "Get LLM-guided team recommendations",
      "category": "orchestration",
      "executor": "agents.orchestrator.tools.TeamRecommender",
      "input_schema": {
        "type": "object",
        "properties": {
          "requirements": {"type": "string"},
          "budget": {"type": "number"}
        },
        "required": ["requirements"]
      }
    },
    {
      "name": "build_team",
      "description": "Build team from selected agents",
      "category": "orchestration",
      "executor": "agents.orchestrator.tools.TeamBuilder",
      "input_schema": {
        "type": "object",
        "properties": {
          "agents": {"type": "array"},
          "approved": {"type": "boolean"}
        },
        "required": ["agents", "approved"]
      }
    },
    {
      "name": "monitor_team",
      "description": "Monitor team health and performance",
      "category": "monitoring",
      "executor": "agents.orchestrator.tools.TeamMonitor"
    }
  ],
  
  "authority": {
    "instruction": {"type": "app", "id": "app.{APP_ID}"},
    "oversight": {"type": "human", "id": "user", "independent": true},
    "escalation": {
      "channels": ["human", "system"],
      "auto_escalate_on": [
        "budget_overrun",
        "team_health_critical",
        "ethics_violation"
      ]
    }
  }
}
```

---

## 🔧 **Core Capabilities**

### **1. Requirement Analysis**

Parse user/app requirements:

```typescript
interface Requirements {
  description: string;           // Natural language description
  capabilities: string[];        // Required capabilities
  budget?: number;               // Max budget
  duration?: string;             // Team duration (e.g., "30d")
  preferences?: {
    verified_creators_only?: boolean;
    min_rating?: number;
    max_price_per_action?: number;
  };
}

async analyzeRequirements(input: string): Promise<Requirements> {
  // Use LLM to parse natural language
  const requirements = await this.llm.parse(input);
  return requirements;
}
```

**Example:**

```typescript
const input = "I need to automate email campaigns with scheduling and analytics. Budget is $100/month.";

const requirements = await orchestrator.analyzeRequirements(input);
// {
//   description: "Automate email campaigns with scheduling and analytics",
//   capabilities: ["email_sending", "scheduling", "analytics"],
//   budget: 100,
//   duration: "30d"
// }
```

---

### **2. Team Discovery**

Query marketplace for agents:

```typescript
async queryMarketplace(requirements: Requirements): Promise<Agent[]> {
  const response = await fetch('https://marketplace.agentify.io/api/search', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      requirements: {
        capabilities: requirements.capabilities,
        max_price_per_action: requirements.preferences?.max_price_per_action,
        min_rating: requirements.preferences?.min_rating || 7.0
      }
    })
  });
  
  return response.json();
}
```

---

### **3. LLM-Guided Recommendations**

Get team recommendations:

```typescript
async recommendTeam(requirements: Requirements): Promise<TeamRecommendation[]> {
  // Query marketplace
  const agents = await this.queryMarketplace(requirements);
  
  // Use LLM to recommend teams
  const prompt = `
    Given these requirements: ${requirements.description}
    Budget: $${requirements.budget}
    
    Available agents:
    ${JSON.stringify(agents, null, 2)}
    
    Recommend the best team composition. Consider:
    - Coverage of all required capabilities
    - Cost optimization
    - Agent ratings and reliability
    - Team synergy
  `;
  
  const recommendations = await this.llm.complete(prompt);
  return recommendations;
}
```

**Example Response:**

```json
{
  "recommendations": [
    {
      "team_id": "team-rec-001",
      "agents": [
        {
          "agent_id": "agent.company.email-sender",
          "role": "Email Sending",
          "estimated_cost": 30.00,
          "rating": 8.7
        },
        {
          "agent_id": "agent.company.scheduler",
          "role": "Campaign Scheduling",
          "estimated_cost": 25.00,
          "rating": 9.1
        },
        {
          "agent_id": "agent.company.analytics",
          "role": "Campaign Analytics",
          "estimated_cost": 40.00,
          "rating": 8.5
        }
      ],
      "total_cost": 95.00,
      "confidence": 0.92,
      "reasoning": "This team covers all requirements within budget. High ratings and proven track record."
    }
  ]
}
```

---

### **4. Human-in-the-Loop Review**

Present options to user for approval:

```typescript
async requestHumanApproval(recommendations: TeamRecommendation[]): Promise<boolean> {
  // Display recommendations to user
  const approved = await this.ui.showApprovalDialog({
    title: "Review Team Recommendations",
    recommendations,
    actions: ["Approve", "Reject", "Modify"]
  });
  
  // Log decision (Agent Standard)
  await this.logActivity({
    action: "human_approval",
    input: recommendations,
    output: { approved },
    timestamp: new Date().toISOString()
  });
  
  return approved;
}
```

---

### **5. Team Building**

Book agents and initialize team:

```typescript
async buildTeam(recommendation: TeamRecommendation, approved: boolean): Promise<Team> {
  // Ethics check: Must be approved
  if (!approved) {
    throw new Error('Team building requires human approval');
  }
  
  // Book agents via marketplace
  const bookings = await Promise.all(
    recommendation.agents.map(agent =>
      this.marketplace.bookAgent(agent.agent_id, this.teamId)
    )
  );
  
  // Initialize team
  const team = {
    team_id: this.teamId,
    agents: recommendation.agents,
    status: 'active',
    created_at: new Date().toISOString()
  };
  
  // Log activity (Agent Standard)
  await this.logActivity({
    action: "team_built",
    input: recommendation,
    output: team,
    timestamp: new Date().toISOString()
  });
  
  return team;
}
```

---

### **6. Team Management**

Monitor and manage team:

```typescript
async monitorTeam(): Promise<TeamHealth> {
  const health = {
    team_id: this.teamId,
    agents: await Promise.all(
      this.team.agents.map(async agent => ({
        agent_id: agent.agent_id,
        status: await this.checkAgentHealth(agent.agent_id),
        last_activity: await this.getLastActivity(agent.agent_id)
      }))
    ),
    overall_health: 'healthy'
  };
  
  // Auto-escalate if critical
  if (health.overall_health === 'critical') {
    await this.escalate({
      severity: 'critical',
      reason: 'Team health critical',
      team_health: health
    });
  }
  
  return health;
}
```

---

## 📊 **Lifecycle Management**

### **Team Lifecycle:**

```
1. Requirements Analysis
   ↓
2. Discovery (Query Marketplace)
   ↓
3. LLM Recommendations
   ↓
4. Human-in-the-Loop Review
   ↓
5. Team Building (Book Agents)
   ↓
6. Team Active (Monitor Health)
   ↓
7. Scale/Update (Add/Remove Agents)
   ↓
8. Team Termination (Unbook Agents)
```

---

## 🔒 **Ethics & Compliance**

All orchestrators enforce:

- ✅ **No unauthorized team changes** - Human approval required
- ✅ **No budget overruns** - Cost checks before booking
- ✅ **No unreviewed bookings** - Human-in-the-loop mandatory
- ✅ **All activities logged** - Agent Standard compliance

---

## 📚 **Examples**

See [examples/](examples/) for:
- Basic orchestrator implementation
- LLM-guided team building
- Human-in-the-loop workflow
- Team monitoring and scaling

---

**Next:** [Implementation Guide](IMPLEMENTATION.md) - Build your orchestrator

