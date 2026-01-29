# 🎨 Formatting Agent

**Number formatting agent for Calculator PoC**

**Version:** 1.0.0  
**Status:** ✅ Active  
**Language:** Node.js 20+  
**Framework:** Express

---

## 🎯 **What is the Formatting Agent?**

The Formatting Agent formats numbers for display with locale and decimal support:

- 🌍 **Localization** - Format numbers for different locales (en-US, de-DE, etc.)
- 🔢 **Decimals** - Control decimal places
- 💰 **Currency** - Format as currency (optional)
- 📊 **Percentage** - Format as percentage (optional)

---

## 🏗️ **Architecture**

```
┌─────────────────────────────────────────┐
│      Formatting Agent                   │
├─────────────────────────────────────────┤
│                                         │
│  Express Server (Port 8001)             │
│                                         │
│  Endpoints:                             │
│  - POST /agent/message                  │
│  - GET  /health                         │
│  - GET  /manifest                       │
│                                         │
│  Capabilities:                          │
│  - formatting                           │
│  - localization                         │
│                                         │
│  Actions:                               │
│  - format (value, locale, decimals)     │
│                                         │
└─────────────────────────────────────────┘
```

---

## 🚀 **Quick Start**

### **Local Development**

```bash
cd platform/agentify/agents/formatting_agent

# Install dependencies
npm install

# Run agent
npm start

# Test
curl http://localhost:8001/health
```

### **Docker**

```bash
# Build
docker build -t formatting-agent .

# Run
docker run -p 8001:8001 formatting-agent

# Test
curl http://localhost:8001/health
```

---

## 📡 **Agent Communication Protocol**

### **Format Number**

**Request:**
```json
{
  "type": "request",
  "sender": "agent.app.orchestrator",
  "to": ["agent.calculator.formatting"],
  "intent": "format",
  "payload": {
    "value": 1234.5678,
    "locale": "de-DE",
    "decimals": 2
  }
}
```

**Response:**
```json
{
  "type": "inform",
  "sender": "agent.calculator.formatting",
  "to": ["agent.app.orchestrator"],
  "intent": "formatting_result",
  "payload": {
    "formatted": "1.234,57",
    "locale": "de-DE",
    "original": 1234.5678
  }
}
```

---

## 📋 **Supported Locales**

- `en-US` - English (United States) - 1,234.57
- `de-DE` - German (Germany) - 1.234,57
- `fr-FR` - French (France) - 1 234,57
- `es-ES` - Spanish (Spain) - 1.234,57
- `ja-JP` - Japanese (Japan) - 1,234.57
- And many more...

---

## 🔧 **Environment Variables**

```bash
PORT=8001              # Server port
LOG_LEVEL=info         # Log level (debug, info, warning, error)
```

---

## 📦 **Project Structure**

```
platform/agentify/agents/formatting_agent/
├── src/
│   └── index.js               # Express app
├── package.json               # NPM dependencies
├── manifest.json              # Agent manifest
├── Dockerfile                 # Docker build
├── .dockerignore
└── README.md
```

---

## 🎯 **Manifest**

See `manifest.json` for complete agent definition including:
- Agent ID: `agent.calculator.formatting`
- Capabilities: `["formatting", "localization"]`
- Repository: GitHub URL
- Build Config: NPM
- Host Requirements: 256MB RAM, 0.25 CPU cores

---

**Status:** ✅ Active  
**Version:** 1.0.0  
**Date:** 2026-01-16

