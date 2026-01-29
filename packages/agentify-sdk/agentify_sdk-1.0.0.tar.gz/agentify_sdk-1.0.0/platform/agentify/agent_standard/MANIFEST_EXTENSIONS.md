# 📦 Agent Manifest Extensions

**Extensions for deployment, hosting, and co-location**

**Version:** 1.0.0  
**Status:** ✅ Active  
**Date:** 2026-01-16

---

## 🎯 **Purpose**

These manifest extensions enable:

- 🏗️ **Automatic Deployment** - Hosting agents can build and deploy agents from repositories
- 📍 **Co-Location** - Agents can request to run on the same infrastructure
- 🔧 **Build Configuration** - Standardized build and start commands
- 💻 **Host Requirements** - Specify CPU, RAM, GPU, region requirements

---

## 📋 **Manifest Extensions**

### **1. Repository**

Specifies where the agent code lives:

```json
{
  "repository": {
    "url": "https://github.com/company/agent-name",
    "branch": "main",
    "path": "/"
  }
}
```

**Fields:**
- `url` - Git repository URL (required)
- `branch` - Branch to use (default: `main`)
- `path` - Path within repository (default: `/`)

---

### **2. Build Config**

Specifies how to build and start the agent:

```json
{
  "build_config": {
    "type": "docker",
    "build_command": "docker build -t agent-name .",
    "start_command": "docker run -p 8000:8000 agent-name",
    "env_vars": {
      "PORT": "8000",
      "LOG_LEVEL": "info"
    }
  }
}
```

**Fields:**
- `type` - Build type: `docker`, `npm`, `yarn`, `pnpm`, `python`, `custom` (required)
- `build_command` - Command to build the agent (required)
- `start_command` - Command to start the agent (required)
- `env_vars` - Environment variables (optional)

**Supported Types:**

**Docker:**
```json
{
  "type": "docker",
  "build_command": "docker build -t agent-name .",
  "start_command": "docker run -p 8000:8000 agent-name"
}
```

**NPM/Yarn/PNPM:**
```json
{
  "type": "npm",
  "build_command": "npm install && npm run build",
  "start_command": "npm start"
}
```

**Python:**
```json
{
  "type": "python",
  "build_command": "pip install -r requirements.txt",
  "start_command": "uvicorn main:app --host 0.0.0.0 --port 8000"
}
```

**Custom:**
```json
{
  "type": "custom",
  "build_command": "./build.sh",
  "start_command": "./start.sh"
}
```

---

### **3. Host Requirements**

Specifies infrastructure requirements:

```json
{
  "host_requirements": {
    "min_memory_mb": 512,
    "min_cpu_cores": 0.5,
    "gpu_required": false,
    "preferred_region": "eu-central-1",
    "co_location_required": false,
    "co_location_with": []
  }
}
```

**Fields:**
- `min_memory_mb` - Minimum RAM in MB (optional)
- `min_cpu_cores` - Minimum CPU cores (optional)
- `gpu_required` - GPU required? (default: `false`)
- `preferred_region` - Preferred cloud region (optional)
- `co_location_required` - Must run with other agents? (default: `false`)
- `co_location_with` - List of agent IDs to co-locate with (optional)

---

### **4. Preferred Host**

Specifies preferred hosting agent:

```json
{
  "preferred_host": "agent.agentify.hosting-orchestrator"
}
```

**Default:** `agent.agentify.hosting-orchestrator`

---

## 🔄 **Complete Example**

```json
{
  "agent_id": "agent.calculator.calculation",
  "name": "Calculation Agent",
  "version": "1.0.0",
  "status": "active",
  
  "repository": {
    "url": "https://github.com/company/calculation-agent",
    "branch": "main",
    "path": "/"
  },
  
  "build_config": {
    "type": "docker",
    "build_command": "docker build -t calc-agent .",
    "start_command": "docker run -p 8000:8000 calc-agent",
    "env_vars": {
      "PORT": "8000",
      "LOG_LEVEL": "info"
    }
  },
  
  "host_requirements": {
    "min_memory_mb": 512,
    "min_cpu_cores": 0.5,
    "gpu_required": false,
    "preferred_region": "eu-central-1",
    "co_location_required": false,
    "co_location_with": []
  },
  
  "preferred_host": "agent.agentify.hosting-orchestrator"
}
```

---

**Status:** ✅ Active  
**Version:** 1.0.0  
**Date:** 2026-01-16

