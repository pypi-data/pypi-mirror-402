# 🧮 Calculator PoC - Requirements Specification

**Version: 1.0.0**  
**Date: 2026-01-16**  
**Purpose: Minimal proof of concept for agent-based application**

---

## 🎯 **Overview**

This is a **minimal proof of concept** demonstrating:

- ✅ Clean agent separation by responsibility
- ✅ Orchestration instead of monolithic logic
- ✅ Containerized execution (Docker)
- ✅ Edge device execution (Raspberry Pi)
- ✅ Agentify App & Agent Standard compliance

---

## 🏗️ **System Architecture**

```
┌─────────────────────────────────────────────────────────┐
│                      Test UI (React)                     │
│  - Input: Number 1, Operator, Number 2                  │
│  - Output: Formatted Result                              │
│  - No logic, only display                                │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│              Orchestrator Agent (Backend)                │
│  - Receives user input from UI                           │
│  - Validates and structures input                        │
│  - Coordinates agents (calculation → formatting)         │
│  - Returns final result to UI                            │
│  - No calculation or formatting logic                    │
└────────┬────────────────────────────────────────┬────────┘
         │                                        │
         ▼                                        ▼
┌────────────────────────┐          ┌────────────────────────┐
│  Calculation Agent     │          │  Formatting Agent      │
│  (Docker Container)    │          │  (Docker Container)    │
│                        │          │                        │
│  - Input: {a, b, op}   │          │  - Input: number       │
│  - Output: number      │          │  - Output: string      │
│  - Stateless           │          │  - Locale formatting   │
│  - Edge-capable (RPi)  │          │  - Decimal separators  │
└────────────────────────┘          └────────────────────────┘
```

---

## 📋 **Components**

### **1. Test UI (React Frontend)**

**Responsibilities:**
- Display input form (number1, operator, number2)
- Send input to orchestrator
- Display formatted result
- **No logic** - pure presentation

**Technology:**
- React + Vite
- Tailwind CSS + shadcn/ui
- Axios for API calls

**UI Elements:**
```
┌─────────────────────────────────────┐
│        Calculator PoC               │
├─────────────────────────────────────┤
│                                     │
│  Number 1:  [_______]               │
│                                     │
│  Operator:  [+ ▼]                   │
│             (+ - * /)               │
│                                     │
│  Number 2:  [_______]               │
│                                     │
│  [Calculate]                        │
│                                     │
│  Result: 42.00                      │
│                                     │
└─────────────────────────────────────┘
```

---

### **2. Orchestrator Agent**

**Responsibilities:**
- Receive user input from UI
- Validate input (numbers, operator)
- Structure calculation request
- Call calculation agent
- Call formatting agent
- Return final result to UI
- **No calculation or formatting logic**

**Technology:**
- Node.js + Express (or Python + FastAPI)
- Agentify Agent Standard v1 compliant
- Docker container

**Manifest:**
```json
{
  "agent_id": "agent.calculator-poc.orchestrator",
  "name": "Calculator Orchestrator",
  "version": "1.0.0",
  "status": "active",
  "capabilities": ["orchestration", "validation"],
  "ethics": {
    "framework": "harm-minimization",
    "hard_constraints": ["no_calculation", "no_formatting"]
  },
  "tools": [
    {
      "name": "validate_input",
      "description": "Validate user input",
      "category": "validation"
    },
    {
      "name": "call_calculation_agent",
      "description": "Call calculation agent",
      "category": "orchestration"
    },
    {
      "name": "call_formatting_agent",
      "description": "Call formatting agent",
      "category": "orchestration"
    }
  ]
}
```

**Execution Flow:**
```typescript
async function handleCalculation(input: { a: number, b: number, op: string }) {
  // 1. Validate input
  if (!isValidInput(input)) {
    throw new Error('Invalid input');
  }

  // 2. Call calculation agent
  const result = await callAgent('agent.calculator-poc.calculation', {
    action: 'calculate',
    params: input
  });

  // 3. Call formatting agent
  const formatted = await callAgent('agent.calculator-poc.formatting', {
    action: 'format',
    params: { value: result.data }
  });

  // 4. Return to UI
  return formatted.data;
}
```

---

### **3. Calculation Agent**

**Responsibilities:**
- Perform mathematical calculation
- Receive structured input: `{ a: number, b: number, op: string }`
- Return raw numeric result
- **Stateless** - no memory between calls
- **Edge-capable** - can run on Raspberry Pi

**Technology:**
- Python + FastAPI (lightweight)
- Docker container
- ARM-compatible for Raspberry Pi

