# Craft Plugin Documentation Enhancement Proposal

**Date:** 2025-12-31
**Project:** aiterm
**Plugin:** craft (Claude Code)

---

## Current State Analysis

### Existing Commands Review

#### Documentation Commands (`/craft:docs:*`)

| Command | Purpose | Strength | Enhancement Opportunity |
|---------|---------|----------|------------------------|
| `update` | Smart documentation generator | ⭐⭐⭐⭐⭐ Full 5-phase cycle | Add website integration |
| `guide` | Orchestrated guide generator | ⭐⭐⭐⭐⭐ Complete workflow | Add template variants |
| `demo` | VHS tape generator | ⭐⭐⭐⭐ Good templates | Add more demo types |
| `claude-md` | CLAUDE.md updater | ⭐⭐⭐ Works well | Add auto-detection |
| `sync` | Change detection | ⭐⭐⭐⭐ Smart classifier | Already used by `update` |
| `check` | Validation & auto-fix | ⭐⭐⭐ Basic validation | Add more checks |
| `mermaid` | Diagram generator | ⭐⭐⭐⭐ Good templates | Add more diagram types |
| `tutorial` | Tutorial generator | ⭐⭐⭐⭐ Comprehensive | Add interactive elements |
| `changelog` | Changelog updater | ⭐⭐⭐ Works | Add conventional commits |

**Total:** 13+ documentation commands

#### Site Commands (`/craft:site:*`)

| Command | Purpose | Strength | Enhancement Opportunity |
|---------|---------|----------|------------------------|
| `status` | Site health dashboard | ⭐⭐⭐⭐⭐ Comprehensive | Add CI/CD integration |
| `update` | Update site from code | ⭐⭐⭐⭐ Smart detection | Add more update types |
| `create` | Create new site | ⭐⭐⭐ Basic setup | Add more frameworks |
| `deploy` | Deploy to hosting | ⭐⭐⭐ GitHub Pages | Add more hosts |
| `build` | Build site | ⭐⭐ Basic wrapper | Add optimization |
| `preview` | Local preview | ⭐⭐ Basic wrapper | Add live reload |
| `check` | Validation | ⭐⭐⭐ Link checking | Add more validations |
| `nav` | Navigation manager | ⭐⭐⭐⭐ Smart updates | Add auto-organization |
| `theme` | Theme management | ⭐⭐⭐ Good presets | Add more themes |
| `audit` | Site audit | ⭐⭐⭐ Comprehensive | Add SEO checks |
| `consolidate` | Merge duplicate content | ⭐⭐⭐ Smart detection | Add conflict resolution |
| `add` | Add new page | ⭐⭐⭐ Template-based | Add more templates |

**Total:** 14+ site commands

---

## Key Strengths to Preserve

### 1. ADHD-Friendly Design ✅
- **Single command does everything** - `/craft:docs:update` is brilliant
- **Visual progress indicators** - Clear phase tracking
- **Smart defaults** - Works without configuration
- **Clear next steps** - Always shows what to do next

### 2. Orchestration Pattern ✅
- **Multi-phase workflow** - Analyze → Generate → Validate → Update
- **Internal command composition** - Reuses smaller commands
- **Dry-run support** - Preview before committing
- **Error handling** - Auto-fix when possible

### 3. Comprehensive Coverage ✅
- **Multiple doc types** - Guide, refcard, demo, mermaid, tutorial
- **Smart detection** - Scoring algorithm determines what's needed
- **Validation** - Checks links, navigation, content
- **Integration** - Updates mkdocs.yml, README, CLAUDE.md, CHANGELOG

---

## Enhancement Opportunities

### Priority 1: Website-Specific Documentation 🎯

**Problem:** Current `/craft:docs:update` is great for general docs but doesn't optimize for website-specific needs.

**Solution:** Create `/craft:docs:website` command

```
/craft:docs:website                  # Full website optimization cycle
/craft:docs:website --analyze        # Analyze website needs only
/craft:docs:website --seo            # SEO optimization
/craft:docs:website --landing        # Optimize landing pages
```

