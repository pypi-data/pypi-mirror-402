# 🏪 Agentify Marketplace

**Central hub for agent discovery, acquisition, and team building**

**URL**: marketplace.meet-harmony.ai

---

## 🎯 **What is the Marketplace?**

The Agentify Marketplace is a **system default app** that enables:

- 🔍 **Agent Discovery** - Find agents by capability, price, rating
- 💰 **Pricing & Billing** - Transparent pricing and automatic revenue sharing
- ⭐ **Trust & Ratings** - Community ratings (1-10) and creator verification
- 🤝 **Team Building** - LLM-guided team recommendations
- 📊 **Analytics** - Usage tracking and performance metrics
- 🔐 **Authentication** - CoreSense IAM integration (https://iam.meet-harmony.ai)

**Default Marketplace**: All Agentify agents and apps use `marketplace.meet-harmony.ai` as their default discovery service.

---

## 🏗️ **Architecture**

```
┌─────────────────────────────────────────────────────────────┐
│                  Marketplace App                             │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │         Marketplace Orchestrator Agent               │  │
│  │  (Discovery, Team Matching, Billing)                 │  │
│  └──────────────┬───────────────────────────────────────┘  │
│                 │                                           │
│  ┌──────────────▼──────────┐  ┌──────────────────────┐    │
│  │  Discovery Service      │  │  Billing Service     │    │
│  │  - Agent Registry       │  │  - Usage Tracking    │    │
│  │  - Search & Filter      │  │  - Revenue Sharing   │    │
│  └─────────────────────────┘  └──────────────────────┘    │
│                                                             │
│  ┌─────────────────────────┐  ┌──────────────────────┐    │
│  │  Rating Service         │  │  Creator Service     │    │
│  │  - User Ratings         │  │  - Verification      │    │
│  │  - Reviews              │  │  - Creator Profiles  │    │
│  └─────────────────────────┘  └──────────────────────┘    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 🤖 **Marketplace Orchestrator**

The Marketplace has its own orchestrator agent with specialized capabilities:

### **Orchestrator Manifest:**

```json
{
  "agent_id": "agent.marketplace.orchestrator",
  "name": "Marketplace Orchestrator",
  "version": "1.0.0",
  "status": "active",
  "ethics": {
    "framework": "harm-minimization",
    "hard_constraints": [
      "no_price_manipulation",
      "no_fake_ratings",
      "no_unauthorized_billing"
    ]
  },
  "desires": {
    "profile": [
      {"id": "fair_pricing", "weight": 0.4},
      {"id": "quality_agents", "weight": 0.3},
      {"id": "user_satisfaction", "weight": 0.3}
    ]
  },
  "tools": [
    {
      "name": "search_agents",
      "description": "Search agents by capability, price, rating",
      "category": "discovery"
    },
    {
      "name": "recommend_team",
      "description": "LLM-guided team recommendations",
      "category": "orchestration"
    },
    {
      "name": "calculate_billing",
      "description": "Calculate costs and revenue sharing",
      "category": "billing"
    }
  ]
}
```

---

## 🔍 **Agent Discovery**

### **Agent Registration**

Agents register with the marketplace:

```json
{
  "agent_id": "agent.company.email-sender",
  "name": "Email Sender Pro",
  "version": "2.1.0",
  "description": "Professional email sending with SMTP and API support",
  "creator": {
    "id": "creator-123",
    "name": "Acme Corp",
    "email": "dev@acme.com",
    "verified": true
  },
  "capabilities": [
    {
      "name": "email_sending",
      "level": "high",
      "description": "Send emails via SMTP or API"
    },
    {
      "name": "template_rendering",
      "level": "medium",
      "description": "Render email templates"
    }
  ],
  "pricing": {
    "model": "usage-based",
    "currency": "USD",
    "rates": {
      "per_email": 0.01,
      "per_month": 10.00
    }
  },
  "rating": {
    "average": 8.7,
    "count": 142,
    "distribution": {
      "10": 45,
      "9": 38,
      "8": 32,
      "7": 15,
      "6": 8,
      "5": 4
    }
  },
  "repository": "https://github.com/acme/email-sender",
  "manifest_url": "https://github.com/acme/email-sender/manifest.json",
  "documentation_url": "https://docs.acme.com/email-sender"
}
```

### **Search API**

```typescript
// POST /api/marketplace/search
{
  "requirements": {
    "capabilities": ["email_sending", "scheduling"],
    "max_price_per_action": 0.05,
    "min_rating": 7.0,
    "verified_creators_only": true
  },
  "filters": {
    "tags": ["email", "marketing"],
    "exclude_agents": ["agent.old.email-sender"]
  },
  "sort": {
    "by": "rating",  // rating, price, popularity
    "order": "desc"
  },
  "pagination": {
    "page": 1,
    "per_page": 20
  }
}

// Response
{
  "agents": [
    {
      "agent_id": "agent.company.email-sender",
      "name": "Email Sender Pro",
      "rating": 8.7,
      "price": 0.01,
      "capabilities": ["email_sending", "template_rendering"]
    }
  ],
  "total": 15,
  "page": 1,
  "per_page": 20
}
```

---

## 🤝 **Team Building**

### **LLM-Guided Recommendations**

The Marketplace Orchestrator uses LLM to recommend teams:

```typescript
// POST /api/marketplace/recommend-team
{
  "requirements": {
    "description": "I need to automate email campaigns with scheduling and analytics",
    "budget": 100.00,
    "duration": "30d"
  }
}

// Response
{
  "recommendations": [
    {
      "team_id": "team-rec-001",
      "agents": [
        {
          "agent_id": "agent.company.email-sender",
          "role": "Email Sending",
          "estimated_cost": 30.00
        },
        {
          "agent_id": "agent.company.scheduler",
          "role": "Campaign Scheduling",
          "estimated_cost": 25.00
        },
        {
          "agent_id": "agent.company.analytics",
          "role": "Campaign Analytics",
          "estimated_cost": 40.00
        }
      ],
      "total_cost": 95.00,
      "confidence": 0.92,
      "reasoning": "This team covers all requirements: email sending, scheduling, and analytics. Total cost is within budget."
    }
  ]
}
```

### **Human-in-the-Loop Review**

Before booking, users review and approve:

```typescript
// POST /api/marketplace/book-team
{
  "team_id": "team-rec-001",
  "app_id": "app.myapp",
  "duration": "30d",
  "approved_by": "user-123",
  "approval_timestamp": "2026-01-14T12:00:00Z"
}

// Response
{
  "booking_id": "booking-456",
  "team_id": "team-001",
  "status": "active",
  "agents": [...],
  "billing": {
    "estimated_cost": 95.00,
    "billing_cycle": "monthly",
    "next_billing_date": "2026-02-14"
  }
}
```

---

## 💰 **Billing & Revenue Sharing**

### **Automatic Billing**

Each agent sends usage data to the Billing Agent:

```json
{
  "agent_id": "agent.company.email-sender",
  "booking_id": "booking-456",
  "usage": {
    "period": "2026-01-14",
    "actions": [
      {
        "action": "send_email",
        "count": 1500,
        "rate": 0.01,
        "total": 15.00
      }
    ]
  }
}
```

### **Revenue Sharing**

The marketplace automatically distributes revenue:

```json
{
  "booking_id": "booking-456",
  "period": "2026-01",
  "total_revenue": 95.00,
  "distribution": [
    {
      "agent_id": "agent.company.email-sender",
      "creator_id": "creator-123",
      "amount": 30.00,
      "marketplace_fee": 3.00,
      "creator_payout": 27.00
    },
    {
      "agent_id": "agent.company.scheduler",
      "creator_id": "creator-456",
      "amount": 25.00,
      "marketplace_fee": 2.50,
      "creator_payout": 22.50
    }
  ],
  "marketplace_total_fee": 9.50
}
```

**Marketplace Fee:** 10% of revenue (configurable)

---

## ⭐ **Ratings & Trust**

### **Submit Rating**

```typescript
// POST /api/marketplace/rate
{
  "agent_id": "agent.company.email-sender",
  "user_id": "user-123",
  "rating": 9,
  "review": "Excellent email agent! Fast and reliable.",
  "booking_id": "booking-456"
}
```

### **Creator Verification**

Creators can get verified:

```json
{
  "creator_id": "creator-123",
  "verification": {
    "status": "verified",
    "verified_at": "2026-01-10T10:00:00Z",
    "verified_by": "marketplace-admin",
    "checks": [
      {"type": "email", "status": "passed"},
      {"type": "identity", "status": "passed"},
      {"type": "repository", "status": "passed"}
    ]
  }
}
```

---

## 🌐 **Marketplace Types**

### **1. Public Marketplace (Default)**

- **URL**: `https://marketplace.agentify.io`
- **Access**: Public
- **Agents**: Community-contributed
- **Billing**: Centralized

### **2. Private Marketplace**

Organizations can deploy private marketplaces:

```json
{
  "marketplace_id": "marketplace.acme.private",
  "type": "private",
  "url": "https://marketplace.acme.com",
  "access": "restricted",
  "allowed_domains": ["acme.com"],
  "billing": "self-hosted"
}
```

---

## 📊 **Analytics**

Track marketplace metrics:

- Agent popularity
- Revenue per agent
- User satisfaction
- Team performance

---

## 🔗 **API Reference**

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/marketplace/search` | POST | Search agents |
| `/api/marketplace/recommend-team` | POST | Get team recommendations |
| `/api/marketplace/book-team` | POST | Book a team |
| `/api/marketplace/rate` | POST | Rate an agent |
| `/api/marketplace/agents/{id}` | GET | Get agent details |

---

**Next:** [API Documentation](API.md) - Complete API reference

