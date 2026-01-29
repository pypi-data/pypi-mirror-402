# Documentation CI Testing Enhancements

**Generated:** 2025-12-31
**Context:** aiterm website CI/CD

## Overview
The docs CI currently builds successfully but lacks comprehensive testing. This proposal adds validation steps to catch issues before deployment.

---

## Current State

**Working:**
- ✅ Auto-build on push/PR
- ✅ Auto-deploy to GitHub Pages
- ✅ Fast builds with `uv` (2.74s)
- ✅ Material theme with custom styling

**Missing:**
- ⚠️ Link validation
- ⚠️ Strict mode warnings as errors
- ⚠️ Navigation completeness check
- ⚠️ Screenshot/image validation

---

## Proposed Enhancements

### Option A: Minimal (Quick Win - 10 min)
Add `--strict` flag to catch warnings as errors.

**Changes to `.github/workflows/docs.yml`:**
```yaml
- name: Build documentation
  run: uv run mkdocs build --strict
```

**Benefits:**
- Catches orphaned pages
- Catches broken internal links
- No new dependencies

**Current orphaned pages:**
- `demos/README.md`
- `demos/tutorials/README.md`
- `specs/SPEC-statusline-config-ux-2025-12-31.md`
- `specs/SPEC-statusline-integration-2025-12-31.md`
- `tutorials/USER-TESTING-CHECKLIST.md`

---

### Option B: Enhanced Testing (Medium - 30 min)
Add link validation and preview deployment for PRs.

**New workflow step:**
```yaml
- name: Validate documentation
  run: |
    # Build in strict mode
    uv run mkdocs build --strict

    # Check for broken links (internal)
    find site -name "*.html" -exec grep -l "404.html" {} \; | wc -l

    # Verify all images exist
    find docs -name "*.png" -o -name "*.gif" | while read img; do
      [ -f "$img" ] || echo "Missing: $img"
    done
```

**Benefits:**
- All benefits from Option A
- Validates images exist
- Could add PR preview comments

---

### Option C: Comprehensive (Long-term - 2 hours)
Full validation suite with visual regression testing.

**Additional tools:**
- `linkchecker` - External link validation
- `htmltest` - HTML validation
- Percy/Chromatic - Visual regression

**New test job:**
```yaml
  test-docs:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Install uv
        uses: astral-sh/setup-uv@v4

      - name: Set up Python
        run: uv python install 3.12

      - name: Install dependencies
        run: uv sync --extra docs

      - name: Build in strict mode
        run: uv run mkdocs build --strict

      - name: Validate HTML
        run: |
          # Install htmltest
          wget -qO- https://github.com/wjdp/htmltest/releases/download/v0.17.0/htmltest_0.17.0_linux_amd64.tar.gz | tar xz
          ./htmltest site/

      - name: Check internal links
        run: |
          pip install linkchecker
          linkchecker --check-extern site/

      - name: Verify navigation completeness
        run: |
          # Custom script to ensure all docs are in nav
          python scripts/check_nav_completeness.py
```

---

## Quick Wins (Immediate Actions)

### 1. Add strict mode (5 min)
```bash
# Edit .github/workflows/docs.yml
# Change: uv run mkdocs build
# To:     uv run mkdocs build --strict
```

### 2. Fix orphaned pages (15 min)
Add to `mkdocs.yml`:
```yaml
nav:
  - Development:
      - Specs:
          - StatusLine Config UX: specs/SPEC-statusline-config-ux-2025-12-31.md
          - StatusLine Integration: specs/SPEC-statusline-integration-2025-12-31.md
      - Demos: demos/README.md
      - Tutorials Dev: demos/tutorials/README.md
      - Testing Checklist: tutorials/USER-TESTING-CHECKLIST.md
```

Or add to `exclude_docs` if intentionally unlisted:
```yaml
exclude_docs: |
  _archive/
  specs/SPEC-statusline-*.md
  demos/README.md
  tutorials/USER-TESTING-CHECKLIST.md
```

### 3. Local testing alias (2 min)
Add to project README:
```bash
# Test docs locally
uv run mkdocs build --strict  # Validate
uv run mkdocs serve           # Preview at http://127.0.0.1:8000
```

---

## Recommended Path

**Start with Option A** (strict mode) - It's a 2-line change that catches most issues.

**Progression:**
1. ⚡ Add `--strict` flag (today)
2. ⚡ Fix orphaned pages (today)
3. 🔧 Add basic validation script (next session)
4. 🏗️ Consider link checker if external links become an issue (future)

---

## Implementation

### Step 1: Update workflow
```bash
# Edit .github/workflows/docs.yml
sed -i '' 's/mkdocs build/mkdocs build --strict/' .github/workflows/docs.yml

git add .github/workflows/docs.yml
git commit -m "ci(docs): enable strict mode for documentation builds"
```

### Step 2: Fix orphaned pages
Choose either:
- **A)** Add them to `mkdocs.yml` nav
- **B)** Add to `exclude_docs` if intentional

### Step 3: Test locally
```bash
uv run mkdocs build --strict
# Should pass with no warnings
```

### Step 4: Push and verify
```bash
git push
gh run watch  # Watch workflow run
```

---

## Testing Checklist

Before merging docs changes, verify:
- [ ] `mkdocs build --strict` passes locally
- [ ] All images referenced exist
- [ ] Internal links work
- [ ] Navigation structure makes sense
- [ ] Mobile view looks good (Material theme responsive)
- [ ] Search works (try a few queries)

---

## Next Steps

**Immediate (Today):**
1. [ ] Add `--strict` to workflow
2. [ ] Decide on orphaned pages (nav or exclude)
3. [ ] Test build locally
4. [ ] Push and verify CI

**Short-term (Next Week):**
- [ ] Create `scripts/check_nav_completeness.py`
- [ ] Add image validation
- [ ] Document testing process

**Long-term (Future):**
- [ ] External link validation (if needed)
- [ ] Visual regression testing (if design changes frequently)
- [ ] Automated screenshot updates
