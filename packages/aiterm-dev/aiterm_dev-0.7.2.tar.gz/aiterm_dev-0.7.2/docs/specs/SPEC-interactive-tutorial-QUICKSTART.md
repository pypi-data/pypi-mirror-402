# Interactive Tutorial System - Quick Start Implementation Guide

**For**: Implementing the tutorial system after spec approval  
**Reference**: See `SPEC-interactive-tutorial-system.md` for full details  
**Target Branch**: `dev`  

---

## Pre-Implementation Checklist

Before starting, ensure:

- [ ] Specification reviewed and approved
- [ ] On `dev` branch and up to date with remote
- [ ] All existing tests passing (`pytest`)
- [ ] Current version is v0.5.0 (check `pyproject.toml`)
- [ ] No uncommitted changes that could conflict

---

## Phase 1: Core Engine (Day 1-2, 10-12 hours)

### Step 1.1: Create Tutorial Module

```bash
# Create the tutorial module
touch src/aiterm/utils/tutorial.py
```

**File**: `src/aiterm/utils/tutorial.py`

**Content Structure** (600-700 lines):
```python
"""Interactive tutorial system for aiterm."""

import time
from dataclasses import dataclass
from enum import Enum
from typing import Callable

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.table import Table

# 1. Enum and Dataclass Definitions (30 lines)
class TutorialLevel(str, Enum): ...
@dataclass
class TutorialStep: ...

# 2. Tutorial Base Class (150 lines)
class Tutorial:
    def __init__(self, name, level, description): ...
    def add_step(self, step): ...
    def show_intro(self): ...
    def show_step(self, step_num): ...
    def run(self): ...
    def show_completion(self): ...

# 3. Getting Started Tutorial (120 lines)
def create_getting_started_tutorial() -> Tutorial: ...

# 4. Intermediate Tutorial (180 lines)
def create_intermediate_tutorial() -> Tutorial: ...

# 5. Advanced Tutorial (200 lines)
def create_advanced_tutorial() -> Tutorial: ...

# 6. Helper Functions (40 lines)
def get_tutorial(level: TutorialLevel) -> Tutorial: ...
def list_tutorials() -> None: ...
```

**Key Implementation Notes**:
- Copy structure from Nexus: `/Users/dt/projects/dev-tools/nexus-cli/nexus/utils/tutorial.py`
- Use Rich Panel for intro (with level-specific colors: green/yellow/red)
- Use Rich Panel for steps (blue border)
- Use questionary Confirm for interactive prompts
- Implement pause/resume logic (save current_step)

### Step 1.2: Create Initial Tests

```bash
# Create test file
touch tests/test_tutorial.py
```

**File**: `tests/test_tutorial.py`

**Initial Tests** (15 tests):
```python
"""Tests for tutorial system."""

import pytest
from aiterm.utils.tutorial import (
    Tutorial,
    TutorialLevel,
    TutorialStep,
    create_getting_started_tutorial,
    get_tutorial,
)

# Structure tests (5 tests)
def test_tutorial_instantiation(): ...
def test_add_step(): ...
def test_step_count(): ...
def test_tutorial_levels(): ...
def test_tutorial_step_dataclass(): ...

# Navigation tests (5 tests)
def test_show_intro(): ...
def test_show_step(): ...
def test_show_completion(): ...
def test_current_step_tracking(): ...
def test_step_out_of_range(): ...

# Content tests (5 tests)
def test_getting_started_has_7_steps(): ...
def test_intermediate_has_11_steps(): ...
def test_advanced_has_12_steps(): ...
def test_all_steps_have_titles(): ...
def test_interactive_steps_have_commands(): ...
```

### Step 1.3: Validation

```bash
# Run tests
pytest tests/test_tutorial.py -v

# Check coverage
pytest tests/test_tutorial.py --cov=src/aiterm/utils/tutorial --cov-report=term

# Target: 80%+ coverage at this stage
```

---

## Phase 2: Tutorial Content (Day 3-4, 8-10 hours)

### Step 2.1: Implement Getting Started Tutorial

**Content** (7 steps):

1. Welcome → No command
2. Check Installation → `ait doctor` (interactive)
3. View Configuration → `ait config show` (interactive)
4. Detect Context → `ait detect` (interactive)
5. Apply Context → `ait switch` (interactive)
6. Explore Commands → `ait --help` (non-interactive)
7. Next Steps → No command, summary

