# Release Automation Guide

Complete guide to aiterm's release automation system.

## Overview

aiterm has **two ways** to publish releases:

| Method | Type | PyPI | Homebrew | Recommended |
|--------|------|------|----------|-------------|
| **GitHub Actions** | Automatic | ✅ Trusted Publisher | ✅ Auto-merge | ✅ **YES** |
| **CLI Commands** | Manual | ⚠️ Local credentials | ⚠️ Manual PR | Testing only |

**Bottom line:** Use `gh release create` for production releases. It's more secure, fully automated, and requires zero manual steps.

---

## The Two Automation Paths

### Path 1: GitHub Actions (Recommended) 🎯

```bash
# 1. Update version
# Edit pyproject.toml, bump version to 0.6.3

# 2. Update changelog
# Edit CHANGELOG.md, add v0.6.3 entry

# 3. Commit and push
git add pyproject.toml CHANGELOG.md
git commit -m "chore: bump version to 0.6.3"
git push

# 4. Create GitHub release
gh release create v0.6.3 \
  --title "v0.6.3 - StatusLine System" \
  --notes-file <(sed -n '/## \[0.6.3\]/,/## \[0.6.0\]/p' CHANGELOG.md)

# 5. ✅ DONE! Everything happens automatically:
#    ✓ PyPI publish (30 seconds)
#    ✓ Homebrew formula update (2 minutes)
#    ✓ Documentation deploy (1 minute)
```

**What happens automatically:**

```
gh release create v0.6.3
  │
  ├─> Triggers: .github/workflows/pypi-release.yml
  │     ├─ Checkout code
  │     ├─ Install uv
  │     ├─ Build package (uv build)
  │     └─ Publish to PyPI (trusted publisher)
  │        ✅ No tokens needed!
  │        ✅ OIDC authentication
  │        ✅ Secure & automatic
  │
  ├─> Triggers: .github/workflows/homebrew-release.yml
  │     ├─ Download release tarball
  │     ├─ Calculate SHA256
  │     ├─ Clone Data-Wise/homebrew-tap
  │     ├─ Update Formula/aiterm.rb
  │     ├─ Create PR
  │     └─ Auto-merge PR
  │        ✅ Formula updated automatically!
  │
  └─> Triggers: .github/workflows/docs.yml
        ├─ Build docs (mkdocs build --strict)
        └─ Deploy to GitHub Pages
           ✅ https://data-wise.github.io/aiterm/
```

---

### Path 2: CLI Commands (Manual Control)

```bash
# Full manual workflow
ait release full 0.6.3

# What it does:
#   1. check      - Validate readiness
#   2. tag        - Create git tag
#   3. push       - Push tag to GitHub
#   4. pypi       - Publish to PyPI (LOCAL)
#   5. homebrew   - Update formula (CREATES PR, NO AUTO-MERGE)
```

**Problems with this approach:**

1. **PyPI:** Uses local credentials (twine/uv)
   - Requires PyPI API token in environment
   - Less secure than trusted publishing
   - Token can expire

2. **Homebrew:** Only creates PR, doesn't merge
   - You must manually merge the PR
   - Extra step, easy to forget

3. **No parallel execution**
   - Steps run sequentially
   - Slower than GitHub Actions

4. **Local dependencies**
   - Requires `uv`, `twine` installed
   - Requires `gh` CLI for Homebrew update
   - Requires clean git state

---

## Why GitHub Actions is Better

### 🔐 Security: Trusted Publishing

**GitHub Actions:**
```yaml
# No tokens needed!
environment: pypi
permissions:
  id-token: write  # OIDC authentication
```

- Uses PyPI Trusted Publishers
- OIDC authentication (OpenID Connect)
- No API tokens to leak or expire
- Configured once at: https://pypi.org/manage/account/publishing/

**CLI Commands:**
```bash
# Requires environment variables
export TWINE_USERNAME=__token__
export TWINE_PASSWORD=pypi-xxx...  # Can leak!
```

### ⚡ Speed: Parallel Execution

**GitHub Actions:**
- PyPI and Homebrew workflows run **in parallel**
- Total time: ~2 minutes (longest workflow)

**CLI Commands:**
- Steps run **sequentially**
- Total time: ~5 minutes (sum of all steps)

### 🎯 Reliability: Automatic Everything

