# 🔐 Authentication & IAM Standard

**Version: 1.0.0**  
**Date: 2026-01-16**  
**Default IAM Provider: CoreSense**

---

## 🎯 **Overview**

Every Agentify **app** and **agent** must implement authentication and authorization to ensure:

- ✅ Secure access to agents and apps
- ✅ User identity verification
- ✅ Organization/Team/Project membership validation
- ✅ Role-based access control (RBAC)
- ✅ Audit logging of all actions

---

## 🏗️ **Default IAM Provider: CoreSense**

**CoreSense** is the default Identity and Access Management (IAM) provider for Agentify.

**URL**: `https://iam.meet-harmony.ai`

**Features:**
- User authentication (email/password, OAuth, SSO)
- Organization management
- Team management
- Project management
- Role-based access control (RBAC)
- JWT token generation and validation
- Audit logging

---

## 🔑 **Authentication Flow**

### **1. User Login**

```typescript
import { CoreSenseAuth } from '@meet-harmony/coresense-sdk';

const auth = new CoreSenseAuth({
  url: process.env.VITE_CORESENSE_URL,
  clientId: process.env.VITE_CORESENSE_CLIENT_ID,
  clientSecret: process.env.VITE_CORESENSE_CLIENT_SECRET,
});

// Login with email/password
const { token, user } = await auth.login(email, password);

// Token structure (JWT)
{
  "sub": "user-123",                   // User ID
  "email": "user@example.com",
  "name": "John Doe",
  "organization_id": "org-456",
  "team_ids": ["team-789", "team-012"],
  "project_ids": ["project-345"],
  "roles": ["user", "developer"],
  "iat": 1234567890,
  "exp": 1234571490
}
```

---

### **2. Token Validation**

Every agent and app must validate tokens on **every request**:

```typescript
// Middleware for Express
async function validateToken(req, res, next) {
  const token = req.headers.authorization?.replace('Bearer ', '');
  
  if (!token) {
    return res.status(401).json({ error: 'No token provided' });
  }

  try {
    const { valid, user } = await auth.validateToken(token);
    
    if (!valid) {
      return res.status(401).json({ error: 'Invalid token' });
    }

    // Attach user to request
    req.user = user;
    next();
  } catch (error) {
    return res.status(401).json({ error: 'Token validation failed' });
  }
}

// Use in routes
app.post('/calculate', validateToken, async (req, res) => {
  // req.user is now available
  const { a, b, op } = req.body;
  // ... perform calculation
});
```

---

### **3. Agent-to-Agent Authentication**

When agents call other agents, they must include the **user's token**:

```typescript
// Orchestrator calling calculation agent
async function callCalculationAgent(input, userToken) {
  const response = await axios.post(
    'http://calculation-agent:8000/calculate',
    input,
    {
      headers: {
        'Authorization': `Bearer ${userToken}`,
        'Content-Type': 'application/json',
      }
    }
  );
  
  return response.data;
}
```

**Important**: Agents must **forward the user token**, not create their own. This ensures:
- Audit trail of who initiated the action
- Proper access control at every layer
- Compliance with security policies

---

## 🛡️ **Authorization**

### **1. Role-Based Access Control (RBAC)**

**Standard Roles:**

| Role | Permissions |
|------|-------------|
| `admin` | Full access to all resources |
| `developer` | Create/update agents and apps |
| `user` | Use agents and apps |
| `viewer` | Read-only access |

**Custom Roles:**
Organizations can define custom roles in CoreSense.

---

### **2. Resource-Level Access Control**

**Visibility Levels:**

| Level | Who Can Access |
|-------|----------------|
| `public` | Everyone (authenticated) |
| `organization` | Members of the same organization |
| `team` | Members of the same team |
| `project` | Members of the same project |
| `private` | Only the creator |

**Implementation:**

```typescript
// Check if user can access resource
function canAccess(user, resource) {
  if (resource.visibility === 'public') {
    return true;
  }
  
  if (resource.visibility === 'organization') {
    return user.organization_id === resource.organization_id;
  }
  
  if (resource.visibility === 'team') {
    return user.team_ids.includes(resource.team_id);
  }
  
  if (resource.visibility === 'project') {
    return user.project_ids.includes(resource.project_id);
  }
  
  if (resource.visibility === 'private') {
    return user.sub === resource.creator_id;
  }
  
  return false;
}
```