**Implementation**:
```python
def create_getting_started_tutorial() -> Tutorial:
    tutorial = Tutorial(
        name="Getting Started with aiterm",
        level=TutorialLevel.GETTING_STARTED,
        description="Learn terminal optimization basics for AI development",
    )
    
    # Step 1: Welcome
    tutorial.add_step(TutorialStep(
        title="Welcome to aiterm!",
        description=(
            "aiterm optimizes your terminal for AI-assisted development.\n"
            "It manages:\n"
            "• 🖥️ Terminal profiles and themes (6 terminals supported)\n"
            "• 🤖 Claude Code integration and auto-approvals\n"
            "• 📊 Workflows and automation\n"
            "• 🚀 Release automation (PyPI, Homebrew)\n\n"
            "Let's learn the essentials in 7 quick steps!"
        ),
    ))
    
    # Step 2: doctor check
    tutorial.add_step(TutorialStep(
        title="Check Your Installation",
        description=(
            "The 'doctor' command verifies aiterm can access your terminal,\n"
            "shell, and optional integrations."
        ),
        command="ait doctor",
        interactive=True,
        hint="Green checkmarks = working. Red X's = optional features.",
    ))
    
    # ... add steps 3-7 ...
    
    return tutorial
```

### Step 2.2: Implement Intermediate Tutorial

**Content** (11 steps): See spec for full breakdown
- Claude Code integration (4 steps) - **primary focus**
- Workflows & sessions (3 steps)
- Terminal management (4 steps)

### Step 2.3: Implement Advanced Tutorial

**Content** (12 steps): See spec for full breakdown
- Release automation (4 steps) - v0.5.0 features
- Custom workflows (2 steps)
- Integrations: Craft, MCP, IDE (3 steps)
- Advanced: debugging, config, resources (3 steps)

### Step 2.4: Add Content Tests

```python
# Add to tests/test_tutorial.py

def test_getting_started_content():
    tutorial = create_getting_started_tutorial()
    assert len(tutorial.steps) == 7
    assert tutorial.steps[1].command == "ait doctor"
    assert tutorial.steps[1].interactive is True

def test_intermediate_content():
    tutorial = create_intermediate_tutorial()
    assert len(tutorial.steps) == 11
    # Check key commands present

def test_advanced_content():
    tutorial = create_advanced_tutorial()
    assert len(tutorial.steps) == 12
    # Verify release commands featured
```

### Step 2.5: Validation

```bash
# Test all tutorials can be created
pytest tests/test_tutorial.py::test_getting_started_content -v
pytest tests/test_tutorial.py::test_intermediate_content -v
pytest tests/test_tutorial.py::test_advanced_content -v

# Manual validation: Run each tutorial
python -c "from aiterm.utils.tutorial import create_getting_started_tutorial; t = create_getting_started_tutorial(); t.show_intro()"
```

---

## Phase 3: CLI Integration (Day 5, 4-6 hours)

### Step 3.1: Add learn Command

**File**: `src/aiterm/cli/main.py`

**Add after other commands** (~line 150):

```python
@app.command(
    epilog="""
[bold]Examples:[/]
  ait learn                         # List all tutorials
  ait learn getting-started         # Start beginner tutorial
  ait learn intermediate            # Domain workflows
  ait learn advanced                # Power user techniques
  ait learn intermediate --step 5   # Resume from step 5
"""
)
def learn(
    level: Annotated[
        str | None,
        typer.Argument(help="Tutorial level: getting-started, intermediate, advanced, or 'list'"),
    ] = None,
    step: Annotated[
        int | None,
        typer.Option("--step", "-s", help="Start at specific step number"),
    ] = None,
) -> None:
    """Interactive tutorials for learning aiterm.
    
    Learn aiterm through hands-on tutorials at different skill levels.
    Each tutorial includes real commands, hints, and interactive practice.
    """
    from aiterm.utils.tutorial import TutorialLevel, get_tutorial, list_tutorials

    # No argument or "list" shows all tutorials
    if level is None or level == "list":
        list_tutorials()
        return

    # Normalize level name
    level_normalized = level.lower().replace("_", "-")

    # Validate level
    try:
        tutorial_level = TutorialLevel(level_normalized)
    except ValueError:
        console.print(f"[red]Error:[/] Unknown tutorial level: {level}")
        console.print("\n[dim]Available levels:[/]")
        console.print("  • getting-started")
        console.print("  • intermediate")
        console.print("  • advanced")
        console.print("\n[dim]Example:[/] ait learn getting-started")
        raise typer.Exit(1)

    # Get and run tutorial
    tutorial_obj = get_tutorial(tutorial_level)

    # Resume from specific step if requested
    if step is not None:
        if step < 1 or step > len(tutorial_obj.steps):
            console.print(f"[red]Error:[/] Step {step} is out of range")
            console.print(f"This tutorial has {len(tutorial_obj.steps)} steps")
            console.print(f"\n[dim]Try:[/] ait learn {level} --step 1")
            raise typer.Exit(1)
        tutorial_obj.current_step = step - 1

    # Run the tutorial
    tutorial_obj.run()
```

### Step 3.2: Add CLI Tests

