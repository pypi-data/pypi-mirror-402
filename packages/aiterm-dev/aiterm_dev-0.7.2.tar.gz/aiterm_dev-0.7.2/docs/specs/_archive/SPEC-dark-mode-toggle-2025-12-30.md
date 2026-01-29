# Spec: Dark Mode Toggle

**Status:** implemented
**Created:** 2025-12-30
**From Brainstorm:** BRAINSTORM-dark-mode-toggle-2025-12-30.md

---

## Overview

Add dark mode toggle to aiterm documentation site, allowing developers to switch between light and dark themes with preference persistence.

---

## User Stories

### Primary Story

**As a** developer using aiterm docs
**I want** to toggle between light and dark mode
**So that** I can reduce eye strain during extended documentation reading

### Acceptance Criteria

- [x] Toggle switch visible in docs header/navigation
- [x] Theme applies immediately without page reload
- [x] Preference persists across browser sessions (localStorage: `aiterm-theme`)
- [x] Respects system preference on first visit (if no saved preference)

---

## Technical Requirements

### Architecture

```
User clicks toggle
       ↓
Update localStorage('theme')
       ↓
Apply CSS class to <html> or <body>
       ↓
CSS variables swap colors
```

### CSS Variables

| Variable | Light | Dark |
|----------|-------|------|
| `--bg-primary` | #ffffff | #1a1a2e |
| `--text-primary` | #333333 | #e0e0e0 |
| `--accent` | #2563eb | #60a5fa |
| `--border` | #e5e7eb | #374151 |

### Storage

- **Key:** `aiterm-theme`
- **Values:** `light`, `dark`, `high-contrast`, `sepia`, `system`
- **Default:** `system` (follows OS preference)

### Theme Options (Claude Code Pattern)

```
Default: System (auto-detect) ← shown first
─────────────────────────────
Alternatives:
  • Light - Clean white background
  • Dark - Easy on eyes at night
  • High Contrast - Accessibility focus
  • Sepia - Warm, paper-like
```

### Dependencies

- MkDocs Material theme (already in use)
- No additional libraries required

---

## UI/UX Specifications

### Toggle Location

```
┌────────────────────────────────────────────┐
│ aiterm docs    [nav] [nav]    [🌙/☀️]     │
└────────────────────────────────────────────┘
                                  ↑
                            Theme toggle
```

### Behavior

1. Click toggles between light ↔ dark
2. Icon changes: ☀️ (light mode) / 🌙 (dark mode)
3. Smooth transition (0.2s ease)

### Accessibility

- [x] Toggle has aria-label (via MkDocs Material)
- [x] Color contrast meets WCAG AA (4.5:1) - high-contrast theme available
- [x] Focus ring visible on toggle (MkDocs Material built-in)
- [x] Respects prefers-reduced-motion (via extra.css)

---

## Open Questions

- [x] Use MkDocs Material built-in palette toggle? → Yes, simpler
- [x] Support multiple color themes beyond light/dark? → Yes, add high-contrast + sepia
- [x] Code syntax highlighting colors? → Use MkDocs Material defaults (built-in)
- [x] Follow Claude Code pattern? → Yes, default first + alternatives menu

---

## Review Checklist

- [x] Acceptance criteria are testable
- [x] Technical requirements are complete
- [x] Dependencies identified
- [x] No blocking open questions (all 4 resolved)
- [x] UI/UX specs reviewed

**Approved:** 2025-12-30
**Implemented:** 2025-12-30

---

## Implementation Notes

### Files Modified

| File | Change |
|------|--------|
| `mkdocs.yml` | Added 4-theme palette toggle (auto, light, dark, high-contrast) |
| `docs/stylesheets/extra.css` | Added high-contrast theme CSS variables |
| `docs/javascripts/theme-toggle.js` | Added localStorage persistence with `aiterm-theme` key |

### Theme Cycle

```
Auto → Light → Dark → High Contrast → Auto...
 ☀️     🌙      🌓        ◐           ☀️
```

### Testing

Run locally: `mkdocs serve`
Then click the toggle icon in the header to cycle through themes.
