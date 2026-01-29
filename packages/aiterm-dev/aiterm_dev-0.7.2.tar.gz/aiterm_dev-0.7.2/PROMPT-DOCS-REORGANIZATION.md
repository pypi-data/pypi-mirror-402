# Documentation Reorganization & Content Revision Prompt

**Use this prompt with Claude Code or any AI assistant to reorganize AND maintain documentation sites.**

---

## The Complete Prompt

```
You are a documentation architect and technical editor specializing in ADHD-friendly information design.

## Task
Review, reorganize, and improve the documentation website for [PROJECT NAME].

## Scope (Select all that apply)
- [ ] **Navigation Reorganization** - Restructure site navigation
- [ ] **Content Audit** - Identify outdated, duplicate, or missing content
- [ ] **Content Editing** - Revise and improve existing content
- [ ] **Content Consolidation** - Merge overlapping documents
- [ ] **Gap Analysis** - Identify missing documentation
- [ ] **Style Consistency** - Align tone, formatting, and structure

## Current State
- Site URL: [URL]
- Framework: [mkdocs/docusaurus/etc]
- Total doc files: [number]
- Last major revision: [date or "unknown"]
- Known issues: [list any pain points]

## Navigation (if reorganizing)
Current nav structure:
[paste mkdocs.yml nav section]

## Content Concerns (if editing/auditing)
- Outdated content: [list files or topics]
- Duplicate content: [list overlapping docs]
- Missing topics: [what should be documented but isn't]
- Inconsistent sections: [formatting issues]

---

## PART 1: Navigation Reorganization

### ADHD-Friendly Design Principles
1. Maximum 6-7 top-level navigation sections
2. Progressive disclosure (basics first, details later)
3. Visual hierarchy with icons and clear labels
4. Quick access to reference/cheat sheets
5. Separate user docs from developer docs

### Deliverables
1. Analysis of current navigation issues
2. Proposed nav structure in YAML format
3. Before/After comparison
4. Implementation phases (quick wins → long-term)

---

## PART 2: Content Audit & Revision

### Content Health Check
For each document, evaluate:

| Criterion | Check |
|-----------|-------|
| **Accuracy** | Is information current and correct? |
| **Completeness** | Does it cover the topic fully? |
| **Clarity** | Is it easy to understand? |
| **Conciseness** | Is it too long or wordy? |
| **Consistency** | Does it match site style? |
| **Currency** | When was it last updated? |

### Content Actions
For each document, recommend one of:
- ✅ **Keep** - Good as is
- ✏️ **Edit** - Minor revisions needed
- 🔄 **Revise** - Major rewrite needed
- 🔗 **Merge** - Combine with another doc
- 🗑️ **Archive** - Move out of main nav
- ➕ **Create** - New doc needed

### Deliverables
1. Content inventory table with status
2. Priority ranking (what to fix first)
3. Specific revision recommendations
4. Suggested new content to create

---

## PART 3: Content Writing & Editing

### Writing Standards
When editing or creating content:

1. **ADHD-Friendly Format**
   - Start with "What" and "Why" (not history)
   - Use tables over paragraphs
   - Include copy-paste examples
   - Add "Quick Start" sections
   - Use bullet points over prose

2. **Structure**
   - H1: Page title only
   - H2: Major sections
   - H3: Subsections
   - Max 3-4 paragraphs before a heading

3. **Code Examples**
   - Always include working examples
   - Show expected output
   - Add comments for complex code

4. **Cross-References**
   - Link related topics
   - Add "See Also" sections
   - Use relative links

### Deliverables
1. Edited content with track changes or diff
2. New content drafts
3. Style guide recommendations

---

## PART 4: Ongoing Maintenance Plan

### Regular Tasks
| Frequency | Task |
|-----------|------|
| Monthly | Check for outdated version numbers |
| Quarterly | Review analytics for unused pages |
| Per Release | Update changelog and feature docs |
| Annually | Full content audit |

### Quality Checklist
Before publishing any doc:
- [ ] All code examples tested
- [ ] Links validated
- [ ] Version numbers current
- [ ] Screenshots up to date
- [ ] Consistent with style guide

---

## Output Format
- Use tables for comparisons and inventories
- Use code blocks for YAML and examples
- Provide actionable next steps
- Break work into phases:
  - Phase 1: Quick wins (< 1 hour)
  - Phase 2: Content edits (1-3 hours)
  - Phase 3: Major revisions (future sessions)
```

---

## Quick Templates

### Navigation Only
```
Reorganize docs navigation for [PROJECT]. Max 7 sections, ADHD-friendly.
Current nav: [paste mkdocs.yml]
Issues: [list problems]
Output: New nav YAML + implementation steps.
```

### Content Audit Only
```
Audit documentation for [PROJECT].
Files: [list or "all docs/*.md"]
Check for: outdated info, duplicates, gaps, inconsistencies.
Output: Inventory table with actions (keep/edit/revise/merge/archive).
```

### Content Editing Only
```
Edit [FILE] for clarity and ADHD-friendliness.
Current issues: [what's wrong]
Standards: tables over prose, examples, quick start sections.
Output: Revised content or specific edits to make.
```

### Full Review
```
Complete documentation review for [PROJECT].
1. Audit all content
2. Reorganize navigation
3. Identify gaps
4. Prioritize fixes
Output: Action plan with phases.
```

---

## Example: aiterm Content Audit Request

```
Audit documentation for aiterm (https://data-wise.github.io/aiterm/).

## Files to Review
- 52 markdown files in docs/
- Focus on: getting-started/, guide/, reference/

## Check For
1. Outdated version numbers (should be 0.3.8)
2. Duplicate content between files
3. Missing documentation for new features
4. Inconsistent formatting

## Output
1. Content inventory table with status
2. Top 5 priority fixes
3. List of files to merge
4. Suggested new docs to create
```

---

## Content Inventory Template

Use this table format for audits:

| File | Status | Action | Priority | Notes |
|------|--------|--------|----------|-------|
| `QUICK-START.md` | ✅ Current | Keep | - | Good |
| `guide/profiles.md` | ⚠️ Outdated | Edit | High | Update for v0.3.8 |
| `reference/REFCARD-MCP.md` | 📝 Incomplete | Revise | Medium | Add new commands |
| `getting-started/quickstart.md` | 🔗 Duplicate | Merge | Low | Merge into QUICK-START |

---

## Revision Tracking

When editing content, use this format:

```markdown
## Revision Log

| Date | Change | By |
|------|--------|-----|
| 2025-12-28 | Reorganized navigation | Claude |
| 2025-12-28 | Updated version refs to 0.3.8 | Claude |
| TBD | Merge troubleshooting files | - |
| TBD | Add MCP setup tutorial | - |
```

---

## Tips for Best Results

### For Navigation
- Include current nav structure
- List specific pain points
- State what should be prominent

### For Content Audits
- Specify files or directories to review
- Mention known outdated areas
- Include version numbers to check

### For Editing
- Provide context on audience (beginners? experts?)
- Note any style guides to follow
- Specify ADHD-friendly requirements

### For Ongoing Maintenance
- Ask for a maintenance schedule
- Request automation suggestions
- Include CI/CD integration ideas
