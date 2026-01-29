# 🧮 Calculator PoC - Lovable Prompt

**Copy this complete prompt into Lovable to generate the Calculator PoC**

---

```
Create a complete Calculator Proof of Concept (PoC) application following the Agentify standards.

This is a minimal proof of concept demonstrating clean agent separation, orchestration, and containerized execution.

## App Details
- App Name: Calculator PoC
- App ID: app.meet-harmony.calculator-poc
- Description: Minimal proof of concept for agent-based application with calculation and formatting agents
- Purpose: Demonstrate clean agent separation, orchestration, and edge execution

## Architecture Standards

This app MUST follow the Agentify standards documented here:
- **Agent Standard**: https://github.com/your-org/agentify/blob/main/platform/agentify/agent_standard/AGENT_STANDARD.md
- **App Standard**: https://github.com/your-org/agentify/blob/main/platform/agentify/app_standard/README.md
- **Communication Standard**: https://github.com/your-org/agentify/blob/main/platform/agentify/agent_standard/COMMUNICATION.md
- **Authentication Standard**: https://github.com/your-org/agentify/blob/main/platform/agentify/agent_standard/AUTHENTICATION.md
- **Architecture**: https://github.com/your-org/agentify/blob/main/platform/agentify/ARCHITECTURE.md

## System Architecture

The system consists of 4 components:

1. **Test UI (React)** - Simple lab-style frontend
2. **Orchestrator Agent** - Coordinates calculation and formatting agents
3. **Calculation Agent** - Performs mathematical calculations (Docker, edge-capable)
4. **Formatting Agent** - Formats numeric results for display (Docker)

**Execution Flow:**
```
User Input (UI) 
  → Orchestrator (validates & coordinates)
    → Calculation Agent (performs math)
      → Formatting Agent (formats result)
        → Orchestrator (returns to UI)
          → UI (displays result)
```

## Technology Stack

### Frontend (UI)
- Framework: Vite + React 18+ (TypeScript)
- Styling: Tailwind CSS
- UI Components: shadcn/ui
- Icons: Lucide React
- HTTP Client: Axios

### Backend (Orchestrator)
- Runtime: Node.js + Express (TypeScript)
- Validation: Zod
- HTTP Client: Axios
- Docker: Yes

### Calculation Agent
- Runtime: Python + FastAPI
- Docker: Yes
- Platform: linux/arm64 (Raspberry Pi compatible)

### Formatting Agent
- Runtime: Node.js + Express (TypeScript)
- Formatting: Intl.NumberFormat
- Docker: Yes

### Infrastructure
- Container Orchestration: Docker Compose
- Default Marketplace: marketplace.meet-harmony.ai
- Authentication: CoreSense (https://iam.meet-harmony.ai)
- Logging: Console (development)

## Component 1: Test UI (React Frontend)

### Responsibilities
- Display input form (number1, operator, number2)
- Send input to orchestrator
- Display formatted result
- **NO LOGIC** - pure presentation layer

### UI Design

Create a simple, clean calculator interface:

```
┌─────────────────────────────────────────┐
│         Calculator PoC                  │
│         Agentify Demo                   │
├─────────────────────────────────────────┤
│                                         │
│  First Number:                          │
│  ┌─────────────────────────────────┐   │
│  │ 0                               │   │
│  └─────────────────────────────────┘   │
│                                         │
│  Operator:                              │
│  ┌─────────────────────────────────┐   │
│  │ + ▼                             │   │
│  └─────────────────────────────────┘   │
│  Options: + (Add)                       │
│           - (Subtract)                  │
│           * (Multiply)                  │
│           / (Divide)                    │
│                                         │
│  Second Number:                         │
│  ┌─────────────────────────────────┐   │
│  │ 0                               │   │
│  └─────────────────────────────────┘   │
│                                         │
│  ┌─────────────────────────────────┐   │
│  │      Calculate                  │   │
│  └─────────────────────────────────┘   │
│                                         │
│  Result:                                │
│  ┌─────────────────────────────────┐   │
│  │ 0.00                            │   │
│  └─────────────────────────────────┘   │
│                                         │
│  ┌─────────────────────────────────┐   │
│  │ Orchestrator: ✓ Connected       │   │
│  │ Calculation Agent: ✓ Active     │   │
│  │ Formatting Agent: ✓ Active      │   │
│  └─────────────────────────────────┘   │
│                                         │
└─────────────────────────────────────────┘
```

### Features
- Number inputs (type="number", step="any")
- Operator dropdown (select)
- Calculate button
- Result display (read-only input)
- Agent status indicators (green = active, red = inactive)
- Loading state during calculation
- Error display (if calculation fails)

### Implementation

**src/pages/Calculator.tsx:**
```typescript
import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select } from '@/components/ui/select';
import { Card } from '@/components/ui/card';
import { orchestratorService } from '@/services/orchestrator';

