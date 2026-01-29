# Aiterm Website Documentation Enhancements - Feature Brainstorm

**Date:** 2025-12-31
**Focus:** Feature (ADHD-optimized documentation website)
**Depth:** Deep (8 expert questions)
**Primary User:** ADHD developers
**Duration:** < 10 minutes

---

## 🎯 Executive Summary

Transform the aiterm documentation site at https://data-wise.github.io/aiterm/ into an **exemplary ADHD-friendly technical documentation model**. The site has a solid foundation but needs enhanced visual hierarchy, workflow visualization, and reduced cognitive load for ADHD users.

**Key Goal:** Reduce time-to-first-success from ~15 minutes to **< 5 minutes** for new users.

---

## 📊 Context from Expert Questions

### Decisions Made

| Question | Answer | Impact |
|----------|--------|--------|
| **Priority** | All phases sequentially | 2-week implementation timeline |
| **Primary User** | ADHD developers | Optimize for visual hierarchy, time estimates, quick wins |
| **Navigation** | Flatten ADHD guide to top-level | Increase discoverability of ADHD features |
| **Diagrams** | Visual Workflows page + embed + interactive | Multi-channel diagram distribution |
| **Phase 1 Done** | All mermaid errors fixed | Clear, measurable completion criterion |
| **Metrics** | Tutorial completion rate | Track % finishing getting-started tutorial |
| **Content Density** | TL;DR boxes everywhere | 30-second summaries at top of all pages |
| **Mobile** | Fix mermaid overflow first | Horizontal scroll for diagrams on mobile |

---

## ⚡ Quick Wins (< 30 min each)

### 1. Fix Mermaid Syntax Errors (CRITICAL)
**Time:** 15 minutes
**Benefit:** Diagrams render correctly, no "Syntax error in text" messages
**Implementation:**
```yaml
# mkdocs.yml - Verify mermaid configuration
markdown_extensions:
  - pymdownx.superfences:
      custom_fences:
        - name: mermaid
          class: mermaid
          format: !!python/name:pymdownx.superfences.fence_code_format

extra_javascript:
  - https://unpkg.com/mermaid@10/dist/mermaid.min.js
```

**Files to check:**
- All `.md` files with ` ```mermaid` blocks
- Look for missing closing tags, syntax issues
- Test rendering with `mkdocs serve`

### 2. Add TL;DR Box Template
**Time:** 20 minutes
**Benefit:** Every page scannable in < 30 seconds
**Template:**
```markdown
> **TL;DR** (30 seconds)
> - **What:** [One sentence]
> - **Why:** [One benefit]
> - **How:** [One command or link]
> - **Next:** [One next step]
```

**Apply to:**
- `index.md` (homepage)
- `QUICK-START.md`
- `GETTING-STARTED.md`
- All guide pages under `docs/guide/`

### 3. Add Time Estimates to All Tutorials
**Time:** 15 minutes
**Benefit:** Users know commitment upfront (ADHD-critical)
**Format:**
```markdown
### Tutorial Name
⏱️ **10 minutes** • 🟢 Beginner • ✓ 7 steps
```

**Files:**
- `docs/tutorials/getting-started/index.md`
- `docs/tutorials/intermediate/index.md`
- `docs/tutorials/advanced/index.md`
- All tutorial step pages

### 4. Create ADHD Quick Start Card
**Time:** 25 minutes
**Benefit:** New top-level page for ADHD users
**Location:** `docs/ADHD-QUICK-START.md`
**Content:**
```markdown
# ADHD Quick Start

> Get started in **under 2 minutes** with aiterm

## ⏱️ First 30 Seconds
```bash
ait doctor    # Check installation
ait detect    # See project type
ait switch    # Apply visual context
```

## ⏱️ Next 5 Minutes
- Interactive tutorial: `ait learn start`
- View settings: `ait claude settings`
- See status: `ait statusline render`