---

## 📋 **Agent Manifest - Authentication Section**

Every agent manifest must include an `authentication` section:

```json
{
  "agent_id": "agent.company.calculator",
  "name": "Calculator Agent",
  "version": "1.0.0",
  "authentication": {
    "required": true,
    "provider": "coresense",
    "provider_url": "https://iam.meet-harmony.ai",
    "token_validation": "jwt",
    "roles_required": ["user"],
    "scopes_required": ["agent:execute"]
  },
  "authorization": {
    "visibility": "public",
    "rbac_enabled": true,
    "custom_policies": []
  }
}
```

---

## 📋 **App Manifest - Authentication Section**

Every app manifest must include an `authentication` section:

```json
{
  "app_id": "app.company.calculator-poc",
  "name": "Calculator PoC",
  "version": "1.0.0",
  "authentication": {
    "required": true,
    "provider": "coresense",
    "provider_url": "https://iam.meet-harmony.ai",
    "login_redirect": "/auth/callback",
    "logout_redirect": "/",
    "token_storage": "localStorage",
    "token_refresh": true
  },
  "authorization": {
    "visibility": "public",
    "rbac_enabled": true,
    "roles_required": ["user"]
  }
}
```

---

## 🔧 **Environment Variables**

**Required for all apps and agents:**

```env
# CoreSense IAM
VITE_CORESENSE_URL=https://iam.meet-harmony.ai
VITE_CORESENSE_CLIENT_ID=your-client-id
VITE_CORESENSE_CLIENT_SECRET=your-client-secret

# Optional: Custom IAM provider
VITE_IAM_PROVIDER=coresense
VITE_IAM_URL=https://iam.meet-harmony.ai
```

---

## 📝 **Audit Logging**

All authentication and authorization events must be logged:

```typescript
// Log authentication event
await logger.info('User authenticated', {
  user_id: user.sub,
  email: user.email,
  organization_id: user.organization_id,
  ip_address: req.ip,
  user_agent: req.headers['user-agent'],
});

// Log authorization event
await logger.info('Access granted', {
  user_id: user.sub,
  resource_type: 'agent',
  resource_id: 'agent.company.calculator',
  action: 'execute',
});

// Log authorization failure
await logger.warn('Access denied', {
  user_id: user.sub,
  resource_type: 'agent',
  resource_id: 'agent.company.calculator',
  action: 'execute',
  reason: 'insufficient_permissions',
});
```

---

## 🚀 **Quick Start**

### **1. Install CoreSense SDK**

```bash
npm install @meet-harmony/coresense-sdk
```

### **2. Configure Environment**

```env
VITE_CORESENSE_URL=https://iam.meet-harmony.ai
VITE_CORESENSE_CLIENT_ID=your-client-id
VITE_CORESENSE_CLIENT_SECRET=your-client-secret
```

### **3. Implement Authentication**

```typescript
import { CoreSenseAuth } from '@meet-harmony/coresense-sdk';

const auth = new CoreSenseAuth({
  url: process.env.VITE_CORESENSE_URL,
  clientId: process.env.VITE_CORESENSE_CLIENT_ID,
  clientSecret: process.env.VITE_CORESENSE_CLIENT_SECRET,
});

// In your app/agent
app.use(async (req, res, next) => {
  const token = req.headers.authorization?.replace('Bearer ', '');
  const { valid, user } = await auth.validateToken(token);
  
  if (!valid) {
    return res.status(401).json({ error: 'Unauthorized' });
  }
  
  req.user = user;
  next();
});
```

---

## 📚 **References**

- **CoreSense Documentation**: https://docs.meet-harmony.ai/coresense
- **Agent Standard**: https://github.com/your-org/agentify/blob/main/platform/agentify/agent_standard/AGENT_STANDARD.md
- **App Standard**: https://github.com/your-org/agentify/blob/main/platform/agentify/app_standard/README.md

---

**Next:** Integrate authentication into your agents and apps following this standard.