export function Calculator() {
  const [a, setA] = useState<number>(0);
  const [b, setB] = useState<number>(0);
  const [op, setOp] = useState<string>('+');
  const [result, setResult] = useState<string>('0.00');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleCalculate = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await orchestratorService.calculate({ a, b, op });
      setResult(response.result);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
      <Card className="w-full max-w-md p-6">
        <h1 className="text-2xl font-bold mb-2">Calculator PoC</h1>
        <p className="text-sm text-gray-600 mb-6">Agentify Demo</p>
        
        {/* First Number */}
        <div className="mb-4">
          <label className="block text-sm font-medium mb-2">First Number</label>
          <Input
            type="number"
            step="any"
            value={a}
            onChange={(e) => setA(parseFloat(e.target.value))}
          />
        </div>
        
        {/* Operator */}
        <div className="mb-4">
          <label className="block text-sm font-medium mb-2">Operator</label>
          <Select value={op} onValueChange={setOp}>
            <option value="+">+ (Add)</option>
            <option value="-">- (Subtract)</option>
            <option value="*">* (Multiply)</option>
            <option value="/">/ (Divide)</option>
          </Select>
        </div>
        
        {/* Second Number */}
        <div className="mb-4">
          <label className="block text-sm font-medium mb-2">Second Number</label>
          <Input
            type="number"
            step="any"
            value={b}
            onChange={(e) => setB(parseFloat(e.target.value))}
          />
        </div>
        
        {/* Calculate Button */}
        <Button
          onClick={handleCalculate}
          disabled={loading}
          className="w-full mb-4"
        >
          {loading ? 'Calculating...' : 'Calculate'}
        </Button>
        
        {/* Result */}
        <div className="mb-4">
          <label className="block text-sm font-medium mb-2">Result</label>
          <Input
            type="text"
            value={result}
            readOnly
            className="font-mono text-lg"
          />
        </div>
        
        {/* Error */}
        {error && (
          <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded text-red-700 text-sm">
            {error}
          </div>
        )}
        
        {/* Agent Status */}
        <div className="border-t pt-4">
          <p className="text-xs text-gray-600 mb-2">Agent Status:</p>
          <div className="space-y-1 text-xs">
            <div className="flex items-center">
              <span className="w-2 h-2 bg-green-500 rounded-full mr-2"></span>
              Orchestrator: Connected
            </div>
            <div className="flex items-center">
              <span className="w-2 h-2 bg-green-500 rounded-full mr-2"></span>
              Calculation Agent: Active
            </div>
            <div className="flex items-center">
              <span className="w-2 h-2 bg-green-500 rounded-full mr-2"></span>
              Formatting Agent: Active
            </div>
          </div>
        </div>
      </Card>
    </div>
  );
}
```

**src/services/orchestrator.ts:**
```typescript
import axios from 'axios';

const ORCHESTRATOR_URL = import.meta.env.VITE_ORCHESTRATOR_URL || 'http://localhost:3000';

export const orchestratorService = {
  async calculate(input: { a: number; b: number; op: string }) {
    const response = await axios.post(`${ORCHESTRATOR_URL}/calculate`, input);
    return response.data;
  },
  
  async healthCheck() {
    const response = await axios.get(`${ORCHESTRATOR_URL}/health`);
    return response.data;
  },
};
```

## Component 2: Orchestrator Agent

### Responsibilities
- Receive user input from UI
- Validate input (numbers, operator)
- Structure calculation request
- Call calculation agent
- Call formatting agent
- Return final result to UI
- **NO CALCULATION OR FORMATTING LOGIC**

### Implementation

Create orchestrator at `orchestrator/` directory (separate from UI):

**orchestrator/src/index.ts:**
```typescript
import express from 'express';
import cors from 'cors';
import axios from 'axios';
import { z } from 'zod';

const app = express();
app.use(cors());
app.use(express.json());

const CALCULATION_AGENT_URL = process.env.CALCULATION_AGENT_URL || 'http://calculation:8000';
const FORMATTING_AGENT_URL = process.env.FORMATTING_AGENT_URL || 'http://formatting:8001';

// Validation schema
const CalculationInputSchema = z.object({
  a: z.number(),
  b: z.number(),
  op: z.enum(['+', '-', '*', '/']),
});