## 🆘 Stuck?
- Diagnose: `ait doctor`
- Help: `ait --help`
- Detailed info: `ait info --json`
```

---

## 🔧 Medium Effort (1-2 hours each)

### 5. Create Visual Workflows Page
**Time:** 90 minutes
**Benefit:** Central hub for all workflow diagrams
**Location:** `docs/workflows/index.md`
**Structure:**
```markdown
# Visual Workflows

Quick visual guides to aiterm's core workflows.

## 🚀 Getting Started
[Embed: User Onboarding Journey mermaid diagram]

## 🎯 Daily Workflows
[Embed: ADHD-Optimized Daily Workflow diagram]

## 🔍 Feature Discovery
[Embed: Complete Feature Decision Tree diagram]

## 🎨 Context Detection
[Embed: Context Detection System diagram]

## 📦 Release Process
[Embed: Release Workflow diagram]
```

**Make interactive:**
- Add click handlers to nodes (future: link to docs)
- Add zoom/pan controls
- Add diagram export buttons

### 6. Flatten Navigation Hierarchy
**Time:** 60 minutes
**Benefit:** ADHD features discoverable at top level
**Changes to `mkdocs.yml`:**
```yaml
nav:
  - Home: index.md
  - 🚀 Quick Start: QUICK-START.md
  - 🧠 ADHD Guide: ADHD-QUICK-START.md  # NEW - promoted from gemini-cli/
  - 📊 Visual Workflows: workflows/index.md  # NEW
  - 📚 Reference Card: REFCARD.md
  - 🎓 Tutorials:
      - Overview: tutorials/index.md
      - Getting Started: tutorials/getting-started/index.md
      - Intermediate: tutorials/intermediate/index.md
      - Advanced: tutorials/advanced/index.md
  - Features: [...]
  - Integrations: [...]
  - Reference: [...]
  - Development: [...]
```

### 7. Add Visual Callout Boxes
**Time:** 75 minutes
**Benefit:** Important info stands out visually
**Template:**
```markdown
> 💡 **Pro Tip:** [Helpful insight]

> ⚠️ **Warning:** [Important caution]

> ✅ **Success:** [Positive outcome indicator]

> 🎯 **ADHD-Friendly:** [Specific ADHD optimization]
```

**Apply to:**
- Installation guides (warnings about permissions)
- Command references (pro tips for power users)
- Tutorials (success indicators after each step)

### 8. Homepage Restructure (Card-Based Layout)
**Time:** 120 minutes
**Benefit:** Visual hierarchy, reduce cognitive load
**New `docs/index.md` structure:**
```markdown
# aiterm

> AI-powered terminal optimizer for Claude Code and Gemini CLI workflows

[Large hero section with 3 CTA buttons]
[Quick Start] [Learn System] [Reference]

## Choose Your Path

<div class="grid cards" markdown>

-   🚀 **Quick Setup**

    Get started in 5 minutes

    [Install & Configure →](QUICK-START.md)

-   🎓 **Learn System**

    30-minute interactive tutorials

    [Start Learning →](tutorials/index.md)

-   📚 **Find Command**

    Instant command lookup

    [Reference Card →](REFCARD.md)

-   🧠 **ADHD Guide**

    Optimized for ADHD users

    [ADHD Features →](ADHD-QUICK-START.md)

</div>

## Core Features

<div class="grid cards" markdown>

-   🎯 **Context Detection**

    Automatically detects R, Python, Node.js projects

-   🤖 **Claude Integration**

    Seamless Claude Code CLI integration

-   🎨 **Visual Customization**

    iTerm2 and Ghostty terminal themes

-   ⚡ **Workflow Automation**

    Release, feature, and session management