**Workflow:**

```
┌─────────────────────────────────────────────────────────────┐
│ /craft:docs:website                                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ Phase 1: ANALYZE WEBSITE NEEDS                              │
│   ✓ Detect target audience (developers, users, both)       │
│   ✓ Identify missing landing pages                         │
│   ✓ Check navigation hierarchy                             │
│   ✓ Analyze competitor sites                               │
│                                                             │
│ Phase 2: ENHANCE LANDING PAGES                              │
│   ✓ index.md - Add hero section, feature grid              │
│   ✓ QUICK-START.md - Add visual steps                      │
│   ✓ GETTING-STARTED.md - Add progression path              │
│                                                             │
│ Phase 3: SEO OPTIMIZATION                                   │
│   ✓ Add meta descriptions to all pages                     │
│   ✓ Optimize headings (H1, H2, H3)                         │
│   ✓ Add alt text to images                                 │
│   ✓ Generate sitemap.xml                                   │
│                                                             │
│ Phase 4: VISUAL ENHANCEMENTS                                │
│   ✓ Add feature comparison tables                          │
│   ✓ Add workflow diagrams (mermaid)                        │
│   ✓ Add screenshot placeholders                            │
│   ✓ Add syntax highlighting examples                       │
│                                                             │
│ Phase 5: NAVIGATION OPTIMIZATION                            │
│   ✓ Group related pages                                    │
│   ✓ Add breadcrumbs                                        │
│   ✓ Add "Next Steps" links                                 │
│   ✓ Create reference card index                            │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Features:**
- Landing page templates (hero, features, CTA)
- SEO metadata generation
- Screenshot/GIF integration guidance
- Navigation hierarchy optimization
- Social media previews (Open Graph, Twitter Cards)

### Priority 2: Enhanced Site Integration 🔗

**Problem:** `/craft:docs:update` and `/craft:site:update` are separate, causing manual coordination.

**Solution:** Create unified workflow in `/craft:docs:update`

**Enhancement to `/craft:docs:update`:**

```diff
  ## When Invoked

  ### Step 1: Smart Detection (sync)

+ ### Step 1.5: Website Impact Analysis (NEW)
+
+ ```
+ ┌─────────────────────────────────────────────────────────────┐
+ │ Step 1.5/6: ANALYZING WEBSITE IMPACT                        │
+ ├─────────────────────────────────────────────────────────────┤
+ │                                                             │
+ │ Detected changes will affect:                               │
+ │   • Home page (feature list)                                │
+ │   • Navigation (new guide section)                          │
+ │   • Reference card index (new REFCARD-*.md)                 │
+ │   • Search index (new content)                              │
+ │                                                             │
+ │ Website updates needed:                                     │
+ │   ✓ Update index.md feature grid                            │
+ │   ✓ Add navigation entry                                    │
+ │   ✓ Update REFCARD.md links                                 │
+ │   ✓ Regenerate search index                                 │
+ │                                                             │
+ └─────────────────────────────────────────────────────────────┘
+ ```

  ### Step 2: Generate Documentation

  ...

