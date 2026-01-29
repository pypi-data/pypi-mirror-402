# Testing Guide - aiterm

Quick reference for running all test suites.

## Quick Start

```bash
# Run everything (2-3 minutes)
pytest tests/ && bash tests/cli/automated-tests.sh && bash tests/cli/e2e-workflows.sh

# Just unit tests (1 minute)
pytest tests/

# Just CLI tests (20 seconds)
bash tests/cli/automated-tests.sh

# Just E2E workflows (1 minute)
bash tests/cli/e2e-workflows.sh
```

---

## Python Unit Tests (982 tests)

### All Tests
```bash
pytest tests/
```

### StatusLine Phase 1 Only
```bash
pytest tests/test_statusline_*.py
```

### With Coverage
```bash
pytest --cov=src/aiterm --cov-report=html tests/
open htmlcov/index.html
```

### Specific Test
```bash
pytest tests/test_statusline_hooks.py::TestHookInstallation::test_install_creates_hook_file -v
```

### Options
```bash
pytest tests/ -v              # Verbose
pytest tests/ -x              # Stop on first failure
pytest tests/ -k statusline   # Run tests matching pattern
pytest tests/ --lf            # Last failed
```

---

## CLI Automated Tests (54 tests)

### All CLI Tests
```bash
bash tests/cli/automated-tests.sh
```

### Specific Category
```bash
bash tests/cli/automated-tests.sh statusline    # StatusLine only
bash tests/cli/automated-tests.sh core          # Core commands
bash tests/cli/automated-tests.sh feature       # Feature branch
bash tests/cli/automated-tests.sh release       # Release automation
bash tests/cli/automated-tests.sh claude        # Claude Code
bash tests/cli/automated-tests.sh terminal      # Terminal support
bash tests/cli/automated-tests.sh help          # Help accessibility
bash tests/cli/automated-tests.sh errors        # Error handling
bash tests/cli/automated-tests.sh learn         # Learn/tutorials
```

### Verbose Output
```bash
VERBOSE=1 bash tests/cli/automated-tests.sh
```

### Logs
```bash
cat tests/cli/logs/automated-*.log
```

---

## E2E Workflow Tests (6 workflows)

### All Workflows
```bash
bash tests/cli/e2e-workflows.sh
```

### Specific Workflow
```bash
bash tests/cli/e2e-workflows.sh statusline   # StatusLine customization
bash tests/cli/e2e-workflows.sh feature      # Feature development
bash tests/cli/e2e-workflows.sh release      # Release preparation
bash tests/cli/e2e-workflows.sh claude       # Claude Code integration
bash tests/cli/e2e-workflows.sh terminal     # Terminal switching
bash tests/cli/e2e-workflows.sh full         # Full integration
```

### Logs
```bash
cat tests/cli/logs/e2e-*.log
```

---

## Interactive Tests

For human-guided testing:

```bash
bash tests/cli/interactive-tests.sh
```

Controls:
- **y** - Pass the test
- **n** - Fail the test
- **q** - Quit

---

## Running Before Commit

```bash
#!/bin/bash
# Pre-commit test suite

echo "Running pre-commit tests..."

# Quick checks (30 seconds)
bash tests/cli/automated-tests.sh || exit 1

# Run pytest on changed files (faster)
pytest tests/test_cli.py -q || exit 1

echo "✅ All pre-commit tests passed"
```

---

## CI/CD Integration

### GitHub Actions

```yaml
- name: Run Tests
  run: |
    pip install -e ".[dev]"
    pytest tests/ -q
    bash tests/cli/automated-tests.sh
```

### Pre-commit Hook

Create `.git/hooks/pre-commit`:

```bash
#!/bin/bash
bash tests/cli/automated-tests.sh || exit 1
```

Make executable:
```bash
chmod +x .git/hooks/pre-commit
```

---

## Coverage Reports

### Generate Coverage
```bash
pytest --cov=src/aiterm --cov-report=html tests/
open htmlcov/index.html
```

### Check Coverage
```bash
pytest --cov=src/aiterm --cov-report=term tests/
```

---

## Test Organization

### By Component
```bash
# StatusLine tests
pytest tests/test_statusline_*.py

# Feature workflow tests
pytest tests/test_feature.py

# Release tests
pytest tests/test_release.py

# Terminal tests
pytest tests/test_iterm2.py tests/test_ghostty.py
```

### By Feature
```bash
# Phase 1 tests only
pytest tests/test_statusline_hooks.py
pytest tests/test_statusline_cli_gateway.py
```

---

## Common Tasks

### Run specific test file
```bash
pytest tests/test_cli.py
```

### Run test with output
```bash
pytest tests/test_cli.py -s
```

### List all tests
```bash
pytest tests/ --collect-only
```

### Run only failing tests
```bash
pytest tests/ --lf
```

### Run with markers
```bash
pytest tests/ -m integration
```

### Set timeout
```bash
pytest tests/ --timeout=10
```

---

## Troubleshooting

### Install dependencies
```bash
pip install -e ".[dev]"
```

### Clear pytest cache
```bash
pytest --cache-clear
```

### Verify CLI is installed
```bash
ait --version
```

### Check PATH
```bash
which ait
```

### Reinstall package
```bash
pip install -e .
```

---

## Test Files

| File | Tests | Focus |
|------|-------|-------|
| `test_cli.py` | 25 | Basic CLI commands |
| `test_cli_integration.py` | 30 | CLI integration |
| `test_statusline_hooks.py` | 31 | Hook templates |
| `test_statusline_cli_gateway.py` | 20+ | Gateway commands |
| `test_feature.py` | 25 | Feature workflows |
| `test_release.py` | 55 | Release automation |
| Other | 700+ | Various modules |

---

## Documentation

- **Test Summary:** `tests/cli/TEST_SUITE_SUMMARY.md`
- **Test Report:** `TEST_GENERATION_REPORT.md`
- **CLI Guide:** `tests/cli/README.md`
- **This Guide:** `TESTING.md`

---

## Performance

| Test Type | Count | Duration |
|-----------|-------|----------|
| Python Unit | 982 | 60-90s |
| CLI Automated | 54 | 15-20s |
| E2E Workflows | 6 | 30-45s |
| **Total** | **1,000+** | **2-3 min** |

---

**Last Updated:** 2026-01-17
