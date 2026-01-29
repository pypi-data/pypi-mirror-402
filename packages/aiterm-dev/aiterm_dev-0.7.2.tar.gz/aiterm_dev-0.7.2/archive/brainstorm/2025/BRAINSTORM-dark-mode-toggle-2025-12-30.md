# Brainstorm: Dark Mode Toggle

**Generated:** 2025-12-30
**Mode:** feature | **Depth:** quick
**Spec Captured:** Yes → `docs/specs/SPEC-dark-mode-toggle-2025-12-30.md`

---

## Quick Wins (< 30 min each)

1. **CSS variable system** - Define color tokens for theming
2. **Toggle component** - Simple switch in docs header
3. **localStorage persistence** - Remember user preference

## Medium Effort (1-2 hours)

- [ ] System preference detection (`prefers-color-scheme`)
- [ ] Smooth transitions between themes (CSS transitions)
- [ ] MkDocs Material theme sync

## Long-term (Future sessions)

- [ ] Multiple themes beyond light/dark
- [ ] Per-component theme overrides
- [ ] Scheduled auto-switching (time-based)

---

## User Story

**As a** developer using aiterm docs
**I want** to toggle between light and dark mode
**So that** I can reduce eye strain during extended documentation reading

---

## MVP Scope

| Include | Exclude |
|---------|---------|
| Toggle switch | Multiple themes |
| CSS variables | Per-component overrides |
| localStorage | Scheduled switching |
| System preference | Animation customization |

---

## Recommended Path

Start with MkDocs Material's built-in palette toggle feature - it handles most of this out of the box. Customize colors via CSS variables if needed.

---

## Next Steps

1. Review spec: `/spec:review dark-mode`
2. When ready: `/craft:do implement dark mode toggle`
