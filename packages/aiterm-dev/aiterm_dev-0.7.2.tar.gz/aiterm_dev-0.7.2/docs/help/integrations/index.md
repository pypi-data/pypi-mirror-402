# Integrations

**Connect aiterm with your development tools**

aiterm integrates with popular AI coding assistants, MCP servers, and development tools.

---

## 🤖 AI Assistants

### [Claude Code](claude-code.md) ⭐ **Primary Integration**

Deep integration with Anthropic's Claude Code CLI.

**Features:**

- Auto-approval presets (safe, moderate, git, npm, python, full)
- Settings backup and restore
- StatusLine integration (Powerlevel10k-style status bar)
- Permission management

**Quick Start:**

```bash
# Setup auto-approvals
ait claude backup
ait claude approvals add safe

# Install StatusLine
ait statusline install
ait statusline test
```

**Learn More:** [Claude Code Complete Guide](claude-code.md) | [Tutorial](../../CLAUDE-CODE-TUTORIAL.md)

---

### [Gemini CLI](../../gemini-cli/WORKFLOW_GUIDE.md)

Integration with Google's Gemini CLI.

**Features:**

- ADHD-friendly prompting
- Workflow automation
- Context management

**Quick Start:**

```bash
# Check Gemini CLI status
ait info --json | grep gemini
```

**Learn More:** [Gemini Workflow Guide](../../gemini-cli/WORKFLOW_GUIDE.md) | [Tutorial](../../gemini-cli/GEMINI_TUTORIAL.md)

---

## 🔌 MCP Servers

### [MCP Integration](mcp.md)

Model Context Protocol server management.

**Features:**

- Server health monitoring
- Configuration management
- Testing and debugging

**Quick Start:**

```bash
# List configured servers
ait mcp list

# Check server health
ait mcp status

# Test specific server
ait mcp test <name>
```

**Learn More:** [MCP Complete Guide](mcp.md)

---

## 🛠️ Development Tools

### [flow-cli Integration](../../guide/flow-cli-integration.md)

Terminal manager for instant context switching.

**Features:**

- Tab title management
- Profile switching
- Terminal detection

**Quick Start:**

```bash
# Set tab title
tm title "My Project"

# Switch profile
tm profile <name>

# Detect terminal
tm which
```

**Learn More:** [flow-cli Guide](../../guide/flow-cli-integration.md)

---

### [IDE Integration](../../guide/ide-integration.md)

Editor and IDE integrations.

**Features:**

- Context detection
- Profile switching
- Workflow automation

**Learn More:** [IDE Integration Guide](../../guide/ide-integration.md)

---

## 📊 Integration Comparison

| Integration | Auto-Approvals | StatusLine | Context Detection |
|-------------|----------------|------------|-------------------|
| Claude Code | ✅ | ✅ | ✅ |
| Gemini CLI | ❌ | ❌ | ✅ |
| MCP Servers | ❌ | ❌ | ⚠️ Partial |
| flow-cli | ❌ | ❌ | ✅ |

---

## 🎯 Choose Your Integration

### Use Claude Code if you want

- AI pair programming
- Auto-approval management
- Beautiful status bar
- Full aiterm integration

### Use Gemini CLI if you want

- Google's AI models
- ADHD-friendly workflows
- Alternative to Claude

### Use MCP Servers if you want

- Custom tool integrations
- Extended AI capabilities
- Protocol-based architecture

---

## 🚀 Getting Started

1. **Check available integrations:**

   ```bash
   ait info
   ```

2. **Setup Claude Code:**

   ```bash
   ait claude backup
   ait claude approvals add safe
   ait statusline install
   ```

3. **Configure MCP:**

   ```bash
   ait mcp list
   ait mcp status
   ```

---

## 📚 More Resources

- **[Help Center](../index.md)** - All help topics
- **[Quick Reference](../quick-reference.md)** - Command cheat sheet
- **[Tutorials](../tutorials/index.md)** - Step-by-step guides
