# Prompt: Wrap Existing Code as Agent Standard v1 Agent

Use this prompt with AI coding assistants to wrap existing Python code as an Agent Standard v1 compliant agent **without modifying the original code**.

---

## 📋 **Prompt Template**

```
Wrap the following existing Python code as an Agent Standard v1 compliant agent:

EXISTING CODE:
{PASTE_YOUR_CODE_HERE}

AGENT CONFIGURATION:
- Agent ID: agent.{COMPANY}.{NAME}
- Agent Name: {AGENT_NAME}
- Description: {DESCRIPTION}

ETHICS:
- Hard Constraints: {HARD_CONSTRAINTS}
- Soft Constraints: {SOFT_CONSTRAINTS}

DESIRES:
{DESIRE_PROFILE}

AUTHORITY:
- Instruction: {INSTRUCTION_AUTHORITY}
- Oversight: {OVERSIGHT_AUTHORITY}

REQUIREMENTS:
1. Do NOT modify the existing code
2. Use @agent_tool decorator to wrap functions
3. Generate complete manifest.json
4. Ensure Agent Standard v1 compliance
5. Add ethics evaluation
6. Add desire tracking
7. Preserve original function signatures

OUTPUT:
- manifest.json (Agent Standard v1 manifest)
- wrapped_agent.py (original code + decorators)
- README.md (usage instructions)
```

---

## 🎯 **Example Usage**

### **Example 1: Wrap Email Sender**

```
Wrap the following existing Python code as an Agent Standard v1 compliant agent:

EXISTING CODE:
```python
import smtplib
from email.mime.text import MIMEText

def send_email(to: str, subject: str, body: str) -> bool:
    """Send email via SMTP."""
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['To'] = to
    msg['From'] = 'noreply@example.com'
    
    with smtplib.SMTP('smtp.example.com', 587) as server:
        server.starttls()
        server.login('user', 'password')
        server.send_message(msg)
    
    return True

def validate_email(email: str) -> bool:
    """Validate email format."""
    return '@' in email and '.' in email
```

AGENT CONFIGURATION:
- Agent ID: agent.my-company.email-sender
- Agent Name: Email Sender
- Description: Send emails via SMTP with ethics compliance

ETHICS:
- Hard Constraints: no_spam, privacy_first, no_unauthorized_access
- Soft Constraints: inform_before_send, log_all_emails

DESIRES:
- trust (0.4)
- helpfulness (0.3)
- coherence (0.3)

AUTHORITY:
- Instruction: human:user
- Oversight: human:supervisor

REQUIREMENTS:
1. Do NOT modify the existing code
2. Use @agent_tool decorator to wrap functions
3. Generate complete manifest.json
4. Ensure Agent Standard v1 compliance
5. Add ethics evaluation
6. Add desire tracking
7. Preserve original function signatures

OUTPUT:
- manifest.json (Agent Standard v1 manifest)
- wrapped_agent.py (original code + decorators)
- README.md (usage instructions)
```

---

## ✅ **Expected Output**

The AI should generate:

### **1. manifest.json**
```json
{
  "agent_id": "agent.my-company.email-sender",
  "name": "Email Sender",
  "version": "1.0.0",
  "ethics": {
    "framework": "harm-minimization",
    "hard_constraints": ["no_spam", "privacy_first", "no_unauthorized_access"],
    "soft_constraints": ["inform_before_send", "log_all_emails"]
  },
  "authority": {
    "instruction": {"type": "human", "id": "user"},
    "oversight": {"type": "human", "id": "supervisor", "independent": true}
  }
}
```

### **2. wrapped_agent.py**
```python
from core.agent_standard.decorators import agent_tool
import smtplib
from email.mime.text import MIMEText

# ============================================================================
# ORIGINAL CODE (UNCHANGED!)
# ============================================================================

def _send_email_impl(to: str, subject: str, body: str) -> bool:
    """Send email via SMTP."""
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['To'] = to
    msg['From'] = 'noreply@example.com'
    
    with smtplib.SMTP('smtp.example.com', 587) as server:
        server.starttls()
        server.login('user', 'password')
        server.send_message(msg)
    
    return True

def _validate_email_impl(email: str) -> bool:
    """Validate email format."""
    return '@' in email and '.' in email

# ============================================================================
# AGENT STANDARD WRAPPERS
# ============================================================================

@agent_tool(
    name="send_email",
    description="Send email via SMTP",
    ethics=["no_spam", "privacy_first", "no_unauthorized_access"],
    desires=["trust", "helpfulness"]
)
async def send_email(to: str, subject: str, body: str) -> bool:
    """Send email via SMTP (Agent Standard wrapped)."""
    # Validate email first
    if not _validate_email_impl(to):
        raise ValueError(f"Invalid email: {to}")
    
    # Call original implementation
    return _send_email_impl(to, subject, body)

@agent_tool(
    name="validate_email",
    description="Validate email format",
    ethics=["privacy_first"],
    desires=["trust"]
)
async def validate_email(email: str) -> bool:
    """Validate email format (Agent Standard wrapped)."""
    return _validate_email_impl(email)
```

### **3. README.md**
```markdown
# Email Sender Agent

Agent Standard v1 compliant email sender.

## Original Code
The original code has been wrapped with Agent Standard v1 compliance without modification.

## Usage
```bash
agent-std run manifest.json
```
```

---

## 🔧 **Customization**

Replace these placeholders:
- `{PASTE_YOUR_CODE_HERE}` - Your existing Python code
- `{COMPANY}` - Your company/organization
- `{NAME}` - Agent name (lowercase-with-dashes)
- `{AGENT_NAME}` - Human-readable agent name
- `{DESCRIPTION}` - What the agent does
- `{HARD_CONSTRAINTS}` - Ethical hard constraints
- `{SOFT_CONSTRAINTS}` - Ethical soft constraints
- `{DESIRE_PROFILE}` - Desire weights
- `{INSTRUCTION_AUTHORITY}` - Who instructs the agent
- `{OVERSIGHT_AUTHORITY}` - Who oversees the agent

---

## 📚 **Resources**

- [Agent Standard v1 Spec](../README.md)
- [Quick Start](../QUICKSTART.md)
- [Examples](../examples/)