**Manifest:**
```json
{
  "agent_id": "agent.calculator-poc.calculation",
  "name": "Calculation Agent",
  "version": "1.0.0",
  "status": "active",
  "capabilities": ["math", "calculation"],
  "ethics": {
    "framework": "harm-minimization",
    "hard_constraints": ["no_formatting", "no_validation"]
  },
  "tools": [
    {
      "name": "calculate",
      "description": "Perform calculation",
      "category": "math",
      "input_schema": {
        "a": "number",
        "b": "number",
        "op": "string (+ - * /)"
      },
      "output_schema": {
        "result": "number"
      }
    }
  ],
  "deployment": {
    "container": "docker",
    "platforms": ["x86_64", "arm64"],
    "edge_capable": true
  }
}
```

**Implementation:**
```python
from fastapi import FastAPI

app = FastAPI()

@app.post("/calculate")
async def calculate(a: float, b: float, op: str):
    if op == "+":
        result = a + b
    elif op == "-":
        result = a - b
    elif op == "*":
        result = a * b
    elif op == "/":
        if b == 0:
            raise ValueError("Division by zero")
        result = a / b
    else:
        raise ValueError(f"Invalid operator: {op}")
    
    return {"result": result}
```

---

### **4. Formatting Agent**

**Responsibilities:**
- Format numeric result for display
- Apply locale-specific formatting
- Handle decimal separators (e.g., 1,234.56 vs 1.234,56)
- Round to appropriate precision
- Return formatted string

**Technology:**
- Node.js + Express (or Python + FastAPI)
- Docker container

**Manifest:**
```json
{
  "agent_id": "agent.calculator-poc.formatting",
  "name": "Formatting Agent",
  "version": "1.0.0",
  "status": "active",
  "capabilities": ["formatting", "localization"],
  "ethics": {
    "framework": "harm-minimization",
    "hard_constraints": ["no_calculation"]
  },
  "tools": [
    {
      "name": "format",
      "description": "Format number for display",
      "category": "formatting",
      "input_schema": {
        "value": "number",
        "locale": "string (optional, default: en-US)",
        "decimals": "number (optional, default: 2)"
      },
      "output_schema": {
        "formatted": "string"
      }
    }
  ]
}
```

**Implementation:**
```typescript
app.post('/format', (req, res) => {
  const { value, locale = 'en-US', decimals = 2 } = req.body;
  
  const formatted = new Intl.NumberFormat(locale, {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  }).format(value);
  
  res.json({ formatted });
});
```

---

## 🔄 **Execution Flow**

1. **User Input**: User enters `5`, `+`, `3` in UI
2. **UI → Orchestrator**: `POST /calculate { a: 5, b: 3, op: '+' }`
3. **Orchestrator validates**: Input is valid
4. **Orchestrator → Calculation Agent**: `POST /calculate { a: 5, b: 3, op: '+' }`
5. **Calculation Agent**: Returns `{ result: 8 }`
6. **Orchestrator → Formatting Agent**: `POST /format { value: 8 }`
7. **Formatting Agent**: Returns `{ formatted: '8.00' }`
8. **Orchestrator → UI**: Returns `{ result: '8.00' }`
9. **UI displays**: `Result: 8.00`

---

## 🐳 **Docker Deployment**

**docker-compose.yml:**
```yaml
version: '3.8'

services:
  orchestrator:
    build: ./orchestrator
    ports:
      - "3000:3000"
    environment:
      - CALCULATION_AGENT_URL=http://calculation:8000
      - FORMATTING_AGENT_URL=http://formatting:8001

  calculation:
    build: ./agents/calculation
    ports:
      - "8000:8000"
    platform: linux/arm64  # For Raspberry Pi

  formatting:
    build: ./agents/formatting
    ports:
      - "8001:8001"

  ui:
    build: ./ui
    ports:
      - "5173:5173"
    environment:
      - VITE_ORCHESTRATOR_URL=http://orchestrator:3000
```

---

## 🎯 **Success Criteria**

- ✅ UI displays input form and result
- ✅ Orchestrator coordinates agents without logic
- ✅ Calculation agent performs math correctly
- ✅ Formatting agent formats numbers correctly
- ✅ All agents run in Docker containers
- ✅ Calculation agent can run on Raspberry Pi
- ✅ All components follow Agentify standards

---

## 📚 **References**

- **Agent Standard**: https://github.com/your-org/agentify/blob/main/platform/agentify/agent_standard/AGENT_STANDARD.md
- **App Standard**: https://github.com/your-org/agentify/blob/main/platform/agentify/app_standard/README.md
- **Communication Standard**: https://github.com/your-org/agentify/blob/main/platform/agentify/agent_standard/COMMUNICATION.md

---

**Next:** See `LOVABLE_PROMPT.md` for complete Lovable prompt to build this PoC.

