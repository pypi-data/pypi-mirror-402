# Interactive Tutorial System - Executive Summary

**Full Spec**: `SPEC-interactive-tutorial-system.md`  
**Status**: Draft for Review  
**Target**: v0.6.0  
**Effort**: 36-48 hours over 3-4 weeks  

---

## The One-Liner

Add `ait learn` command with 3 progressive tutorials (30 total steps) following the proven Nexus CLI pattern - reducing new user time-to-productivity from 2 hours to 30 minutes.

---

## What We're Building

### Command Interface

```bash
ait learn                        # List all tutorials
ait learn getting-started        # 7 steps, ~10 min
ait learn intermediate           # 11 steps, ~20 min  
ait learn advanced               # 12 steps, ~30 min
ait learn <level> --step N       # Resume from step N
```

### Tutorial Content

**Level 1: Getting Started** (7 steps)
- What is aiterm? → doctor → config → detect → switch → help → next steps

**Level 2: Intermediate** (11 steps)
- Claude Code (primary) → workflows → sessions → terminals

**Level 3: Advanced** (12 steps)
- Release (v0.5.0) → workflows → integrations (Craft/MCP/IDE) → debugging

---

## Why This Matters

**Current State**: 
- New users must read docs passively
- No guided onboarding
- 2+ hours to productivity
- High support burden

**With Tutorials**:
- Hands-on interactive learning
- Progressive skill building
- 30 minutes to productivity
- 40% reduction in support questions

---

## Implementation Overview

### Core Files

```
src/aiterm/utils/tutorial.py      # NEW: 600-700 lines (tutorial engine)
src/aiterm/cli/main.py            # MODIFIED: +50 lines (learn command)
tests/test_tutorial.py            # NEW: 40+ tests
docs/tutorials/interactive-learning.md  # NEW: MkDocs page
TUTORIAL_GUIDE.md                 # NEW: Standalone reference
```

### Dependencies

**None!** Uses existing:
- `typer` - CLI framework
- `rich` - Terminal formatting  
- `questionary` - Interactive prompts

### Architecture

Following **exact Nexus CLI pattern**:
- `TutorialLevel` enum (getting-started, intermediate, advanced)
- `TutorialStep` dataclass (title, description, command, hint)
- `Tutorial` base class (show_intro, show_step, run, completion)
- Helper functions (create_*_tutorial, get_tutorial, list_tutorials)

---

## Timeline & Effort

| Phase | Duration | Effort |
|-------|----------|--------|
| 1. Core Engine | Week 1 | 10-12h |
| 2. Tutorial Content | Week 1-2 | 8-10h |
| 3. CLI Integration | Week 2 | 4-6h |
| 4. Documentation | Week 2-3 | 6-8h |
| 5. Testing & Polish | Week 3 | 4-6h |
| 6. User Testing | Week 3-4 | 4-6h |
| **TOTAL** | **3-4 weeks** | **36-48h** |

---

## Success Metrics

**Quantitative**:
- 60%+ tutorial completion rate
- <30 min time to productivity (vs. 2 hours)
- 90%+ test coverage
- 40% reduction in support questions

**Qualitative**:
- "Tutorials are clear and helpful"
- "I learned features I didn't know existed"
- "Faster onboarding than reading docs"

---

## Key Decisions

### ✅ Decisions Made (Based on Nexus Success)

1. **Command Name**: `ait learn` (simpler than `ait tutorial`)
2. **Levels**: 3 progressive levels (getting-started → intermediate → advanced)
3. **Pattern**: Follow Nexus implementation exactly (proven success)
4. **Location**: `src/aiterm/utils/tutorial.py` (matches Nexus structure)
5. **Testing**: 40+ tests for 90%+ coverage
6. **Dependencies**: None - use existing Rich, Typer, Questionary

### ❓ Decisions for Review

1. **Tutorial Content Balance**:
   - Getting Started: 7 steps good, or too long?
   - Advanced: Now balanced across release, workflows, integrations, debugging

2. **Intermediate Tutorial**:
   - Reordered: Claude Code first (primary use case), terminals last
   - Ghostty section conditional (skipped if not using Ghostty)

3. **Future Scope**:
   - Implement completion tracking in v0.6.0 or defer to v0.7.0?
   - Video companions priority?

---

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Content becomes outdated | High | Automated command tests |
| Tutorial too long | Medium | Pause/resume, 7-step Getting Started |
| Commands fail for users | High | Pre-flight checks, clear errors |
| Terminal compatibility | Medium | Test on all 6 terminals |

---

## Next Steps (After Approval)

### Week 1
1. Create `src/aiterm/utils/tutorial.py` with core engine
2. Implement all 3 tutorials (30 steps total)
3. Add basic unit tests

### Week 2  
1. Integrate `ait learn` command into CLI
2. Write documentation (MkDocs + standalone guide)
3. Comprehensive testing

### Week 3
1. User testing with 3-5 new users
2. Iterate based on feedback
3. Final polish

### Week 4
1. Merge to dev branch
2. Update CHANGELOG.md
3. Release as part of v0.6.0

---

## Questions for Review

1. **Is the tutorial content appropriate?** 
   - Right mix of basic/intermediate/advanced?
   - Missing any critical workflows?

2. **Is the timeline realistic?**
   - 3-4 weeks acceptable?
   - Should we prioritize for faster delivery?

3. **Should we add any v0.6.0-specific features?**
   - Completion tracking?
   - Quiz mode?
   - Or keep scope tight for first iteration?

4. **Documentation structure good?**
   - MkDocs integration + standalone guide
   - Need additional formats?

5. **Testing strategy sufficient?**
   - 40+ tests with 90%+ coverage
   - Manual testing on all terminals
   - User testing with 3-5 people

---

## Recommendation

**Proceed with implementation as specified** because:

1. ✅ **Proven Pattern**: Nexus tutorial system is successful - replicate it
2. ✅ **Clear Value**: Dramatically reduces onboarding time
3. ✅ **Low Risk**: No new dependencies, well-defined scope
4. ✅ **Timely**: Complements v0.5.0 release automation features
5. ✅ **Scalable**: Foundation for future enhancements (quizzes, videos, etc.)

**Target**: Merge to `dev` branch by mid-January 2026, release in v0.6.0

---

**Full specification**: See `SPEC-interactive-tutorial-system.md` for complete details (architecture, content, testing, etc.)
