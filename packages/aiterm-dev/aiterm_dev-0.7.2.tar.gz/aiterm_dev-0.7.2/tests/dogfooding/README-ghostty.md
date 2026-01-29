# Ghostty Config Dogfooding Test

Interactive containerized test for aiterm's Ghostty configuration functionality.

## Overview

This dogfooding test validates:

- ✅ Ghostty detection in container environment
- ✅ Configuration parsing and management
- ✅ New 1.2.x configuration keys (macos-titlebar-style, background-image, mouse-scroll-multiplier)
- ✅ Profile management with 1.2.x settings
- ✅ Theme application
- ✅ Config backup and restore

## Quick Start

### Using Docker Compose (Recommended)

```bash
# Build and run the test
cd tests/dogfooding
docker-compose -f docker-compose.ghostty.yml up --build

# Clean up after testing
docker-compose -f docker-compose.ghostty.yml down -v
```

### Using Docker Directly

```bash
# Build the image
docker build -f tests/dogfooding/Dockerfile.ghostty -t aiterm-ghostty-test .

# Run the test
docker run -it --rm aiterm-ghostty-test

# Run with volume mount for development
docker run -it --rm \
  -v $(pwd):/app \
  -e TERM_PROGRAM=ghostty \
  aiterm-ghostty-test
```

## Test Phases

The test runs through 6 phases:

### Phase 1: Ghostty Detection

- Verifies Ghostty terminal detection
- Shows aiterm version

### Phase 2: Configuration Management

- Parses existing Ghostty config
- Displays all 1.2.x settings

### Phase 3: New 1.2.x Configuration Keys

- Sets `macos-titlebar-style` to `tabs`
- Sets `background-image` path
- Sets `mouse-scroll-multiplier` to `2.0`
- Verifies all settings in config file

### Phase 4: Profile Management

- Creates profile with 1.2.x settings
- Lists and shows profile details
- Applies profile to restore settings

### Phase 5: Theme Management

- Lists available themes (interactive)
- Applies catppuccin-mocha theme
- Verifies theme in config

### Phase 6: Config Backup and Restore

- Creates timestamped backup
- Lists available backups

## Expected Output

```
╔════════════════════════════════════════════════════════════╗
║  aiterm Ghostty Config Dogfooding Test                    ║
║  Interactive test for Ghostty 1.2.x integration           ║
╚════════════════════════════════════════════════════════════╝

═══ Phase 1: Ghostty Detection ═══

[TEST 1] Detect Ghostty terminal
  ✓ PASS
[TEST 2] Show Ghostty version
  ✓ PASS

...

═══ Test Summary ═══

Tests Run:    15
Tests Passed: 15
Tests Failed: 0

╔════════════════════════════════════════╗
║  ALL TESTS PASSED! ✓                  ║
╚════════════════════════════════════════╝
```

## Interactive Tests

Some tests require manual verification:

- **Theme listing**: Verify themes are displayed correctly

For these tests, you'll be prompted:

```
Did this test pass? (y/n):
```

## Development

### Modifying the Test

Edit [`ghostty-config-test.sh`](ghostty-config-test.sh) to add new test cases:

```bash
run_test "Test description" \
    "ait command to run" \
    "expected pattern in output"
```

### Debugging

Run the container with a shell:

```bash
docker run -it --rm \
  -v $(pwd):/app \
  -e TERM_PROGRAM=ghostty \
  aiterm-ghostty-test \
  /bin/bash
```

Then manually run commands:

```bash
ait ghostty status
ait ghostty config
cat /root/.config/ghostty/config
```

## Files

- [`Dockerfile.ghostty`](Dockerfile.ghostty) - Container definition
- [`ghostty-config-test.sh`](ghostty-config-test.sh) - Test script
- [`docker-compose.ghostty.yml`](docker-compose.ghostty.yml) - Compose configuration

## CI Integration

To run in CI:

```yaml
- name: Run Ghostty Config Dogfooding Test
  run: |
    cd tests/dogfooding
    docker-compose -f docker-compose.ghostty.yml up --abort-on-container-exit
```

## Troubleshooting

**Issue**: Container fails to build

- **Solution**: Ensure you're in the project root when building

**Issue**: Tests fail with "command not found"

- **Solution**: Verify aiterm is installed in the container (`pip list | grep aiterm`)

**Issue**: Config file not persisting

- **Solution**: Use the docker-compose setup which includes a named volume
