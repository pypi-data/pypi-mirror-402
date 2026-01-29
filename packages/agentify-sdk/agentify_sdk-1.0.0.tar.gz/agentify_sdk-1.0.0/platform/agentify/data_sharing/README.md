# 🔄 Agentify Data Sharing Protocol

**Secure cross-app data access with RBAC permissions**

---

## 🎯 **What is Data Sharing?**

The Data Sharing Protocol enables **secure data exchange** between Agentify apps:

- 🔐 **RBAC Permissions** - Role-Based Access Control
- 🌐 **REST + JSON API** - Simple, universal protocol
- 📊 **Audit Trail** - All access logged
- 💾 **Flexible Storage** - Cloud, Edge, or Local (configurable)
- 🔒 **Encryption** - TLS 1.3 + optional end-to-end encryption

---

## 🏗️ **Architecture**

```
┌─────────────────────────────────────────────────────────────┐
│                  Data Sharing Service                        │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │           Permission Manager (RBAC)                  │  │
│  │  - Grant/Revoke Access                               │  │
│  │  - Role Management                                   │  │
│  └──────────────┬───────────────────────────────────────┘  │
│                 │                                           │
│  ┌──────────────▼──────────┐  ┌──────────────────────┐    │
│  │  Data Access Layer      │  │  Audit Logger        │    │
│  │  - Read/Write Data      │  │  - Log All Access    │    │
│  │  - Validate Permissions │  │  - Compliance        │    │
│  └─────────────────────────┘  └──────────────────────┘    │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐  │
│  │           Storage Abstraction Layer                  │  │
│  │  - Cloud (Supabase, Firebase)                        │  │
│  │  - Edge (Cloudflare KV, Deno KV)                     │  │
│  │  - Local (SQLite, File System)                       │  │
│  └─────────────────────────────────────────────────────┘  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔐 **RBAC Permissions Model**

### **Roles**

```typescript
enum Role {
  OWNER = 'owner',       // Full access (read, write, delete, grant)
  ADMIN = 'admin',       // Read, write, delete
  EDITOR = 'editor',     // Read, write
  VIEWER = 'viewer',     // Read only
}
```

### **Permissions**

```typescript
enum Permission {
  READ = 'read',
  WRITE = 'write',
  DELETE = 'delete',
  GRANT = 'grant',       // Grant access to others
}

const RolePermissions = {
  owner: ['read', 'write', 'delete', 'grant'],
  admin: ['read', 'write', 'delete'],
  editor: ['read', 'write'],
  viewer: ['read'],
};
```

---

## 🔄 **Data Sharing Flow**

### **1. Grant Access**

App A grants access to App B:

```typescript
// POST /api/data-sharing/grant
{
  "app_id": "app.myapp",                    // Data owner
  "target_app_id": "app.otherapp",          // Data consumer
  "resource": "users",                      // Resource name
  "role": "viewer",                         // Role (owner, admin, editor, viewer)
  "permissions": ["read"],                  // Explicit permissions
  "expires_at": "2026-02-14T00:00:00Z",    // Optional expiration
  "conditions": {                           // Optional conditions
    "ip_whitelist": ["192.168.1.0/24"],
    "time_window": {
      "start": "09:00",
      "end": "17:00",
      "timezone": "UTC"
    }
  }
}