</div>
```

---

## 🏗️ Long-term (Future sessions / 3+ hours)

### 9. Interactive Mermaid Diagrams
**Time:** 4-6 hours
**Benefit:** Click nodes to navigate to docs
**Technology:**
- Use `mermaid.js` API for click events
- Add custom JavaScript to process diagram clicks
- Link each node to relevant documentation page

**Example:**
```javascript
// docs/javascripts/mermaid-nav.js
document.addEventListener('DOMContentLoaded', function() {
  mermaid.initialize({
    startOnLoad: true,
    theme: 'default',
    flowchart: {
      useMaxWidth: true,
      htmlLabels: true,
      curve: 'basis'
    },
    onClick: function(nodeId) {
      // Map node IDs to documentation URLs
      const nodeMap = {
        'ait-doctor': '/reference/commands/#doctor',
        'ait-detect': '/reference/commands/#detect',
        // ... more mappings
      };
      if (nodeMap[nodeId]) {
        window.location.href = nodeMap[nodeId];
      }
    }
  });
});
```

### 10. Mobile Responsive Overhaul
**Time:** 5-8 hours
**Benefit:** Equal experience on mobile devices
**Components:**
1. **Mermaid overflow fix** (Quick win moved to medium)
   ```css
   /* docs/stylesheets/extra.css */
   .mermaid {
     overflow-x: auto;
     max-width: 100%;
   }
   @media (max-width: 768px) {
     .mermaid svg {
       max-width: 100%;
       height: auto;
     }
   }
   ```

2. **Simplified mobile navigation**
   - Collapse subsections by default
   - Add hamburger menu for deep navigation
   - Sticky quick links at bottom

3. **Touch targets**
   - Ensure 44px minimum for all buttons
   - Add padding to links in lists
   - Increase spacing between navigation items

4. **Testing matrix**
   - iPhone SE (smallest iOS device)
   - iPhone 14 Pro (standard)
   - iPad (tablet)
   - Android (Pixel 7)

### 11. Progress Indicators for Tutorials
**Time:** 3-4 hours
**Benefit:** Users know how far they've progressed
**Implementation:**
```markdown
<!-- At top of each tutorial step -->
Step 3 of 7 ████████░░░░░░░░ 43%