+ ### Step 3.5: Website Integration (NEW)
+
+ ```
+ ┌─────────────────────────────────────────────────────────────┐
+ │ Step 3.5/6: INTEGRATING WITH WEBSITE                        │
+ ├─────────────────────────────────────────────────────────────┤
+ │                                                             │
+ │ Updating website pages...                                   │
+ │                                                             │
+ │ ✓ index.md - Added "Session Tracking" to features          │
+ │ ✓ REFCARD.md - Added sessions command section              │
+ │ ✓ mkdocs.yml - Added navigation entry                      │
+ │ ✓ docs/index.md - Updated "What's New" section             │
+ │                                                             │
+ │ Running /craft:site:update --auto...                        │
+ │ ✓ Updated command reference pages                          │
+ │ ✓ Updated configuration docs                               │
+ │ ✓ Validated all links                                      │
+ │                                                             │
+ └─────────────────────────────────────────────────────────────┘
+ ```
```

### Priority 3: Template Variants for Guides 📝

**Problem:** Current guide template is generic. Different doc types need different structures.

**Solution:** Add specialized guide templates

**New templates:**

1. **CLI Command Guide** (for commands with subcommands)
   ```markdown
   # Command Name

   [Hero section with demo GIF]

   ## Overview
   [What it does, why it exists]

   ## Installation
   [One-time setup]

   ## Subcommands

   ### command subcommand1
   [Description, usage, examples]

   ### command subcommand2
   [Description, usage, examples]

   ## Common Workflows
   [Multi-command sequences]

   ## Configuration
   [Config files, env vars]

   ## Advanced Usage
   [Power user features]

   ## Troubleshooting
   [Common issues]
   ```

2. **Integration Guide** (for external tool integration)
   ```markdown
   # Integration Name

   [Logo, badges, quick intro]

   ## Prerequisites
   [What you need installed]

   ## Setup
   ### Step 1: Configure [Tool]
   ### Step 2: Install [Integration]
   ### Step 3: Verify Installation

   ## How It Works
   [Mermaid architecture diagram]

   ## Usage
   [Common patterns]

   ## Configuration
   [Settings, customization]

   ## Examples
   [Real-world use cases]

   ## Troubleshooting
   ```

3. **Tutorial Guide** (step-by-step learning)
   ```markdown
   # Tutorial Name

   > **Time:** X minutes | **Level:** Beginner/Intermediate/Advanced

   ## What You'll Learn
   - Skill 1
   - Skill 2
   - Skill 3

   ## Prerequisites
   [Required knowledge, setup]

   ## Steps

   ### Step 1: [First Task]
   **Goal:** [What to achieve]

   ```bash
   # Commands
   ```

   **Verify:** [How to check success]

   ### Step 2: [Second Task]
   ...

   ## Recap
   [What was learned]

   ## Next Steps
   [Related tutorials, advanced topics]
   ```

**Usage:**
```bash
/craft:docs:guide "sessions" --template cli-command
/craft:docs:guide "GitHub Actions" --template integration
/craft:docs:guide "First PR" --template tutorial
```

### Priority 4: Enhanced Demo Types 🎬

**Problem:** Current VHS templates are good but limited to 3 types.

**Solution:** Add specialized demo templates

**New demo templates:**

1. **Installation Demo** - Show install process
2. **Error Recovery Demo** - Show fixing common errors
3. **Configuration Demo** - Show config file editing
4. **Integration Demo** - Show connecting to external tools
5. **Before/After Comparison** - Enhanced version
6. **Feature Tour** - Multi-feature showcase

**Example: Error Recovery Demo**

```tape
# Error Recovery Demo
# Shows: How to diagnose and fix common issues

Output error-recovery.gif

Set Shell "zsh"
Set FontSize 18
Set Width 1000
Set Height 600
Set Theme "Dracula"

# === TRIGGER ERROR ===
Type "ait sessions live"
Enter
Sleep 2s
# Shows: Error: No active sessions directory

# === DIAGNOSE ===
Type "ait doctor"
Enter
Sleep 3s
# Shows: Session tracking not initialized

# === FIX ===
Type "ait sessions init"
Enter
Sleep 2s
# Shows: Session tracking initialized

# === VERIFY ===
Type "ait sessions live"
Enter
Sleep 2.5s
# Shows: No active sessions (working!)

```

### Priority 5: Smart CLAUDE.md Updates 🤖

**Problem:** `/craft:docs:claude-md` requires manual invocation. Should auto-update.

**Solution:** Enhance `/craft:docs:update` to auto-update CLAUDE.md

**Enhancement:**

```diff
  ### Step 4: Update Changelog (if commits)

