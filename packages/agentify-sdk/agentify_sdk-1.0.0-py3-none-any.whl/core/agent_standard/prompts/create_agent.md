# Prompt: Create Agent Standard v1 Compliant Agent

Use this prompt with AI coding assistants to generate a complete Agent Standard v1 compliant agent.

---

## 📋 **Prompt Template**

```
Create an Agent Standard v1 compliant agent with the following specifications:

AGENT DETAILS:
- Agent Name: {AGENT_NAME}
- Agent ID: agent.{COMPANY}.{NAME}
- Description: {DESCRIPTION}
- Version: 1.0.0

CAPABILITIES:
{LIST_CAPABILITIES}

ETHICS:
- Framework: harm-minimization
- Hard Constraints: {HARD_CONSTRAINTS}
- Principles: {ETHICAL_PRINCIPLES}

DESIRES:
{DESIRE_PROFILE}

AUTHORITY:
- Instruction: {INSTRUCTION_AUTHORITY}
- Oversight: {OVERSIGHT_AUTHORITY} (must be different!)

TOOLS:
{LIST_TOOLS_WITH_DESCRIPTIONS}

REQUIREMENTS:
1. Generate complete manifest.json
2. Generate agent.py with @agent_tool decorators
3. Ensure Agent Standard v1 compliance
4. Add ethics evaluation before each action
5. Add desire tracking
6. Add comprehensive docstrings
7. Include example usage

OUTPUT:
- manifest.json (complete Agent Standard v1 manifest)
- agent.py (implementation with decorators)
- README.md (usage instructions)
```

---

## 🎯 **Example Usage**

### **Example 1: Calendar Assistant**

```
Create an Agent Standard v1 compliant agent with the following specifications:

AGENT DETAILS:
- Agent Name: Calendar Assistant
- Agent ID: agent.my-company.calendar-assistant
- Description: Checks Outlook calendar and finds free meeting slots
- Version: 1.0.0

CAPABILITIES:
- calendar_access (high)
- time_analysis (medium)
- meeting_scheduling (medium)

ETHICS:
- Framework: harm-minimization
- Hard Constraints: no_unauthorized_access, privacy_first, no_data_exfiltration
- Principles:
  - Respect user privacy
  - Only access authorized calendars
  - Never share calendar data without permission

DESIRES:
- trust (0.4)
- helpfulness (0.3)
- coherence (0.3)

AUTHORITY:
- Instruction: human:user
- Oversight: human:supervisor

TOOLS:
1. check_calendar(date_range: str) -> list[dict]
   - Check Outlook calendar for events in date range
   - Ethics: no_unauthorized_access, privacy_first
   
2. find_free_slots(date_range: str, duration_minutes: int) -> list[dict]
   - Find free time slots in calendar
   - Ethics: privacy_first
   
3. suggest_meeting_times(participants: list[str], duration_minutes: int) -> list[dict]
   - Suggest optimal meeting times for participants
   - Ethics: privacy_first, no_unauthorized_access

REQUIREMENTS:
1. Generate complete manifest.json
2. Generate agent.py with @agent_tool decorators
3. Ensure Agent Standard v1 compliance
4. Add ethics evaluation before each action
5. Add desire tracking
6. Add comprehensive docstrings
7. Include example usage

OUTPUT:
- manifest.json (complete Agent Standard v1 manifest)
- agent.py (implementation with decorators)
- README.md (usage instructions)
```

---

## ✅ **Expected Output**

The AI should generate:

### **1. manifest.json**
```json
{
  "agent_id": "agent.my-company.calendar-assistant",
  "name": "Calendar Assistant",
  "version": "1.0.0",
  "ethics": {
    "framework": "harm-minimization",
    "hard_constraints": ["no_unauthorized_access", "privacy_first"]
  },
  "authority": {
    "instruction": {"type": "human", "id": "user"},
    "oversight": {"type": "human", "id": "supervisor", "independent": true}
  }
}
```

### **2. agent.py**
```python
from core.agent_standard.decorators import agent_tool

@agent_tool(
    name="check_calendar",
    description="Check Outlook calendar for events",
    ethics=["no_unauthorized_access", "privacy_first"],
    desires=["trust", "helpfulness"]
)
async def check_calendar(date_range: str) -> list[dict]:
    """Check calendar for events in date range."""
    # Implementation...
    pass
```

### **3. README.md**
```markdown
# Calendar Assistant

Agent Standard v1 compliant calendar assistant.

## Usage
...
```

---

## 🔧 **Customization**

Replace these placeholders:
- `{AGENT_NAME}` - Your agent name
- `{COMPANY}` - Your company/organization
- `{DESCRIPTION}` - What the agent does
- `{LIST_CAPABILITIES}` - List of capabilities
- `{HARD_CONSTRAINTS}` - Ethical hard constraints
- `{ETHICAL_PRINCIPLES}` - Ethical principles
- `{DESIRE_PROFILE}` - Desire weights
- `{INSTRUCTION_AUTHORITY}` - Who instructs the agent
- `{OVERSIGHT_AUTHORITY}` - Who oversees the agent
- `{LIST_TOOLS_WITH_DESCRIPTIONS}` - Tools with signatures

---

## 📚 **Resources**

- [Agent Standard v1 Spec](../README.md)
- [Quick Start](../QUICKSTART.md)
- [Examples](../examples/)