**You're learning:** [Current topic]
**Up next:** [Next step preview]
**Time remaining:** ~7 minutes
```

**Features:**
- Visual progress bar
- Step counter
- Time estimate
- Preview of next step (reduce anxiety)

### 12. Command Playground (Interactive Demo)
**Time:** 6-10 hours
**Benefit:** Try commands without installing
**Technology:**
- WebAssembly terminal emulator (xterm.js)
- Mock `ait` command responses
- Pre-recorded demo outputs

**MVP Features:**
- Execute `ait doctor` → Show mock health check
- Execute `ait detect` → Show mock project detection
- Execute `ait --help` → Show real help output
- Limited to safe, read-only commands

**Future:**
- Full terminal emulator
- Real command execution in sandboxed environment
- Save command history

---

## 🎯 Recommended Implementation Path

### Week 1: Phase 1 - Quick Wins

**Day 1 (2 hours):**
1. ✅ Fix all mermaid syntax errors (15 min)
2. ✅ Add TL;DR boxes to 10 major pages (60 min)
3. ✅ Add time estimates to all tutorials (15 min)
4. ✅ Create ADHD Quick Start page (25 min)
5. ✅ Test and validate (5 min)

**Acceptance:** All mermaid diagrams render without errors

**Day 2 (3 hours):**
6. ✅ Create Visual Workflows page (90 min)
7. ✅ Flatten navigation hierarchy (60 min)
8. ✅ Add visual callout boxes to guides (30 min)

**Day 3 (2 hours):**
9. ✅ Homepage restructure with cards (120 min)

### Week 2: Phase 2 - Structure

**Day 4-5 (6 hours):**
10. ✅ Mobile responsive fixes (mermaid overflow, navigation) (3 hours)
11. ✅ Progress indicators for tutorials (3 hours)

**Day 6-7 (8 hours):**
12. ✅ Interactive mermaid diagrams (6 hours)
13. ✅ Command playground MVP (2 hours)

### Week 3+: Phase 3 - Polish

**Future iterations:**
- Video walkthrough embeds
- User feedback surveys
- A/B testing different layouts
- Accessibility audit (WCAG AA)
- Performance optimization
- Search optimization

---

## 📊 Success Metrics

### Primary Metric: Time to First Success
**Target:** < 5 minutes (currently ~15 minutes)

**Measurement:**
1. User lands on homepage
2. User completes first `ait` command successfully
3. Time elapsed

**Tracking:**
- Google Analytics custom events
- Tutorial completion events
- Command execution tracking (if telemetry enabled)

### Secondary Metrics

| Metric | Current | Target | How to Measure |
|--------|---------|--------|----------------|
| Tutorial completion rate | Unknown | > 70% | Track tutorial start → finish events |
| Page bounce rate | Unknown | < 30% | Google Analytics |
| Mobile traffic | Unknown | > 20% | Google Analytics device data |
| ADHD guide views | Low (buried) | > 500/month | Page views after promotion |
| Mermaid diagram errors | 5+ | 0 | Manual validation + CI check |

---

## 🎨 ADHD-Specific Optimizations

### Visual Hierarchy Checklist

- [x] **Color coding:** 🟢 Beginner, 🔵 Intermediate, 🔴 Advanced
- [x] **Time estimates:** Every task shows duration
- [x] **Progress indicators:** Show completion percentage
- [x] **TL;DR boxes:** 30-second summaries at top
- [x] **Visual callouts:** Pro tips, warnings, success indicators
- [x] **Scannable content:** No paragraphs > 5 sentences
- [x] **Card-based layout:** Reduce dense text blocks
- [x] **Mermaid diagrams:** Visual workflow understanding

### Cognitive Load Reduction

| Technique | Implementation |
|-----------|----------------|
| **Chunking** | Break guides into 3-5 minute sections |
| **Repetition** | Key commands repeated in multiple contexts |
| **Visual cues** | Emojis for quick scanning (🚀 setup, 🎓 learn, 📚 reference) |
| **Clear paths** | "Choose Your Path" cards on homepage |
| **Escape hatches** | "Stuck? Run `ait doctor`" on every page |
| **Quick wins** | Success indicators after each step |

---

## 🔗 Integration Points

### Existing Aiterm Features

| Feature | Documentation Enhancement |
|---------|--------------------------|
| **`ait learn`** | Interactive tutorials already exist, add progress indicators |
| **`ait doctor`** | Prominently feature as troubleshooting command |
| **`ait statusline`** | Showcase in visual workflows diagram |
| **`ait feature`** | Add to release workflow diagram |
| **Context detection** | Add dedicated context detection diagram |

### External Tools

| Tool | Purpose |
|------|---------|
| **MkDocs Material** | Theme framework (already in use) |
| **Mermaid.js** | Diagram rendering (already in use) |
| **xterm.js** | Command playground (future) |
| **Google Analytics** | Metrics tracking (add if not present) |
| **VHS** | GIF demo generation (already in use) |

---

## 🚧 Technical Considerations

### Mermaid Configuration

**Current Issue:** Syntax errors in diagrams

**Root Cause:** Likely missing proper mermaid.js initialization or markdown extension config

**Fix:**
1. Verify `pymdownx.superfences` config in `mkdocs.yml`
2. Ensure mermaid.js CDN link in `extra_javascript`
3. Test each diagram individually
4. Add CSS for proper rendering

### Mobile Responsive

**Current Issue:** Diagrams overflow on small screens

**Solution:**
```css
/* Mobile-first approach */
.mermaid {
  overflow-x: auto;
  -webkit-overflow-scrolling: touch;
}