**File**: `tests/cli/test_learn.py` (new file)

```python
"""Tests for learn command."""

import pytest
from typer.testing import CliRunner
from aiterm.cli.main import app

runner = CliRunner()

def test_learn_list():
    result = runner.invoke(app, ["learn"])
    assert result.exit_code == 0
    assert "getting-started" in result.output

def test_learn_getting_started():
    result = runner.invoke(app, ["learn", "getting-started"], input="n\n")
    assert result.exit_code == 0
    assert "Getting Started" in result.output

def test_learn_invalid_level():
    result = runner.invoke(app, ["learn", "invalid"])
    assert result.exit_code == 1
    assert "Unknown tutorial level" in result.output

def test_learn_with_step():
    result = runner.invoke(app, ["learn", "getting-started", "--step", "3"], input="n\n")
    assert result.exit_code == 0

def test_learn_invalid_step():
    result = runner.invoke(app, ["learn", "getting-started", "--step", "99"])
    assert result.exit_code == 1
    assert "out of range" in result.output
```

### Step 3.3: Validation

```bash
# Test CLI integration
pytest tests/cli/test_learn.py -v

# Manual testing
ait learn
ait learn getting-started
ait learn --help
```

---

## Phase 4: Documentation (Day 6-7, 6-8 hours)

### Step 4.1: Create MkDocs Page

**File**: `docs/tutorials/interactive-learning.md`

```markdown
# Interactive Learning System

Learn aiterm through hands-on, interactive tutorials at your own pace.

## Quick Start

\`\`\`bash
# List all tutorials
ait learn

# Start with basics (7 steps, ~10 min)
ait learn getting-started

# Learn workflows (11 steps, ~20 min)
ait learn intermediate

# Master advanced features (12 steps, ~30 min)
ait learn advanced
\`\`\`

## Tutorial Levels

### Getting Started (7 steps)
[Content from spec...]

### Intermediate (11 steps)
[Content from spec...]

### Advanced (12 steps)
[Content from spec...]

## Interactive Features
[Pause/resume, hints, etc.]

## FAQ
[Common questions...]
```

### Step 4.2: Create Standalone Guide

**File**: `TUTORIAL_GUIDE.md` (project root)

```markdown
# aiterm Interactive Tutorial System

Complete guide to learning aiterm through interactive tutorials.

## Overview
[High-level intro...]

## Tutorial Levels
[Detailed breakdown of each level...]

## Tips and Tricks
[Best practices...]

## Troubleshooting
[Common issues...]
```

### Step 4.3: Update Existing Docs

**Files to Update**:

1. `README.md` - Add tutorial section:
```markdown
## 🎓 Learn Interactively

**New to aiterm?** Start with our interactive tutorials:

\`\`\`bash
ait learn getting-started  # 10 minutes to productivity
\`\`\`

See [TUTORIAL_GUIDE.md](TUTORIAL_GUIDE.md) for complete guide.
```

2. `docs/REFCARD.md` - Add commands:
```markdown
INTERACTIVE LEARNING
────────────────────
ait learn                   List all tutorials
ait learn getting-started   Basic tutorial (7 steps, ~10 min)
ait learn intermediate      Domain workflows (11 steps, ~20 min)
ait learn advanced          Power user (12 steps, ~30 min)
ait learn <level> --step N  Resume from step N
```

3. `mkdocs.yml` - Add to navigation:
```yaml
nav:
  - Tutorials:
      - Interactive Learning: tutorials/interactive-learning.md
      - First Steps: tutorials/first-steps.md  # existing
```

### Step 4.4: Validation

```bash
# Build docs locally
mkdocs serve

# Verify:
# - Navigation works
# - Tutorial page renders correctly
# - Links are valid
# - Code examples work
```

---

## Phase 5: Testing & Polish (Day 8-9, 4-6 hours)

### Step 5.1: Comprehensive Test Suite

**Add to** `tests/test_tutorial.py`:

```python
# Pause/Resume Tests (6 tests)
def test_pause_at_step(): ...
def test_resume_from_step(): ...
def test_resume_validates_step_number(): ...
def test_pause_shows_resume_command(): ...
def test_resume_skips_completed_steps(): ...
def test_resume_from_last_step(): ...

# Interactive Prompt Tests (8 tests)
def test_confirm_prompt_yes(): ...
def test_confirm_prompt_no(): ...
def test_ready_to_start_no_cancels(): ...
def test_continue_to_next_step_no_pauses(): ...
def test_interactive_step_confirmation(): ...
def test_non_interactive_step_skips_confirmation(): ...
def test_hint_displayed_when_present(): ...
def test_command_displayed_when_present(): ...

# Edge Case Tests (5 tests)
def test_empty_tutorial(): ...
def test_tutorial_with_no_interactive_steps(): ...
def test_tutorial_with_all_interactive_steps(): ...
def test_step_without_command(): ...
def test_step_without_hint(): ...
```