+ ### Step 4.5: Update CLAUDE.md (NEW)
+
+ ```
+ ┌─────────────────────────────────────────────────────────────┐
+ │ Step 4.5/6: UPDATING CLAUDE.md                              │
+ ├─────────────────────────────────────────────────────────────┤
+ │                                                             │
+ │ Smart detection enabled...                                  │
+ │                                                             │
+ │ Detected changes:                                           │
+ │   • New feature: Session Tracking                           │
+ │   • 849 tests (was 685)                                     │
+ │   • Version: 0.6.3 (was 0.6.2)                              │
+ │                                                             │
+ │ Auto-updating sections:                                     │
+ │   ✓ Current Version → v0.6.3                                │
+ │   ✓ Essential Commands → +5 session commands                │
+ │   ✓ Development → Test count updated                        │
+ │   ✓ "Just Completed" section → Session feature              │
+ │                                                             │
+ │ No manual edits needed.                                     │
+ │                                                             │
+ └─────────────────────────────────────────────────────────────┘
+ ```
```

**Auto-detection logic:**

```python
# Detect version changes
old_version = extract_version(CLAUDE.md)
new_version = extract_version(pyproject.toml)
if old_version != new_version:
    update_version_section()

# Detect new commands
old_commands = extract_commands(CLAUDE.md)
new_commands = extract_commands(src/cli/)
added_commands = new_commands - old_commands
if added_commands:
    update_commands_section(added_commands)

# Detect test count changes
old_tests = extract_test_count(CLAUDE.md)
new_tests = run("pytest --collect-only").count
if old_tests != new_tests:
    update_test_count()
```

### Priority 6: Enhanced Validation 🔍

**Problem:** `/craft:docs:check` has basic validation. Need more comprehensive checks.

**Solution:** Expand validation suite

**New validation checks:**

1. **Content Quality**
   - Check for placeholder text ("TODO", "XXX", "FIXME")
   - Verify all commands have examples
   - Check for broken code examples
   - Verify command output is recent

2. **Accessibility**
   - Image alt text present
   - Heading hierarchy (no skipped levels)
   - Link text descriptive (not "click here")
   - Table headers present

3. **SEO**
   - Meta descriptions (140-160 chars)
   - Title tags (<60 chars)
   - H1 tags (one per page)
   - Keyword density reasonable

4. **Technical**
   - Code blocks have language tags
   - Mermaid diagrams render
   - File paths exist
   - Version numbers consistent

5. **Freshness**
   - Command output is recent (<30 days)
   - Screenshots are current version
   - Links to external sites work (200 status)

**Enhanced output:**

```
┌─────────────────────────────────────────────────────────────┐
│ 🔍 COMPREHENSIVE DOCUMENTATION CHECK                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ CONTENT QUALITY                                             │
│   ✅ No placeholder text found                             │
│   ✅ All commands have examples (48/48)                     │
│   ⚠️  2 code blocks missing output verification            │
│   ✅ All command outputs recent (<30 days)                  │
│                                                             │
│ ACCESSIBILITY                                               │
│   ⚠️  3 images missing alt text                             │
│   ✅ Heading hierarchy valid                                │
│   ✅ Link text descriptive (no "click here")                │
│   ✅ All tables have headers                                │
│                                                             │
│ SEO                                                         │
│   ⚠️  5 pages missing meta descriptions                     │
│   ✅ Title tags optimal length                              │
│   ✅ One H1 per page                                        │
│   ✅ Keyword density good                                   │
│                                                             │
│ TECHNICAL                                                   │
│   ✅ All code blocks have language tags (127/127)           │
│   ✅ Mermaid diagrams render (15/15)                        │
│   ✅ File paths exist (all valid)                           │
│   ✅ Version numbers consistent                             │
│                                                             │
│ FRESHNESS                                                   │
│   ✅ Command outputs recent                                 │
│   ⚠️  1 screenshot from v0.6.2 (current: v0.6.3)            │
│   ✅ External links valid (200 status)                      │
│                                                             │
│ OVERALL SCORE: 88/100 ████████▌░                            │
│                                                             │
│ AUTO-FIXABLE: 8 issues                                      │
│ MANUAL FIXES: 3 issues                                      │
│                                                             │
│ Run with --fix to auto-correct 8 issues                    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Implementation Plan