**GitHub Actions:**
| Step | Status |
|------|--------|
| PyPI publish | ✅ Automatic |
| Homebrew PR | ✅ Automatic |
| Homebrew merge | ✅ **Automatic** |
| Docs deploy | ✅ Automatic |

**CLI Commands:**
| Step | Status |
|------|--------|
| PyPI publish | ⚠️ Manual (local) |
| Homebrew PR | ⚠️ Manual (creates PR) |
| Homebrew merge | ❌ **Manual** (you merge) |
| Docs deploy | ❌ Not triggered |

---

## When to Use Each Method

### Use GitHub Actions (`gh release create`) for:

✅ **Production releases** - Always
✅ **Security** - Trusted publishing, no tokens
✅ **Automation** - Zero manual steps
✅ **Team workflows** - Anyone can release
✅ **CI/CD integration** - Hooks into existing workflows

### Use CLI Commands (`ait release *`) for:

⚠️ **Testing** - Before creating actual release
⚠️ **Dry runs** - Preview what would happen
⚠️ **Debugging** - When automation fails
⚠️ **Local development** - Quick PyPI publish for testing
⚠️ **Partial updates** - Only PyPI or only Homebrew

---

## Complete Workflow Examples

### Production Release (Recommended)

```bash
# 1. Prepare release
vim pyproject.toml  # Bump version to 0.6.3
vim CHANGELOG.md    # Add v0.6.3 entry

# 2. Commit
git add pyproject.toml CHANGELOG.md
git commit -m "chore: bump version to 0.6.3"
git push

# 3. Create release (triggers everything)
gh release create v0.6.3 \
  --title "v0.6.3 - StatusLine System & CI Improvements" \
  --notes "$(cat <<'EOF'
## Major Features
- StatusLine system (32 config options)
- Feature workflow enhancements
- CI improvements (849 tests)

See CHANGELOG.md for details.
EOF
)"

# 4. Wait ~2 minutes, verify:
#    ✓ PyPI: https://pypi.org/project/aiterm-dev/0.6.3/
#    ✓ Homebrew: brew upgrade data-wise/tap/aiterm
#    ✓ Docs: https://data-wise.github.io/aiterm/

# 5. ✅ DONE!
```

### Testing Before Release

```bash
# Check readiness
ait release check

# Preview what would happen
ait release full 0.6.3 --dry-run

# Test PyPI publish (to test instance)
ait release pypi --repository testpypi

# If everything looks good, do the real release:
gh release create v0.6.3 ...
```

### Emergency Manual Release

```bash
# If GitHub Actions are down or broken
ait release full 0.6.3

# Then manually:
# 1. Go to https://github.com/Data-Wise/homebrew-tap/pulls
# 2. Find the PR for v0.6.3
# 3. Review and merge
```

---

## Troubleshooting

### PyPI Publish Fails

**Check trusted publisher configuration:**

1. Go to https://pypi.org/manage/account/publishing/
2. Verify publisher for `aiterm-dev`:
   - Owner: `Data-Wise`
   - Repository: `aiterm`
   - Workflow: `pypi-release.yml`
   - Environment: `pypi`

**If misconfigured:** Update settings and re-run workflow:
```bash
gh run rerun <run-id> --repo Data-Wise/aiterm
```

### Homebrew PR Not Created

**Check workflow logs:**
```bash
gh run list --workflow=homebrew-release.yml --limit 5
gh run view <run-id> --log
```

**Common issues:**
- SHA256 calculation failed (tarball not available)
- Token expired (update `HOMEBREW_TAP_GITHUB_TOKEN`)
- Formula syntax error (check homebrew-tap repo)

**Manual fix:**
```bash
# Run manually
gh workflow run homebrew-release.yml -f version=0.6.3
```

### Homebrew PR Not Auto-Merged

**Check auto-merge setting:**
```yaml
# .github/workflows/homebrew-release.yml
auto_merge: true  # Should be true
```

**If disabled:** Manually merge at:
https://github.com/Data-Wise/homebrew-tap/pulls

---

## CLI Command Reference

### Individual Commands

