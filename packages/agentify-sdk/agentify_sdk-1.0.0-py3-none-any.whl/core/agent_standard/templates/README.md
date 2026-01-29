# 📝 Agent Standard v1 - Templates

**Ready-to-use JSON templates for creating Agent Standard v1 compliant agents**

---

## 📋 **Available Templates**

### **1. Minimal Agent Template** ⚡

**File:** `minimal_agent_template.json`

**Use when:**
- You want to get started quickly
- You only need basic agent functionality
- You're prototyping or testing

**Includes:**
- ✅ All required sections only
- ✅ Minimal configuration
- ✅ Ready to use in 2 minutes

**How to use:**
```bash
# Copy template
cp minimal_agent_template.json my_agent.json

# Edit placeholders (search for <PLACEHOLDER>)
# Replace:
#   - <YOUR_COMPANY> with your company name
#   - <YOUR_AGENT_NAME> with your agent name
#   - <your-email@example.com> with your email
#   - etc.

# Validate
python -m core.agent_standard.validation.manifest_validator my_agent.json
```

---

### **2. Complete Agent Template** 🎯

**File:** `agent_manifest_template.json`

**Use when:**
- You need full control over all features
- You're building a production agent
- You want to see all available options

**Includes:**
- ✅ All 14 core sections
- ✅ Detailed comments and examples
- ✅ All optional features

**How to use:**
```bash
# Copy template
cp agent_manifest_template.json my_agent.json

# Edit placeholders and remove unused sections
# Each optional section has a "_comment" field explaining when to remove it

# Validate
python -m core.agent_standard.validation.manifest_validator my_agent.json
```

---

## 🚀 **Quick Start**

### **Step 1: Choose Your Template**

```bash
# For quick start (minimal)
cp minimal_agent_template.json my_agent.json

# For full features (complete)
cp agent_manifest_template.json my_agent.json
```

### **Step 2: Replace Placeholders**

Search for all `<PLACEHOLDER>` values and replace them:

```bash
# Example replacements:
# <YOUR_COMPANY> → "acme"
# <YOUR_AGENT_NAME> → "sales-assistant"
# <your-email@example.com> → "john@acme.com"
# <What does your agent do?> → "Helps sales team with lead qualification"
```

### **Step 3: Validate**

```bash
python -m core.agent_standard.validation.manifest_validator my_agent.json
```

### **Step 4: Deploy**

```bash
# Register in marketplace
python -m core.agent_standard.cli register my_agent.json

# Or use programmatically
python -c "
from core.agent_standard.models.manifest import AgentManifest
manifest = AgentManifest.from_json_file('my_agent.json')
print(f'✅ Agent {manifest.name} loaded successfully!')
"
```

---

## 📖 **Template Structure**

### **Minimal Template**

```
minimal_agent_template.json
├── agent_id (required)
├── name (required)
├── version (required)
├── status (required)
├── revisions (required)
├── overview (required)
├── capabilities (required)
├── ethics (required)
├── desires (required)
├── authority (required)
└── io (required)
```

### **Complete Template**

```
agent_manifest_template.json
├── All minimal fields
├── pricing (optional)
├── tools (optional)
├── memory (optional)
├── schedule (optional)
├── activities (optional)
├── prompt (optional)
├── guardrails (optional)
├── team (optional)
├── customers (optional)
├── knowledge (optional)
├── observability (optional)
├── ai_model (optional)
└── framework_adapter (optional)
```

---

## ⚠️ **Important Notes**

### **Four-Eyes Principle**

The `authority` section MUST have separate entities for `instruction` and `oversight`:

```json
"authority": {
  "instruction": {
    "type": "human",
    "id": "user@example.com"  // ← Person who instructs the agent
  },
  "oversight": {
    "type": "human",
    "id": "supervisor@example.com",  // ← DIFFERENT person who oversees
    "independent": true  // ← MUST be true
  }
}
```

**❌ WRONG:**
```json
"instruction": {"id": "john@example.com"},
"oversight": {"id": "john@example.com"}  // ❌ Same person!
```

**✅ CORRECT:**
```json
"instruction": {"id": "john@example.com"},
"oversight": {"id": "jane@example.com"}  // ✅ Different person!
```

---

## 🔍 **Validation**

All templates are pre-validated against the Agent Standard v1 schema.

**Validate your agent:**

```python
from core.agent_standard.validation.manifest_validator import ManifestValidator

validator = ManifestValidator()
result = validator.validate_file("my_agent.json")

if result.is_valid:
    print("✅ Valid!")
else:
    for error in result.errors:
        print(f"❌ {error}")
```

---

## 📚 **Resources**

- **[Quick Start Guide](../QUICKSTART_COMPLETE.md)** - Complete tutorial
- **[Agent Anatomy](../AGENT_ANATOMY.md)** - Reference for all 14 sections
- **[Complete Example](../examples/complete_agent_example.json)** - Real-world example
- **[Full Specification](../README.md)** - Complete documentation

---

**Need help?** See the [Quick Start Guide](../QUICKSTART_COMPLETE.md) for detailed instructions!