### Phase 1: Website-Specific Documentation (Week 1)

**Goal:** Make documentation website-ready

**Tasks:**
1. Create `/craft:docs:website` command
2. Add SEO optimization phase
3. Add landing page templates
4. Add feature grid generator
5. Add screenshot placeholder system

**Deliverables:**
- `commands/docs/website.md` (new command)
- `templates/landing-hero.md`
- `templates/feature-grid.md`
- SEO metadata generator

### Phase 2: Enhanced Integration (Week 2)

**Goal:** Unify docs and site workflows

**Tasks:**
1. Add website impact analysis to `/craft:docs:update`
2. Add automatic site integration phase
3. Enhance `/craft:site:update` auto mode
4. Add cross-referencing validation
5. Add navigation consistency checks

**Deliverables:**
- Enhanced `commands/docs/update.md`
- Enhanced `commands/site/update.md`
- Website integration logic
- Cross-reference validator

### Phase 3: Template Expansion (Week 3)

**Goal:** Support diverse documentation types

**Tasks:**
1. Add CLI command guide template
2. Add integration guide template
3. Add tutorial guide template
4. Add template selector logic
5. Add template customization options

**Deliverables:**
- `templates/guide-cli-command.md`
- `templates/guide-integration.md`
- `templates/guide-tutorial.md`
- Template selection algorithm
- `/craft:docs:guide` enhancements

### Phase 4: Demo Enhancement (Week 4)

**Goal:** Richer visual documentation

**Tasks:**
1. Add 5 new demo templates
2. Add demo template selector
3. Add timing optimization
4. Add error recovery demos
5. Add comparison demos

**Deliverables:**
- 6 new VHS tape templates
- Enhanced `commands/docs/demo.md`
- Demo best practices guide

### Phase 5: Smart Automation (Week 5)

**Goal:** Reduce manual steps

**Tasks:**
1. Add auto-detection to CLAUDE.md updates
2. Add smart version tracking
3. Add test count tracking
4. Add command inventory tracking
5. Add feature completion detection

**Deliverables:**
- Auto-update logic for CLAUDE.md
- Version change detector
- Command change detector
- Enhanced `commands/docs/claude-md.md`

### Phase 6: Enhanced Validation (Week 6)

**Goal:** Comprehensive quality checks

**Tasks:**
1. Add content quality checks
2. Add accessibility checks
3. Add SEO checks
4. Add technical checks
5. Add freshness checks
6. Add auto-fix capability

**Deliverables:**
- Enhanced `commands/docs/check.md`
- Validation suite (5 categories)
- Auto-fix engine
- Validation report generator

---

## Success Metrics

### Quantitative

1. **Documentation Coverage**
   - Target: 100% of features documented
   - Current: ~85%
   - Enhancement: Auto-detection ensures no feature is missed

2. **Website Quality**
   - Target: 95+ SEO score
   - Current: ~80
   - Enhancement: SEO optimization phase

3. **Automation Level**
   - Target: 90% auto-generated content
   - Current: ~70%
   - Enhancement: Smart detection + auto-updates

4. **Validation Pass Rate**
   - Target: 95+ score on all checks
   - Current: ~85
   - Enhancement: Comprehensive validation + auto-fix

### Qualitative

1. **ADHD-Friendliness**
   - Still single command for full cycle ✅
   - Visual progress maintained ✅
   - Smart defaults enhanced ✅
   - Clear next steps always shown ✅

2. **Developer Experience**
   - Less manual coordination (docs + site unified)
   - Fewer forgotten updates (auto-detection)
   - Better validation (comprehensive checks)
   - Faster iteration (preview modes)

3. **Documentation Quality**
   - Better SEO (landing pages, metadata)
   - Better accessibility (alt text, headings)
   - Better freshness (auto-updates)
   - Better visuals (enhanced demos)

---

## Backward Compatibility

**All existing commands remain unchanged:**
- `/craft:docs:update` - Enhanced, not replaced
- `/craft:docs:guide` - Enhanced with templates
- `/craft:docs:demo` - Enhanced with more types
- `/craft:site:update` - Enhanced with auto mode

