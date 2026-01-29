# 🧮 Calculation Agent

**Simple mathematical calculation agent for Calculator PoC**

**Version:** 1.0.0  
**Status:** ✅ Active  
**Language:** Python 3.11+  
**Framework:** FastAPI

---

## 🎯 **What is the Calculation Agent?**

The Calculation Agent is a simple agent that performs basic mathematical calculations:

- ➕ **Addition** - Add two numbers
- ➖ **Subtraction** - Subtract two numbers
- ✖️ **Multiplication** - Multiply two numbers
- ➗ **Division** - Divide two numbers

---

## 🏗️ **Architecture**

```
┌─────────────────────────────────────────┐
│      Calculation Agent                  │
├─────────────────────────────────────────┤
│                                         │
│  FastAPI Server (Port 8000)             │
│                                         │
│  Endpoints:                             │
│  - POST /agent/message                  │
│  - GET  /health                         │
│  - GET  /manifest                       │
│                                         │
│  Capabilities:                          │
│  - calculation                          │
│                                         │
│  Actions:                               │
│  - calculate (a, b, op)                 │
│                                         │
└─────────────────────────────────────────┘
```

---

## 🚀 **Quick Start**

### **Local Development**

```bash
cd platform/agentify/agents/calculation_agent

# Install dependencies
pip install -r requirements.txt

# Run agent
python main.py

# Test
curl http://localhost:8000/health
```

### **Docker**

```bash
# Build
docker build -t calculation-agent .

# Run
docker run -p 8000:8000 calculation-agent

# Test
curl http://localhost:8000/health
```

---

## 📡 **Agent Communication Protocol**

### **Calculate**

**Request:**
```json
{
  "type": "request",
  "sender": "agent.app.orchestrator",
  "to": ["agent.calculator.calculation"],
  "intent": "calculate",
  "payload": {
    "a": 5,
    "b": 3,
    "op": "+"
  }
}
```

**Response:**
```json
{
  "type": "inform",
  "sender": "agent.calculator.calculation",
  "to": ["agent.app.orchestrator"],
  "intent": "calculation_result",
  "payload": {
    "result": 8,
    "operation": "5 + 3"
  }
}
```

---

## 📋 **Supported Operations**

- `+` - Addition
- `-` - Subtraction
- `*` - Multiplication
- `/` - Division

---

## 🔧 **Environment Variables**

```bash
PORT=8000              # Server port
LOG_LEVEL=info         # Log level (debug, info, warning, error)
```

---

## 📦 **Project Structure**

```
platform/agentify/agents/calculation_agent/
├── main.py                    # FastAPI app
├── manifest.json              # Agent manifest
├── requirements.txt           # Python dependencies
├── Dockerfile                 # Docker build
├── .dockerignore
└── README.md
```

---

## 🎯 **Manifest**

See `manifest.json` for complete agent definition including:
- Agent ID: `agent.calculator.calculation`
- Capabilities: `["calculation"]`
- Repository: GitHub URL
- Build Config: Docker
- Host Requirements: 512MB RAM, 0.5 CPU cores

---

**Status:** ✅ Active  
**Version:** 1.0.0  
**Date:** 2026-01-16

