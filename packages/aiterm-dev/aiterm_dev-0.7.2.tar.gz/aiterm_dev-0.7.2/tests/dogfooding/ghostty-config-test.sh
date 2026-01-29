#!/usr/bin/env bash
# Ghostty Config Dogfooding Test
# Interactive test script for aiterm Ghostty configuration

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  aiterm Ghostty Config Dogfooding Test                    ║${NC}"
echo -e "${BLUE}║  Interactive test for Ghostty 1.2.x integration           ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Check if running interactively
INTERACTIVE=true
if [ ! -t 0 ]; then
    INTERACTIVE=false
fi

# Test counter
TESTS_RUN=0
TESTS_PASSED=0
TESTS_FAILED=0

# Pause between phases
pause_between_phases() {
    if [ "$INTERACTIVE" = true ]; then
        echo ""
        echo -e "${YELLOW}Press ENTER to continue to next phase...${NC}"
        read -r
        echo ""
    fi
}

# Test helper functions
run_test() {
    local test_name="$1"
    local test_cmd="$2"
    local expected_pattern="$3"
    
    TESTS_RUN=$((TESTS_RUN + 1))
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${YELLOW}[TEST $TESTS_RUN]${NC} $test_name"
    echo ""
    
    if output=$(eval "$test_cmd" 2>&1); then
        # Show expected vs actual
        echo -e "${BLUE}Expected Pattern:${NC}"
        echo -e "  ${GREEN}✓${NC} $expected_pattern"
        echo ""
        echo -e "${BLUE}Actual Output:${NC}"
        echo "$output" | sed 's/^/  /'
        echo ""
        
        if echo "$output" | grep -q "$expected_pattern"; then
            echo -e "${GREEN}✓ PASS${NC} - Pattern found in output"
            TESTS_PASSED=$((TESTS_PASSED + 1))
            return 0
        else
            echo -e "${RED}✗ FAIL${NC} - Expected pattern NOT found in output"
            TESTS_FAILED=$((TESTS_FAILED + 1))
            return 1
        fi
    else
        echo -e "${RED}Command failed with exit code $?${NC}"
        echo ""
        echo -e "${BLUE}Expected Pattern:${NC}"
        echo -e "  $expected_pattern"
        echo ""
        echo -e "${BLUE}Actual Output:${NC}"
        echo "$output" | sed 's/^/  /'
        echo ""
        echo -e "${RED}✗ FAIL${NC} - Command execution failed"
        TESTS_FAILED=$((TESTS_FAILED + 1))
        return 1
    fi
}

interactive_test() {
    local test_name="$1"
    local test_cmd="$2"
    
    echo -e "${YELLOW}[INTERACTIVE]${NC} $test_name"
    echo -e "${BLUE}Command:${NC} $test_cmd"
    echo ""
    
    eval "$test_cmd"
    echo ""
    
    read -p "Did this test pass? (y/n): " response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        echo -e "${GREEN}  ✓ PASS (manual)${NC}"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        echo -e "${RED}  ✗ FAIL (manual)${NC}"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
    TESTS_RUN=$((TESTS_RUN + 1))
    echo ""
}

# ============================================================================
# Test Suite
# ============================================================================

echo -e "${BLUE}═══ Phase 1: Ghostty Detection ═══${NC}"
echo ""

run_test "Detect Ghostty terminal" \
    "ait ghostty status" \
    "Running in Ghostty.*Yes"

run_test "Show Ghostty version" \
    "ait --version" \
    "aiterm version"

pause_between_phases

echo -e "${BLUE}═══ Phase 2: Configuration Management ═══${NC}"
echo ""

# Create initial config
echo "theme = nord" > /root/.config/ghostty/config
echo "font-family = JetBrains Mono" >> /root/.config/ghostty/config
echo "font-size = 14" >> /root/.config/ghostty/config

run_test "Parse existing config" \
    "ait ghostty config" \
    "nord"

run_test "Display all 1.2.x settings" \
    "ait ghostty config" \
    "Titlebar Style"

pause_between_phases

echo -e "${BLUE}═══ Phase 3: New 1.2.x Configuration Keys ═══${NC}"
echo ""

run_test "Set macos-titlebar-style" \
    "ait ghostty set macos-titlebar-style tabs" \
    "Set macos-titlebar-style = tabs"

run_test "Verify titlebar style in config" \
    "cat /root/.config/ghostty/config" \
    "macos-titlebar-style = tabs"

run_test "Set background-image" \
    "ait ghostty set background-image /tmp/bg.jpg" \
    "Set background-image = /tmp/bg.jpg"

run_test "Verify background-image in config" \
    "cat /root/.config/ghostty/config" \
    "background-image = /tmp/bg.jpg"

run_test "Set mouse-scroll-multiplier" \
    "ait ghostty set mouse-scroll-multiplier 2.0" \
    "Set mouse-scroll-multiplier = 2.0"

run_test "Verify scroll multiplier in config" \
    "cat /root/.config/ghostty/config" \
    "mouse-scroll-multiplier = 2.0"

pause_between_phases

echo -e "${BLUE}═══ Phase 4: Profile Management with 1.2.x Keys ═══${NC}"
echo ""

run_test "Create profile from current config" \
    "ait ghostty profile create test-profile -d 'Test profile with 1.2.x settings'" \
    "Created profile"

run_test "List profiles" \
    "ait ghostty profile list" \
    "test-profile"

run_test "Show profile details" \
    "ait ghostty profile show test-profile" \
    "tabs"

# Modify config
echo "theme = dracula" > /root/.config/ghostty/config

run_test "Apply profile (restore 1.2.x settings)" \
    "ait ghostty profile apply test-profile" \
    "Applied profile"

run_test "Verify profile restored titlebar style" \
    "cat /root/.config/ghostty/config" \
    "macos-titlebar-style = tabs"

pause_between_phases

echo -e "${BLUE}═══ Phase 5: Theme Management ═══${NC}"
echo ""

interactive_test "List available themes" \
    "ait ghostty theme list"

run_test "Apply catppuccin-mocha theme" \
    "ait ghostty theme apply catppuccin-mocha" \
    "Theme set to"

run_test "Verify theme in config" \
    "cat /root/.config/ghostty/config" \
    "theme = catppuccin-mocha"

pause_between_phases

echo -e "${BLUE}═══ Phase 6: Config Backup and Restore ═══${NC}"
echo ""

run_test "Create config backup" \
    "ait ghostty backup --suffix before-test" \
    "Backup created"

# Modify config
echo "theme = nord" > /root/.config/ghostty/config

run_test "List backups" \
    "ait ghostty restore" \
    "before-test"

echo ""
echo -e "${BLUE}═══ Test Summary ═══${NC}"
echo ""
echo -e "Tests Run:    ${BLUE}$TESTS_RUN${NC}"
echo -e "Tests Passed: ${GREEN}$TESTS_PASSED${NC}"
echo -e "Tests Failed: ${RED}$TESTS_FAILED${NC}"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}╔════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║  ALL TESTS PASSED! ✓                  ║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════╝${NC}"
    exit 0
else
    echo -e "${RED}╔════════════════════════════════════════╗${NC}"
    echo -e "${RED}║  SOME TESTS FAILED ✗                  ║${NC}"
    echo -e "${RED}╚════════════════════════════════════════╝${NC}"
    exit 1
fi