**New commands are additive:**
- `/craft:docs:website` - New, optional
- Enhanced validation - New checks, old checks preserved

**Migration path:**
- No breaking changes
- All enhancements opt-in via flags
- Existing workflows continue working
- Gradual adoption encouraged

---

## Next Steps

1. **Review this proposal** - Get feedback on priorities
2. **Refine Phase 1** - Detail the `/craft:docs:website` command
3. **Prototype** - Build Phase 1 commands
4. **Test on aiterm** - Use aiterm as test project
5. **Iterate** - Refine based on real usage
6. **Document** - Create guides for new features
7. **Release** - Ship Phase 1, plan Phase 2

---

## Questions for Review

1. **Priority Order** - Is the 6-phase plan in the right order?
2. **Scope** - Is this too ambitious? Should we focus on fewer phases?
3. **Website Focus** - Is website-specific documentation valuable enough to be Priority 1?
4. **Template Expansion** - Are the 3 proposed guide templates the right ones?
5. **Auto-Detection** - Should CLAUDE.md auto-update be more aggressive or more conservative?
6. **Validation** - Are the 5 validation categories comprehensive enough?

---

## Appendix: Current Command Inventory

### Documentation Commands (13+)

```
/craft:docs:update       - Smart documentation generator (⭐⭐⭐⭐⭐)
/craft:docs:guide        - Orchestrated guide generator (⭐⭐⭐⭐⭐)
/craft:docs:demo         - VHS tape generator (⭐⭐⭐⭐)
/craft:docs:claude-md    - CLAUDE.md updater (⭐⭐⭐)
/craft:docs:sync         - Change detection (⭐⭐⭐⭐)
/craft:docs:check        - Validation & auto-fix (⭐⭐⭐)
/craft:docs:mermaid      - Diagram generator (⭐⭐⭐⭐)
/craft:docs:tutorial     - Tutorial generator (⭐⭐⭐⭐)
/craft:docs:changelog    - Changelog updater (⭐⭐⭐)
/craft:docs:nav-update   - Navigation updater (⭐⭐⭐⭐)
/craft:docs:api          - API documentation (⭐⭐⭐)
/craft:docs:prompt       - Prompt documentation (⭐⭐⭐)
/craft:docs:site         - Site documentation (⭐⭐⭐)
```

### Site Commands (14+)

```
/craft:site:status       - Site health dashboard (⭐⭐⭐⭐⭐)
/craft:site:update       - Update site from code (⭐⭐⭐⭐)
/craft:site:create       - Create new site (⭐⭐⭐)
/craft:site:deploy       - Deploy to hosting (⭐⭐⭐)
/craft:site:build        - Build site (⭐⭐)
/craft:site:preview      - Local preview (⭐⭐)
/craft:site:check        - Validation (⭐⭐⭐)
/craft:site:nav          - Navigation manager (⭐⭐⭐⭐)
/craft:site:theme        - Theme management (⭐⭐⭐)
/craft:site:audit        - Site audit (⭐⭐⭐)
/craft:site:consolidate  - Merge duplicate content (⭐⭐⭐)
/craft:site:add          - Add new page (⭐⭐⭐)
/craft:site:init         - Initialize site (⭐⭐)
/craft:site:docs/*       - Site docs management (various)
```

**Total Commands:** 27+ documentation/site commands

---

## Summary

The craft plugin already has excellent documentation and site management commands. This proposal focuses on:

1. **Website optimization** - Make docs website-ready with SEO, landing pages, visuals
2. **Unified workflows** - Integrate docs and site updates seamlessly
3. **Template expansion** - Support diverse documentation types
4. **Enhanced demos** - Richer visual documentation options
5. **Smart automation** - Auto-detect and auto-update more content
6. **Comprehensive validation** - Catch more issues, auto-fix more problems

**Philosophy:** Preserve ADHD-friendly design, maintain backward compatibility, add value incrementally.