// Calculate endpoint
app.post('/calculate', async (req, res) => {
  try {
    // 1. Validate input
    const input = CalculationInputSchema.parse(req.body);
    
    console.log('[Orchestrator] Received calculation request:', input);
    
    // 2. Call calculation agent
    console.log('[Orchestrator] Calling calculation agent...');
    const calcResponse = await axios.post(`${CALCULATION_AGENT_URL}/calculate`, input);
    const result = calcResponse.data.result;
    
    console.log('[Orchestrator] Calculation result:', result);
    
    // 3. Call formatting agent
    console.log('[Orchestrator] Calling formatting agent...');
    const formatResponse = await axios.post(`${FORMATTING_AGENT_URL}/format`, {
      value: result,
      locale: 'en-US',
      decimals: 2,
    });
    const formatted = formatResponse.data.formatted;
    
    console.log('[Orchestrator] Formatted result:', formatted);
    
    // 4. Return to UI
    res.json({ result: formatted });
  } catch (error) {
    console.error('[Orchestrator] Error:', error);
    res.status(500).json({ error: error.message });
  }
});

// Health check
app.get('/health', (req, res) => {
  res.json({ status: 'ok', agent: 'orchestrator' });
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
  console.log(`[Orchestrator] Running on port ${PORT}`);
});
```

**orchestrator/manifest.json:**
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
  "desires": {
    "profile": [
      {"id": "accuracy", "weight": 0.5},
      {"id": "speed", "weight": 0.5}
    ]
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
  ],
  "authority": {
    "instruction": {"type": "app", "id": "app.meet-harmony.calculator-poc"},
    "oversight": {"type": "human", "id": "user", "independent": true}
  },
  "authentication": {
    "required": false,
    "provider": "coresense",
    "provider_url": "https://iam.meet-harmony.ai"
  }
}
```

**orchestrator/Dockerfile:**
```dockerfile
FROM node:18-alpine

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .
RUN npm run build

EXPOSE 3000

CMD ["node", "dist/index.js"]
```

**orchestrator/package.json:**
```json
{
  "name": "calculator-orchestrator",
  "version": "1.0.0",
  "scripts": {
    "dev": "tsx watch src/index.ts",
    "build": "tsc",
    "start": "node dist/index.js"
  },
  "dependencies": {
    "express": "^4.18.2",
    "cors": "^2.8.5",
    "axios": "^1.6.0",
    "zod": "^3.22.0"
  },
  "devDependencies": {
    "@types/express": "^4.17.21",
    "@types/cors": "^2.8.17",
    "typescript": "^5.3.0",
    "tsx": "^4.7.0"
  }
}
```

## Component 3: Calculation Agent

### Responsibilities
- Perform mathematical calculation
- Receive structured input: `{ a: number, b: number, op: string }`
- Return raw numeric result
- **STATELESS** - no memory between calls
- **EDGE-CAPABLE** - can run on Raspberry Pi

### Implementation

Create calculation agent at `agents/calculation/` directory:

**agents/calculation/main.py:**
```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Literal
import uvicorn

app = FastAPI()

class CalculationInput(BaseModel):
    a: float
    b: float
    op: Literal['+', '-', '*', '/']

class CalculationOutput(BaseModel):
    result: float

@app.post("/calculate", response_model=CalculationOutput)
async def calculate(input: CalculationInput):
    """
    Perform mathematical calculation.
    This agent ONLY calculates - no formatting, no validation beyond input schema.
    """
    print(f"[Calculation Agent] Received: {input.a} {input.op} {input.b}")
    
    if input.op == "+":
        result = input.a + input.b
    elif input.op == "-":
        result = input.a - input.b
    elif input.op == "*":
        result = input.a * input.b
    elif input.op == "/":
        if input.b == 0:
            raise HTTPException(status_code=400, detail="Division by zero")
        result = input.a / input.b
    else:
        raise HTTPException(status_code=400, detail=f"Invalid operator: {input.op}")
    
    print(f"[Calculation Agent] Result: {result}")
    
    return CalculationOutput(result=result)

@app.get("/health")
async def health():
    return {"status": "ok", "agent": "calculation"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

**agents/calculation/manifest.json:**
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
  "desires": {
    "profile": [
      {"id": "accuracy", "weight": 1.0}
    ]
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
  },
  "authority": {
    "instruction": {"type": "agent", "id": "agent.calculator-poc.orchestrator"},
    "oversight": {"type": "agent", "id": "agent.calculator-poc.orchestrator", "independent": false}
  },
  "authentication": {
    "required": false,
    "provider": "coresense",
    "provider_url": "https://iam.meet-harmony.ai"
  }
}
```

**agents/calculation/Dockerfile:**
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["python", "main.py"]
```

**agents/calculation/requirements.txt:**
```
fastapi==0.109.0
uvicorn==0.27.0
pydantic==2.5.0
```

## Component 4: Formatting Agent

### Responsibilities
- Format numeric result for display
- Apply locale-specific formatting
- Handle decimal separators
- Round to appropriate precision
- Return formatted string

### Implementation

Create formatting agent at `agents/formatting/` directory:

**agents/formatting/src/index.ts:**
```typescript
import express from 'express';
import { z } from 'zod';