```bash
# Validate release readiness
ait release check
  ✓ Version in pyproject.toml
  ✓ Git clean state
  ✓ All tests passing
  ✓ CHANGELOG.md updated

# Show current state
ait release status
  Current: v0.6.2
  Latest tag: v0.6.2
  Commits since: 15
  Ready: Yes

# Create git tag
ait release tag 0.6.3
  ✓ Created v0.6.3
  ✓ Pushed to origin

# Generate release notes
ait release notes
  ## Changes since v0.6.2
  - feat(statusline): add worktree display
  - ci(docs): enable strict mode
  ...

# Publish to PyPI
ait release pypi
  Building...
  ✓ Built dist/aiterm_dev-0.6.3.tar.gz
  Publishing...
  ✓ Published to PyPI

# Update Homebrew formula
ait release homebrew
  ✓ Calculated SHA256
  ✓ Created PR in homebrew-tap
  → Merge at: https://github.com/Data-Wise/homebrew-tap/pulls/42

# Full workflow
ait release full 0.6.3
  # Runs all steps above
```

### Flags

```bash
# Dry run (preview only)
ait release full 0.6.3 --dry-run

# Skip specific steps
ait release full 0.6.3 --skip-tests
ait release full 0.6.3 --skip-homebrew

# PyPI repository
ait release pypi --repository testpypi
```

---

## GitHub Actions Configuration

### PyPI Trusted Publisher Setup

**One-time setup at PyPI:**

1. Go to: https://pypi.org/manage/account/publishing/
2. Add pending publisher:
   - **PyPI Project Name:** `aiterm-dev`
   - **Owner:** `Data-Wise`
   - **Repository name:** `aiterm`
   - **Workflow name:** `pypi-release.yml`
   - **Environment name:** `pypi`

3. Verify in workflow:
```yaml
environment: pypi  # Must match!
permissions:
  id-token: write  # Required for OIDC
```

### Homebrew Token Setup

**One-time setup in GitHub:**

1. Create Personal Access Token at: https://github.com/settings/tokens
   - Name: `HOMEBREW_TAP_GITHUB_TOKEN`
   - Scopes: `repo` (full control)

2. Add to repository secrets:
   - Go to: https://github.com/Data-Wise/aiterm/settings/secrets/actions
   - New repository secret
   - Name: `HOMEBREW_TAP_GITHUB_TOKEN`
   - Value: `ghp_...` (your token)

3. Verify in workflow:
```yaml
secrets:
  tap_token: ${{ secrets.HOMEBREW_TAP_GITHUB_TOKEN }}
```

---

## Best Practices

### Version Management

**Always update these together:**
1. `pyproject.toml` - Source of truth
2. `CHANGELOG.md` - User-facing changelog
3. `docs/REFCARD.md` - Quick reference version header

**Script to check:**
```bash
# Check version consistency
grep version pyproject.toml
grep "AITERM v" docs/REFCARD.md
grep "## \[" CHANGELOG.md | head -1
```

### Release Checklist

- [ ] All tests passing (`pytest`)
- [ ] Documentation updated
- [ ] CHANGELOG.md has entry for new version
- [ ] Version bumped in `pyproject.toml`
- [ ] REFCARD.md version updated
- [ ] CLAUDE.md current version updated
- [ ] Git working directory clean
- [ ] On main branch
- [ ] Pulled latest changes

### Release Timing

**When to release:**
- ✅ Major feature complete
- ✅ Bug fix ready
- ✅ End of sprint/milestone
- ✅ Breaking changes (bump major version)

**When NOT to release:**
- ❌ Tests failing
- ❌ Incomplete features
- ❌ During active development
- ❌ Breaking changes without version bump

---

## Summary

| Aspect | GitHub Actions | CLI Commands |
|--------|---------------|--------------|
| **Security** | ✅ Trusted publishing | ⚠️ Local tokens |
| **Speed** | ✅ Parallel execution | ⚠️ Sequential |
| **Automation** | ✅ Fully automatic | ⚠️ Manual steps |
| **Reliability** | ✅ CI environment | ⚠️ Local dependencies |
| **Homebrew** | ✅ Auto-merge | ❌ Manual merge |
| **Docs** | ✅ Auto-deploy | ❌ Not triggered |
| **Use case** | **Production** | Testing/debugging |

**Recommendation:** Always use `gh release create` for production releases. Use CLI commands only for testing and debugging.

---

## Further Reading

- [PyPI Trusted Publishers](https://docs.pypi.org/trusted-publishers/)
- [GitHub Actions: Publishing](https://docs.github.com/en/actions/publishing-packages)
- [Homebrew Formula Updating](https://docs.brew.sh/How-To-Open-a-Homebrew-Pull-Request)
- [Semantic Versioning](https://semver.org/)