// Response
{
  "grant_id": "grant-123",
  "status": "active",
  "created_at": "2026-01-14T12:00:00Z",
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

### **2. Access Data**

App B accesses data from App A:

```typescript
// GET /api/data-sharing/data/{app_id}/{resource}
// Headers: Authorization: Bearer {access_token}

GET /api/data-sharing/data/app.myapp/users

// Response
{
  "data": [
    {
      "id": "user-1",
      "name": "Alice",
      "email": "alice@example.com"
    }
  ],
  "metadata": {
    "total": 100,
    "page": 1,
    "per_page": 20
  }
}
```

### **3. Write Data**

App B writes data to App A (if permissions allow):

```typescript
// POST /api/data-sharing/data/{app_id}/{resource}
// Headers: Authorization: Bearer {access_token}

POST /api/data-sharing/data/app.myapp/users
{
  "name": "Bob",
  "email": "bob@example.com"
}

// Response
{
  "id": "user-2",
  "created_at": "2026-01-14T12:05:00Z"
}
```

### **4. Revoke Access**

App A revokes access:

```typescript
// DELETE /api/data-sharing/grant/{grant_id}

DELETE /api/data-sharing/grant/grant-123

// Response
{
  "status": "revoked",
  "revoked_at": "2026-01-14T12:10:00Z"
}
```

---

## 📊 **Audit Trail**

All data access is logged:

```json
{
  "audit_id": "audit-789",
  "timestamp": "2026-01-14T12:05:00Z",
  "grant_id": "grant-123",
  "app_id": "app.myapp",
  "target_app_id": "app.otherapp",
  "resource": "users",
  "action": "read",
  "user_id": "user-123",
  "ip_address": "192.168.1.100",
  "user_agent": "Mozilla/5.0...",
  "status": "success",
  "records_accessed": 20
}
```

### **Query Audit Log**

```typescript
// GET /api/data-sharing/audit?app_id=app.myapp&resource=users

{
  "audits": [
    {
      "audit_id": "audit-789",
      "timestamp": "2026-01-14T12:05:00Z",
      "action": "read",
      "target_app_id": "app.otherapp",
      "status": "success"
    }
  ],
  "total": 150
}
```

---

## 💾 **Storage Abstraction**

Apps can configure storage backend:

### **Storage Interface**

```typescript
interface StorageBackend {
  read(resource: string, query: Query): Promise<any[]>;
  write(resource: string, data: any): Promise<any>;
  delete(resource: string, id: string): Promise<void>;
  query(resource: string, filter: Filter): Promise<any[]>;
}
```

### **Cloud Storage (Default)**

```typescript
class CloudStorage implements StorageBackend {
  constructor(config: {
    provider: 'supabase' | 'firebase' | 'aws';
    credentials: any;
  }) {}
  
  async read(resource: string, query: Query): Promise<any[]> {
    // Read from cloud database
  }
}
```

### **Edge Storage**

```typescript
class EdgeStorage implements StorageBackend {
  constructor(config: {
    provider: 'cloudflare-kv' | 'deno-kv';
    credentials: any;
  }) {}
  
  async read(resource: string, query: Query): Promise<any[]> {
    // Read from edge storage
  }
}
```

### **Local Storage**

```typescript
class LocalStorage implements StorageBackend {
  constructor(config: {
    provider: 'sqlite' | 'filesystem';
    path: string;
  }) {}
  
  async read(resource: string, query: Query): Promise<any[]> {
    // Read from local storage
  }
}
```

**Note:** Developers must implement storage backends. The protocol provides the interface.

---

## 🔒 **Security**

### **1. Authentication**

- **OAuth 2.0** for user authentication
- **API Keys** for app-to-app communication
- **JWT Tokens** for session management

### **2. Encryption**

- **TLS 1.3** for all communication
- **Encryption at rest** (configurable per storage backend)
- **End-to-end encryption** (optional, for sensitive data)

### **3. Access Control**

- **RBAC** enforced at API level
- **IP Whitelisting** (optional)
- **Time-based access** (optional)
- **Rate limiting** per app

### **4. Audit & Compliance**

- All access logged
- Immutable audit trail
- GDPR-compliant data access logs
- Retention policies configurable

---

## 📋 **Resource Schema**

Define resource schemas for validation:

```json
{
  "resource": "users",
  "schema": {
    "type": "object",
    "properties": {
      "id": {"type": "string"},
      "name": {"type": "string"},
      "email": {"type": "string", "format": "email"}
    },
    "required": ["name", "email"]
  },
  "permissions": {
    "read": ["id", "name", "email"],
    "write": ["name", "email"]
  }
}
```

---

## 🌐 **API Reference**

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/data-sharing/grant` | POST | Grant access to resource |
| `/api/data-sharing/grant/{id}` | GET | Get grant details |
| `/api/data-sharing/grant/{id}` | DELETE | Revoke access |
| `/api/data-sharing/data/{app_id}/{resource}` | GET | Read data |
| `/api/data-sharing/data/{app_id}/{resource}` | POST | Write data |
| `/api/data-sharing/data/{app_id}/{resource}/{id}` | DELETE | Delete data |
| `/api/data-sharing/audit` | GET | Query audit log |

---

## 🎯 **Best Practices**

### **1. Principle of Least Privilege**
- Grant minimum necessary permissions
- Use `viewer` role by default
- Escalate only when needed

### **2. Time-Limited Access**
- Set expiration dates for grants
- Review and renew periodically

### **3. Audit Regularly**
- Monitor audit logs
- Alert on suspicious activity
- Review access patterns

### **4. Encrypt Sensitive Data**
- Use end-to-end encryption for PII
- Encrypt at rest
- Rotate encryption keys

---

## 📚 **Examples**

See [examples/](examples/) for:
- Grant access example
- Read/write data example
- Revoke access example
- Audit log query example

---

**Next:** [API Documentation](API.md) - Complete API reference

