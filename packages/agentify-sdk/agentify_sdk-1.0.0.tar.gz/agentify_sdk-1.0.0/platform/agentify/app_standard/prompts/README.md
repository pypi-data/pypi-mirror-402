# 🤖 AI Prompts for Agentify App Development

**Pre-built prompts for AI-assisted development of Agentify apps**

---

## 🎯 **Overview**

These prompts help you build **Agentify-compliant apps** using AI coding assistants:

- **Lovable** - Generate full apps from prompts
- **Cursor** - AI-powered code editing
- **GitHub Copilot** - Code completion
- **Augment** - Codebase-aware AI
- **v0** - UI generation
- **Bolt** - Full-stack generation

---

## 📚 **Available Prompts**

| Prompt | Description | Tools |
|--------|-------------|-------|
| **[create_app.md](create_app.md)** | Create a new Agentify app from scratch | All |
| **[add_orchestrator.md](add_orchestrator.md)** | Add orchestrator to existing app | All |
| **[integrate_marketplace.md](integrate_marketplace.md)** | Add marketplace integration | All |
| **[add_data_sharing.md](add_data_sharing.md)** | Add data sharing capabilities | All |
| **[convert_to_integrated.md](convert_to_integrated.md)** | Convert standalone to integrated mode | All |

---

## 🚀 **Quick Start**

### **1. Using Lovable**

1. Go to [lovable.dev](https://lovable.dev)
2. Copy the prompt from [create_app.md](create_app.md)
3. Paste into Lovable
4. Customize the app description
5. Generate!

### **2. Using Cursor**

1. Open Cursor
2. Press `Cmd/Ctrl + K`
3. Copy the prompt from [create_app.md](create_app.md)
4. Paste and customize
5. Let Cursor generate the code

### **3. Using GitHub Copilot**

1. Create a new file (e.g., `PROMPT.md`)
2. Copy the prompt
3. Copilot will suggest code based on the prompt
4. Accept suggestions and iterate

### **4. Using Augment**

1. Open Augment
2. Copy the prompt
3. Augment will use codebase context to generate code
4. Review and accept

---

## 📝 **Prompt Structure**

All prompts follow this structure:

```markdown
# [Prompt Title]

## Context
[Background information about Agentify]

## Task
[What you want to build]

## Requirements
[Technical requirements]

## Expected Output
[What the AI should generate]

## Example
[Example code or structure]
```

---

## 🎨 **Customization**

### **App-Specific Customization**

Replace placeholders in prompts:

- `{APP_NAME}` - Your app name
- `{APP_DESCRIPTION}` - What your app does
- `{CAPABILITIES}` - Required agent capabilities
- `{STORAGE_TYPE}` - cloud, edge, or local

### **Example:**

```markdown
Create an Agentify app called "{APP_NAME}" that {APP_DESCRIPTION}.

Replace with:

Create an Agentify app called "Email Manager" that manages email campaigns.
```

---

## 🔧 **Advanced Usage**

### **Combining Prompts**

You can combine multiple prompts:

1. Start with `create_app.md`
2. Add `integrate_marketplace.md`
3. Add `add_data_sharing.md`

### **Iterative Development**

1. Generate base app
2. Test and review
3. Use additional prompts to add features
4. Iterate until complete

---

## 📖 **Prompt Details**

### **1. Create App** ([create_app.md](create_app.md))

**Purpose:** Generate a complete Agentify app from scratch

**Includes:**
- Vite + React + Tailwind + Zustand setup
- App manifest (`agentify.json`)
- Orchestrator agent
- Standalone and Integrated layouts
- Marketplace integration
- Data sharing setup

**Best for:** Starting a new project

---

### **2. Add Orchestrator** ([add_orchestrator.md](add_orchestrator.md))

**Purpose:** Add orchestrator agent to existing app

**Includes:**
- Orchestrator manifest
- Orchestrator implementation
- Team building logic
- Marketplace integration

**Best for:** Adding orchestration to existing React app

---

### **3. Integrate Marketplace** ([integrate_marketplace.md](integrate_marketplace.md))

**Purpose:** Add marketplace integration

**Includes:**
- Marketplace service
- Agent search UI
- Team building UI
- Billing integration

**Best for:** Apps that need to discover and use agents

---

### **4. Add Data Sharing** ([add_data_sharing.md](add_data_sharing.md))

**Purpose:** Add data sharing capabilities

**Includes:**
- Data sharing service
- Permission management UI
- RBAC implementation
- Audit logging

**Best for:** Apps that need to share data with other apps

---

### **5. Convert to Integrated** ([convert_to_integrated.md](convert_to_integrated.md))

**Purpose:** Convert standalone app to integrated mode

**Includes:**
- Integrated layout (sidebar + main)
- Mode switcher
- State management updates

**Best for:** Apps that need both standalone and integrated modes

---

## 🎯 **Best Practices**

### **1. Start Simple**
- Use `create_app.md` first
- Add features incrementally
- Test each feature before adding more

### **2. Customize Prompts**
- Replace placeholders with your specifics
- Add domain-specific requirements
- Include example data

### **3. Review Generated Code**
- Always review AI-generated code
- Test thoroughly
- Ensure Agent Standard compliance

### **4. Iterate**
- Generate → Test → Refine → Repeat
- Use follow-up prompts for refinements
- Don't expect perfection on first try

---

## 🔗 **Resources**

- **[App Standard Spec](../README.md)** - Complete specification
- **[Agentify Architecture](../../ARCHITECTURE.md)** - Platform architecture
- **[Agent Standard v1](../../../../core/agent_standard/README.md)** - Foundation layer
- **[Examples](../examples/)** - Real-world examples

---

## 📞 **Support**

Need help with prompts?

- **Issues**: https://github.com/JonasDEMA/cpa_agent_platform/issues
- **Discussions**: https://github.com/JonasDEMA/cpa_agent_platform/discussions
- **Email**: support@agentify.dev

---

**Happy building with AI! 🤖✨**