const app = express();
app.use(express.json());

const FormatInputSchema = z.object({
  value: z.number(),
  locale: z.string().optional().default('en-US'),
  decimals: z.number().optional().default(2),
});

app.post('/format', (req, res) => {
  try {
    const input = FormatInputSchema.parse(req.body);
    
    console.log('[Formatting Agent] Received:', input);
    
    const formatted = new Intl.NumberFormat(input.locale, {
      minimumFractionDigits: input.decimals,
      maximumFractionDigits: input.decimals,
    }).format(input.value);
    
    console.log('[Formatting Agent] Formatted:', formatted);
    
    res.json({ formatted });
  } catch (error) {
    console.error('[Formatting Agent] Error:', error);
    res.status(500).json({ error: error.message });
  }
});

app.get('/health', (req, res) => {
  res.json({ status: 'ok', agent: 'formatting' });
});

const PORT = process.env.PORT || 8001;
app.listen(PORT, () => {
  console.log(`[Formatting Agent] Running on port ${PORT}`);
});
```

**agents/formatting/manifest.json:**
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
  "desires": {
    "profile": [
      {"id": "readability", "weight": 1.0}
    ]
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
  ],
  "authority": {
    "instruction": {"type": "agent", "id": "agent.calculator-poc.orchestrator"},
    "oversight": {"type": "agent", "id": "agent.calculator-poc.orchestrator", "independent": false}
  },
  "authentication": {
    "required": false,
    "provider": "coresense",
    "provider_url": "https://iam.meet-harmony.ai"
  }
}
```

**agents/formatting/Dockerfile:**
```dockerfile
FROM node:18-alpine

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .
RUN npm run build

EXPOSE 8001

CMD ["node", "dist/index.js"]
```

## Docker Compose

Create `docker-compose.yml` at root:

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
    depends_on:
      - calculation
      - formatting

  calculation:
    build: ./agents/calculation
    ports:
      - "8000:8000"
    platform: linux/arm64  # For Raspberry Pi compatibility

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
    depends_on:
      - orchestrator
```

## Project Structure
```
calculator-poc/
├── ui/                            # React frontend
│   ├── src/
│   │   ├── pages/
│   │   │   └── Calculator.tsx
│   │   ├── services/
│   │   │   └── orchestrator.ts
│   │   ├── components/ui/
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── Dockerfile
│   └── package.json
├── orchestrator/                  # Orchestrator agent
│   ├── src/
│   │   └── index.ts
│   ├── manifest.json
│   ├── Dockerfile
│   └── package.json
├── agents/
│   ├── calculation/               # Calculation agent
│   │   ├── main.py
│   │   ├── manifest.json
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   └── formatting/                # Formatting agent
│       ├── src/
│       │   └── index.ts
│       ├── manifest.json
│       ├── Dockerfile
│       └── package.json
├── docker-compose.yml
├── .env.example
└── README.md
```

## Environment Variables (.env.example)
```env
# Orchestrator
CALCULATION_AGENT_URL=http://calculation:8000
FORMATTING_AGENT_URL=http://formatting:8001

# UI
VITE_ORCHESTRATOR_URL=http://localhost:3000

# Marketplace (for future agent discovery)
VITE_MARKETPLACE_URL=https://marketplace.meet-harmony.ai
```

## Additional Requirements

- Use TypeScript for all Node.js code
- Use Python 3.11+ for calculation agent
- Include proper error handling
- Add loading states
- Include health check endpoints for all agents
- Add comprehensive logging (console)
- Follow Agentify Agent Standard v1
- Include manifest.json for each agent
- Make calculation agent ARM64-compatible (Raspberry Pi)
- Add README with setup instructions

## Expected Output

Generate a complete, working Calculator PoC with:
- React UI (Vite + TypeScript + Tailwind + shadcn/ui)
- Orchestrator agent (Node.js + Express + TypeScript)
- Calculation agent (Python + FastAPI)
- Formatting agent (Node.js + Express + TypeScript)
- Docker containers for all components
- Docker Compose for orchestration
- Agent manifests following Agentify standard
- Health check endpoints
- Proper error handling
- Comprehensive logging

The app should be ready to run with:
```bash
docker-compose up --build
```

Then access UI at http://localhost:5173
```

---

**Next Steps:**
1. Copy this prompt
2. Paste into Lovable
3. Wait for generation
4. Run `docker-compose up --build`
5. Access UI at http://localhost:5173
6. Test calculations
7. Verify agent separation (check logs)
8. Deploy calculation agent to Raspberry Pi (optional)