@media (max-width: 768px) {
  .mermaid svg {
    max-width: 100% !important;
    height: auto !important;
  }

  /* Collapse navigation */
  .md-nav__list {
    display: none;
  }
  .md-nav__item--active > .md-nav__list {
    display: block;
  }
}
```

### Performance

**Concerns:**
- 5 new mermaid diagrams may slow page load
- Interactive features add JavaScript overhead

**Optimizations:**
- Lazy-load diagrams below the fold
- Use mermaid.js CDN for caching
- Minimize custom JavaScript
- Compress images/GIFs

---

## 💡 Innovation Opportunities

### 1. ADHD Customization Toggle
**Idea:** Let users toggle ADHD-optimized mode

**Features:**
- Increase font size (+20%)
- Reduce content density (more whitespace)
- Highlight time estimates in bright colors
- Add more visual cues
- Persist preference in localStorage

### 2. Interactive Tutorial with Live Terminal
**Idea:** Embed terminal emulator in tutorial pages

**Benefits:**
- Users try commands without leaving docs
- No installation required for exploration
- Sandboxed environment prevents errors
- Record command history for resume

### 3. Progress Dashboard
**Idea:** Personal learning dashboard

**Features:**
- Track tutorials completed
- Show badges earned
- Estimate time to mastery
- Suggest next steps
- Share progress on social media

### 4. Voice Navigation (Accessibility++)
**Idea:** Voice commands for documentation

**Features:**
- "Show me getting started" → Navigate to guide
- "Read installation steps" → Text-to-speech
- "Search for context detection" → Trigger search
- Helps users with reading challenges

---

## 🔍 Open Questions

1. **Analytics:** Do we have Google Analytics or similar tracking?
   - If no: Should we add it to measure metrics?
   - If yes: What's current tutorial completion rate?

2. **Mermaid errors:** Are they markdown syntax or mermaid.js version issues?
   - Need to inspect browser console for errors
   - May need to update mermaid.js version

3. **Mobile usage:** What % of users access on mobile?
   - Prioritize mobile responsive if > 20%
   - May defer if usage is low

4. **User feedback:** Have ADHD users tested current docs?
   - Consider user testing before Phase 2
   - May reveal insights we're missing

5. **Command playground:** Is WebAssembly acceptable overhead?
   - Alternative: Pre-recorded GIF demos
   - Consider bandwidth constraints

---

## 📝 Next Steps

1. **Review this brainstorm** with stakeholders
2. **Create formal spec** (via `/spec:capture` workflow)
3. **Set up project board** with 3 phases as milestones
4. **Day 1 implementation** starts with mermaid fixes
5. **Continuous deployment** via GitHub Actions (already configured)

---

## 🎉 Expected Outcomes

**After Phase 1 (Week 1):**
- ✅ All mermaid diagrams render correctly
- ✅ Every page has TL;DR box
- ✅ ADHD Quick Start discoverable at top nav
- ✅ Time estimates on all tutorials
- **Impact:** 30% reduction in time-to-first-success

**After Phase 2 (Week 2):**
- ✅ Visual Workflows page live with 5 diagrams
- ✅ Flattened navigation structure
- ✅ Homepage with card-based layout
- ✅ Mobile responsive fixes deployed
- **Impact:** 50% reduction in time-to-first-success

**After Phase 3 (Week 3+):**
- ✅ Interactive diagrams with click navigation
- ✅ Progress indicators in tutorials
- ✅ Command playground MVP
- ✅ Complete mobile responsive experience
- **Impact:** 70% reduction in time-to-first-success, **< 5 minutes**

---

## 🏆 Success Definition

**This feature is successful when:**

1. **Quantitative:**
   - Time-to-first-success < 5 minutes (from ~15 minutes)
   - Tutorial completion rate > 70%
   - 0 mermaid diagram errors
   - Mobile bounce rate < 30%

2. **Qualitative:**
   - ADHD users report site is "easy to scan"
   - First-time users complete setup without asking for help
   - Homepage clearly shows path forward
   - Diagrams enhance understanding (not confuse)

3. **ADHD-Specific:**
   - Every page scannable in < 30 seconds
   - Time estimates on every task
   - Visual hierarchy supports quick scanning
   - Escape hatches available when stuck

---

**Generated:** 2025-12-31
**Brainstorm Duration:** 8 minutes (deep mode)
**Next:** Capture as formal spec → Implementation
