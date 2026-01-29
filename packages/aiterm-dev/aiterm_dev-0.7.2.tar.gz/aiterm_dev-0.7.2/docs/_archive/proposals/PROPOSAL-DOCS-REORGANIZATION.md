# Docs Website Reorganization Proposal

**Generated:** 2025-12-28
**Context:** aiterm documentation site (https://data-wise.github.io/aiterm/)

## Overview

This proposal reorganizes the aiterm documentation for ADHD-friendly navigation with clear separation of integrations (MCP, Claude, OpenCode, Gemini).

---

## Current Issues

### Navigation Problems

| Issue | Impact |
|-------|--------|
| **12 top-level sections** | Analysis paralysis - too many choices |
| **Duplicate content** | Quick Start AND Getting Started |
| **MCP buried in Features** | Key feature hard to find |
| **Reference has 12 items** | Overwhelming submenu |
| **Gemini as separate section** | Inconsistent with other integrations |
| **Documentation Automation** | Internal docs mixed with user docs |

### Current Structure (Too Complex)

```
Home                          # ✓ Keep
Quick Start                   # ✗ Merge with Getting Started
Getting Started               # ✓ Keep (merge Quick Start into it)
Reference Card                # ✓ Keep as hero link
Documentation Index           # ✗ Remove (meta, not useful)
Installation (3)              # ✗ Merge into Getting Started
User Guide (10)               # ✗ Too many items
Reference (12)                # ✗ Way too many items
Guides (4)                    # ✓ Keep but rename
Gemini CLI (4)                # ✗ Move to Integrations
Features (2)                  # ✗ Rename/restructure
Architecture (7)              # ✗ Move to Development
Documentation Automation (5)  # ✗ Move to Development or remove
```

---

## Proposed Structure (ADHD-Friendly)

### Design Principles

1. **Max 6-7 top-level sections** (cognitive load limit)
2. **Progressive disclosure** - basics first, details later
3. **Integration hub** - all AI tools in one place
4. **Quick access** - refcard and essentials prominent
5. **Visual hierarchy** - icons and clear labels

### New Navigation

```yaml
nav:
  # ============================================
  # TIER 1: ESSENTIALS (Quick Access)
  # ============================================
  - Home: index.md
  - Get Started:
      - Quick Install: QUICK-START.md
      - First Steps: GETTING-STARTED.md
      - Shell Completion: guide/shell-completion.md
  - Reference Card: REFCARD.md

  # ============================================
  # TIER 2: CORE FEATURES
  # ============================================
  - Features:
      - Context Detection: guide/context-detection.md
      - Profile Switching: guide/profiles.md
      - Status Bar: guide/status-bar.md
      - Session Coordination: guide/sessions.md
      - IDE Integration: guide/ide-integration.md
      - Workflows & Triggers: guide/workflows.md

  # ============================================
  # TIER 3: INTEGRATIONS (Separate Menu!)
  # ============================================
  - Integrations:
      - Overview: guides/AITERM-INTEGRATION.md
      - Claude Code:
          - Guide: guide/claude-integration.md
          - Commands: reference/REFCARD-CLAUDE.md
          - Tutorial: CLAUDE-CODE-TUTORIAL.md
          - Capabilities: reference/CLAUDE-CODE-CAPABILITIES.md
      - MCP Servers:
          - Guide: MCP-INTEGRATION.md
          - Commands: reference/REFCARD-MCP.md
          - Server Setup: reference/REFCARD-MCP.md#configuration
      - OpenCode:
          - Guide: reference/REFCARD-OPENCODE.md
          - Agent Testing: guides/OPENCODE-AGENT-TESTING.md
      - Gemini CLI:
          - Reference: gemini-cli/GEMINI_REFCARD.md
          - Tutorial: gemini-cli/GEMINI_TUTORIAL.md
          - ADHD Prompts: gemini-cli/PROMPT_ENGINEERING_ADHD.md

  # ============================================
  # TIER 4: REFERENCE (Streamlined)
  # ============================================
  - Reference:
      - All Commands: reference/commands.md
      - Configuration: reference/configuration.md
      - Context Types: reference/REFCARD-CONTEXT.md
      - Hooks: reference/REFCARD-HOOKS.md
      - Sessions: reference/REFCARD-SESSIONS.md
      - IDE Reference: reference/REFCARD-IDE.md
      - Troubleshooting: reference/troubleshooting.md

  # ============================================
  # TIER 5: GUIDES (Tutorials & Deep Dives)
  # ============================================
  - Guides:
      - Complete User Guide: guides/AITERM-USER-GUIDE.md
      - Git Worktrees: guides/GIT-WORKTREES-GUIDE.md
      - Video Walkthrough: guides/VIDEO-WALKTHROUGH.md

  # ============================================
  # TIER 6: DEVELOPERS ONLY
  # ============================================
  - Development:
      - Architecture: architecture/AITERM-ARCHITECTURE.md
      - Technical Design: reference/ARCHITECTURE.md
      - API Reference: api/AITERM-API.md
      - Contributing: development/contributing.md
```

---

## Key Changes Summary

| Before | After | Reason |
|--------|-------|--------|
| 12 top-level sections | 7 sections | Reduce cognitive load |
| Quick Start + Getting Started | Get Started (unified) | Eliminate confusion |
| MCP in Features | Integrations > MCP Servers | Prominent placement |
| Gemini as separate section | Integrations > Gemini CLI | Consistent pattern |
| Reference (12 items) | Reference (7 items) | Streamlined |
| Documentation Automation | Remove from nav | Internal-only |
| AITERM-DOCS-INDEX.md | Remove | Meta document |
| Architecture scattered | Development section | Developer zone |

---

## ADHD-Friendly Improvements

### Quick Wins

1. **Hero Refcard Link** - Keep REFCARD.md at top level for instant access
2. **Tab Navigation** - Already enabled, keep it
3. **Search** - Already good, no changes
4. **Code Copy** - Already enabled

### Medium Effort

1. **Breadcrumbs** - Add `navigation.path` feature
2. **Section Icons** - Add icons to nav sections
3. **Table of Contents** - Add right-side ToC
4. **Expand/Collapse** - Add `navigation.expand`

### Enhanced Features

```yaml
theme:
  features:
    # Existing (keep)
    - navigation.instant
    - navigation.tracking
    - navigation.tabs
    - navigation.sections
    - navigation.top
    - search.suggest
    - search.highlight
    - content.code.copy
    - content.code.annotate
    # NEW additions
    - navigation.path          # Breadcrumbs
    - navigation.expand        # Auto-expand current section
    - toc.integrate            # ToC in navigation
    - content.tabs.link        # Sync tabs across page
```

---

## Content Cleanup

### Files to Remove from Nav

| File | Reason | Action |
|------|--------|--------|
| `AITERM-DOCS-INDEX.md` | Meta index | Keep file, remove from nav |
| `AUTO-UPDATE-*.md` (5 files) | Internal docs | Keep files, remove from nav |
| `DOCS-HELPERS.md` | Internal | Keep file, remove from nav |
| `AITERM-IMPLEMENTATION-SUMMARY.md` | Internal | Move to Development |

### Files to Consolidate

| Files | Into |
|-------|------|
| `QUICK-START.md` + `getting-started/quickstart.md` | Keep both (different depths) |
| `reference/troubleshooting.md` + `troubleshooting/AITERM-TROUBLESHOOTING.md` | Merge into one |
| `guide/workflows.md` + `guide/triggers.md` | Merge |

---

## Visual Improvements

### Section Icons (mkdocs-material)

```yaml
nav:
  - " Home": index.md
  - " Get Started":
      - Quick Install: QUICK-START.md
  - " Reference": REFCARD.md
  - " Features":
      - ...
  - " Integrations":
      - " Claude Code": ...
      - " MCP Servers": ...
      - " OpenCode": ...
      - " Gemini CLI": ...
  - " Reference":
      - ...
  - " Guides":
      - ...
  - " Development":
      - ...
```

### Color Coding (CSS)

Add to `stylesheets/extra.css`:

```css
/* Integration section highlighting */
.md-nav__item--nested:has([href*="integrations"]) > .md-nav__link {
  border-left: 3px solid var(--md-primary-fg-color);
}

/* Quick access items */
.md-nav__link[href*="REFCARD"] {
  font-weight: 600;
}
```

---

## Implementation Steps

### Phase 1: Navigation Reorganization (30 min) ✅ DONE

1. [x] Update `mkdocs.yml` with new nav structure
2. [x] Remove Documentation Automation from nav
3. [x] Remove AITERM-DOCS-INDEX from nav
4. [x] Test locally with `mkdocs serve`

### Phase 2: Content Consolidation (1-2 hours)

1. [ ] Merge troubleshooting files:
   - `reference/troubleshooting.md` + `troubleshooting/AITERM-TROUBLESHOOTING.md`
   - Keep one comprehensive file
2. [ ] Merge workflows + triggers:
   - `guide/workflows.md` + `guide/triggers.md`
   - Combine into single workflows guide
3. [ ] Review duplicate getting-started content:
   - `QUICK-START.md` vs `getting-started/quickstart.md`
   - Differentiate or merge

### Phase 3: Content Audit & Editing (2-3 hours)

1. [ ] Version number sweep - ensure all refs are 0.3.8
2. [ ] Review outdated content in:
   - `guides/AITERM-USER-GUIDE.md` (large file - 1500+ lines)
   - `CLAUDE-CODE-TUTORIAL.md` (3200+ lines - needs chunking?)
3. [ ] Add missing content:
   - [ ] MCP server setup tutorial (step-by-step)
   - [ ] Session coordination examples
   - [ ] IDE integration screenshots
4. [ ] Standardize formatting:
   - [ ] Ensure all pages have intro paragraph
   - [ ] Add "See Also" sections where missing
   - [ ] Check code examples are tested

### Phase 4: Navigation Enhancements (future)

1. [ ] Add `navigation.path` feature (breadcrumbs)
2. [ ] Add section icons to nav
3. [ ] Add `toc.integrate` feature
4. [ ] Add breadcrumbs CSS styling

### Phase 5: Ongoing Maintenance (ongoing)

1. [ ] Create content revision log
2. [ ] Set up monthly version check
3. [ ] Document style guide for contributors

---

## Recommended Path

Start with **Phase 1** because it requires only changing `mkdocs.yml` - zero content changes. This gives immediate improvement with minimal risk.

## Next Steps

1. [ ] Review this proposal
2. [ ] Apply Phase 1 changes to mkdocs.yml
3. [ ] Preview locally and verify
4. [ ] Deploy to GitHub Pages
5. [ ] Consider Phase 2 in next session

---

## Content Inventory (Priority Items)

| File | Status | Action | Priority | Notes |
|------|--------|--------|----------|-------|
| `QUICK-START.md` | ✅ Current | Keep | - | Good |
| `GETTING-STARTED.md` | ✅ Current | Keep | - | v0.3.8 updated |
| `REFCARD.md` | ✅ Current | Keep | - | v0.3.8 updated |
| `index.md` | ✅ Current | Keep | - | v0.3.8 updated |
| `reference/troubleshooting.md` | 🔗 Duplicate | Merge | Medium | Merge with AITERM-TROUBLESHOOTING |
| `troubleshooting/AITERM-TROUBLESHOOTING.md` | 🔗 Duplicate | Merge | Medium | Into reference/troubleshooting |
| `guide/workflows.md` | 🔗 Related | Merge | Low | Combine with triggers.md |
| `guide/triggers.md` | 🔗 Related | Merge | Low | Into workflows.md |
| `getting-started/quickstart.md` | 🔗 Duplicate | Review | Low | Overlaps QUICK-START.md |
| `guides/AITERM-USER-GUIDE.md` | ⚠️ Large | Review | Medium | 1500+ lines - consider chunking |
| `CLAUDE-CODE-TUTORIAL.md` | ⚠️ Large | Review | Medium | 3200+ lines - consider chunking |
| `MCP-INTEGRATION.md` | 📝 Incomplete | Expand | High | Add setup tutorial |
| `guide/sessions.md` | 📝 New | Expand | Medium | Add examples |
| `guide/ide-integration.md` | 📝 New | Expand | Low | Add screenshots |

### Files Removed from Nav (Internal)

These files still exist but are not shown in navigation:

| File | Reason |
|------|--------|
| `AITERM-DOCS-INDEX.md` | Meta index, not user-facing |
| `AUTO-UPDATE-*.md` (5 files) | Internal automation docs |
| `DOCS-HELPERS.md` | Internal tooling |
| `development/architecture.md` | Duplicate of main architecture |

---

## Before/After Comparison

### Before (12 sections, complex)
```
Home | Quick Start | Getting Started | Reference Card | Documentation Index
Installation | User Guide | Reference | Guides | Gemini CLI | Features
Architecture | Documentation Automation
```

### After (7 sections, clean)
```
Home | Get Started | Reference Card | Features | Integrations | Reference
Guides | Development
```

**Result:** 42% fewer top-level choices, clear integration hub, developer section isolated.
