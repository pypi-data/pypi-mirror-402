# Documentation Maintenance Prompt

**Use with Claude Code or any AI assistant.**

---

## Context

- **Project:** aiterm
- **Version:** 0.3.8
- **Site URL:** https://data-wise.github.io/aiterm
- **Framework:** MkDocs (Material theme)
- **Total docs:** 52 files
- **Generated:** 2025-12-28

---

## Task

Review, reorganize, and improve the documentation for aiterm.

## Scope (Select all that apply)

- [ ] **Navigation Reorganization** - Restructure site navigation
- [ ] **Content Audit** - Identify outdated, duplicate, or missing content
- [ ] **Content Editing** - Revise and improve existing content
- [ ] **Content Consolidation** - Merge overlapping documents
- [ ] **Gap Analysis** - Identify missing documentation
- [ ] **Style Consistency** - Align tone, formatting, and structure

---

## ADHD-Friendly Design Principles

1. Maximum 6-7 top-level navigation sections
2. Progressive disclosure (basics first, details later)
3. Visual hierarchy with icons and clear labels
4. Quick access to reference/cheat sheets
5. Separate user docs from developer docs

---

## Content Health Criteria

| Criterion | Check |
|-----------|-------|
| **Accuracy** | Is information current and correct? |
| **Completeness** | Does it cover the topic fully? |
| **Clarity** | Is it easy to understand? |
| **Conciseness** | Is it too long or wordy? |
| **Consistency** | Does it match site style? |
| **Currency** | Version numbers correct? |

---

## Action Codes

- ✅ **Keep** - Good as is
- ✏️ **Edit** - Minor fixes needed
- 🔄 **Revise** - Major rewrite needed
- 🔗 **Merge** - Combine with another doc
- 🗑️ **Archive** - Remove from nav
- ➕ **Create** - New doc needed

---

## Output Format

1. **Content inventory table** with status and actions
2. **Proposed navigation** in YAML format
3. **Priority fixes** ranked list
4. **Implementation phases**:
   - Phase 1: Quick wins (< 1 hour)
   - Phase 2: Content edits (1-3 hours)
   - Phase 3: Major revisions (future)

---

## Project-Specific Notes

### aiterm Documentation Structure

Current navigation has 8 top-level sections (recently reorganized):
- Home, Get Started, Reference Card, Features
- Integrations, Reference, Guides, Development

### Key Integration Areas
- Claude Code (hooks, approvals, commands)
- MCP Servers (configuration, testing)
- OpenCode (agents, keybinds)
- Gemini CLI (reference, workflow)

### Known Issues from Recent Audit
- Some v0.2.0 references may still exist (should say v0.3.x)
- Potential duplicates in troubleshooting content
- Multiple reference cards that could be consolidated

### Style Guidelines
- Use tables over long paragraphs
- Include copy-paste code examples
- Start sections with "What" and "Why"
- Max 3-4 paragraphs before a heading
