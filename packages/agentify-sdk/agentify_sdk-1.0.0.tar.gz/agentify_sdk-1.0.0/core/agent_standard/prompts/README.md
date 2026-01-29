# Agent Standard v1 - AI Development Prompts

This directory contains prompt templates for AI coding assistants (like GitHub Copilot, Cursor, Augment, etc.) to generate Agent Standard v1 compliant code.

---

## 🎯 **How to Use**

### **1. Copy the appropriate prompt**
Choose from:
- `create_agent.md` - Create a new agent from scratch
- `wrap_existing_code.md` - Wrap existing code as an agent
- `add_tool.md` - Add a new tool to an existing agent
- `integrate_framework.md` - Integrate with LangChain, FastAPI, etc.

### **2. Paste into your AI coding assistant**
- **GitHub Copilot**: Use in comments
- **Cursor**: Use in chat
- **Augment**: Use in conversation
- **ChatGPT/Claude**: Use directly

### **3. Customize the prompt**
Replace placeholders like:
- `{AGENT_NAME}` - Your agent name
- `{DESCRIPTION}` - What your agent does
- `{CAPABILITIES}` - What it can do
- `{ETHICS}` - Ethical constraints

### **4. Let AI generate the code**
The AI will generate fully compliant Agent Standard v1 code!

---

## 📝 **Available Prompts**

### **1. Create New Agent** (`create_agent.md`)
Generate a complete agent from scratch with manifest, tools, and ethics.

**Example:**
```
Create an Agent Standard v1 compliant agent that:
- Checks my Outlook calendar
- Finds free slots
- Suggests meeting times

Ethics: no_unauthorized_access, privacy_first
Desires: trust, helpfulness
Oversight: human:supervisor
```

### **2. Wrap Existing Code** (`wrap_existing_code.md`)
Wrap existing Python code as an Agent Standard agent.

**Example:**
```
Wrap this existing function as an Agent Standard v1 agent:

def send_email(to: str, subject: str, body: str) -> bool:
    # existing implementation
    pass

Add ethics: no_spam, privacy_first
Add desires: trust, helpfulness
```

### **3. Add Tool** (`add_tool.md`)
Add a new tool to an existing agent.

**Example:**
```
Add a new tool to my agent that:
- Searches Google
- Returns top 5 results

Ethics: no_illegal_content
Desires: helpfulness
```

### **4. Integrate Framework** (`integrate_framework.md`)
Integrate with existing frameworks (LangChain, FastAPI, n8n).

**Example:**
```
Integrate my LangChain agent with Agent Standard v1:

agent = AgentExecutor(...)

Add ethics evaluation and oversight.
```

---

## 🚀 **Quick Start**

### **Example 1: Create Calendar Agent**

**Prompt:**
```
Create an Agent Standard v1 compliant agent that checks my Outlook calendar and finds free slots.

Requirements:
- Ethics: no_unauthorized_access, privacy_first
- Desires: trust, helpfulness, coherence
- Oversight: human:supervisor
- Capabilities: calendar_access, time_analysis
```

**AI generates:**
```python
from core.agent_standard import Agent, agent_tool

@agent_tool(
    name="check_calendar",
    description="Check Outlook calendar for free slots",
    ethics=["no_unauthorized_access", "privacy_first"],
    desires=["trust", "helpfulness", "coherence"]
)
async def check_calendar(date_range: str) -> list[dict]:
    # Implementation...
    pass

# Manifest auto-generated...
```

### **Example 2: Wrap Existing Code**

**Prompt:**
```
Wrap this function as Agent Standard v1 agent:

def calculate_tax(income: float, country: str) -> float:
    # existing implementation
    return tax

Add ethics: no_illegal_guidance
Add desires: trust, accuracy
```

**AI generates:**
```python
from core.agent_standard.decorators import wrap_as_agent

# Original function (unchanged!)
def calculate_tax(income: float, country: str) -> float:
    # existing implementation
    return tax

# Wrap at runtime
agent = wrap_as_agent(
    calculate_tax,
    agent_id="agent.finance.tax-calculator",
    auto_ethics=True,
    auto_desires=True
)
```

---

## 📚 **Best Practices**

1. **Always specify ethics** - Even if just `["no_harm"]`
2. **Always specify oversight** - Must be different from instruction
3. **Use descriptive names** - `agent.my-company.calendar-assistant`
4. **Add desires** - For health monitoring
5. **Validate compliance** - Use `agent-std validate`

---

## 🔗 **Resources**

- [Agent Standard v1 Spec](../README.md)
- [Quick Start Guide](../QUICKSTART.md)
- [Examples](../examples/)
- [CLI Tool](../cli/)

---

**Happy Agent Building with AI! 🤖**