### Step 5.2: Coverage Check

```bash
# Run full test suite
pytest tests/test_tutorial.py -v

# Check coverage (target: 90%+)
pytest tests/test_tutorial.py --cov=src/aiterm/utils/tutorial --cov-report=html

# Open coverage report
open htmlcov/index.html
```

### Step 5.3: Manual Testing Checklist

```bash
# Test each tutorial completely
ait learn getting-started      # Complete all 7 steps
ait learn intermediate         # Complete all 11 steps
ait learn advanced             # Complete all 12 steps

# Test pause/resume
ait learn getting-started      # Pause at step 3
ait learn getting-started --step 4  # Resume

# Test error handling
ait learn invalid              # Should show error
ait learn getting-started --step 99  # Should show error

# Test on different terminals
# iTerm2, Ghostty, Terminal.app, etc.
```

### Step 5.4: Performance Check

```bash
# Measure startup time (should be <100ms)
time ait learn

# Measure tutorial start time
time ait learn getting-started <<< "n"
```

---

## Phase 6: Final Steps (Day 10, 2-3 hours)

### Step 6.1: Update CHANGELOG

**File**: `CHANGELOG.md`

```markdown
## [0.6.0] - YYYY-MM-DD

### Added
- **Interactive Tutorial System** (`ait learn`) (#XX)
  - 3 progressive tutorials (Getting Started, Intermediate, Advanced)
  - 30 total hands-on steps
  - Pause/resume capability
  - Reduces new user onboarding from 2 hours to 30 minutes
  - See TUTORIAL_GUIDE.md for complete guide
```

### Step 6.2: Run Full Test Suite

```bash
# All tests
pytest -v

# With coverage
pytest --cov=src/aiterm --cov-report=term --cov-report=html

# Check coverage didn't decrease
# Target: Maintain 85%+ overall
```

### Step 6.3: Final Validation

```bash
# Lint
ruff check src/aiterm/utils/tutorial.py

# Format
ruff format src/aiterm/utils/tutorial.py

# Type check (if mypy configured)
mypy src/aiterm/utils/tutorial.py

# Build docs
mkdocs build

# All checks should pass
```

---

## Checklist Summary

Before committing to dev branch:

- [ ] `src/aiterm/utils/tutorial.py` created (600-700 lines)
- [ ] `src/aiterm/cli/main.py` updated with learn command
- [ ] `tests/test_tutorial.py` created (40+ tests, 90%+ coverage)
- [ ] `tests/cli/test_learn.py` created (5+ tests)
- [ ] `docs/tutorials/interactive-learning.md` created
- [ ] `TUTORIAL_GUIDE.md` created
- [ ] `README.md` updated with tutorial section
- [ ] `docs/REFCARD.md` updated with learn commands
- [ ] `mkdocs.yml` updated with tutorial navigation
- [ ] `CHANGELOG.md` updated for v0.6.0
- [ ] All tests passing (`pytest -v`)
- [ ] Coverage maintained at 85%+ overall
- [ ] Tutorial coverage 90%+ 
- [ ] Docs build successfully (`mkdocs build`)
- [ ] Manual testing complete (all 3 tutorials)
- [ ] Performance acceptable (<100ms start time)

---

## Git Workflow

```bash
# Ensure on dev branch
git checkout dev
git pull origin dev

# Create feature branch (optional)
git checkout -b feature/tutorial-system

# After each phase, commit
git add src/aiterm/utils/tutorial.py tests/test_tutorial.py
git commit -m "feat: add tutorial engine core (Phase 1)"

git add docs/tutorials/interactive-learning.md TUTORIAL_GUIDE.md
git commit -m "docs: add tutorial documentation (Phase 4)"

# Final commit with everything
git add .
git commit -m "feat: complete interactive tutorial system for v0.6.0

- Add 'ait learn' command with 3 progressive tutorials
- 30 total steps (7 getting-started, 11 intermediate, 12 advanced)
- Comprehensive docs and 40+ tests (90%+ coverage)
- Reduces new user onboarding from 2 hours to 30 minutes

Closes #XX"

# Push to dev
git push origin dev
# or
git push origin feature/tutorial-system
```

---

## Ready to Implement?

1. **Review** the full spec: `SPEC-interactive-tutorial-system.md`
2. **Follow** this quickstart phase by phase
3. **Reference** Nexus implementation: `~/projects/dev-tools/nexus-cli/nexus/utils/tutorial.py`
4. **Test** thoroughly after each phase
5. **Ask** for clarification if anything is unclear

**Estimated Total Time**: 36-48 hours over 10 days

**Questions?** See spec or ask before starting!
