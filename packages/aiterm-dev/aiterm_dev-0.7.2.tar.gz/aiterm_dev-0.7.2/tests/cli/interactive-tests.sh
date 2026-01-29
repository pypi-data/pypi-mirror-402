#!/bin/bash
# Interactive CLI Test Suite for: aiterm
# Generated: 2025-12-26
# Run: bash tests/cli/interactive-tests.sh
#
# This suite guides you through manual testing with prompts.
# Use for QA, demos, or validating visual output.

set -euo pipefail

# ============================================
# Configuration
# ============================================

PASS=0
FAIL=0
TOTAL=0
TOTAL_TESTS=42  # Includes: 3 smoke + 5 dogfooding + 4 core + 3 claude + 3 mcp + 5 sessions + 4 ide + 2 opencode + 5 terminals + 4 ghostty + 2 error + 2 visual

# Logging
LOG_DIR="${LOG_DIR:-tests/cli/logs}"
mkdir -p "$LOG_DIR" 2>/dev/null || LOG_DIR="/tmp"
LOG_FILE="$LOG_DIR/interactive-test-$(date +%Y%m%d-%H%M%S).log"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" >> "$LOG_FILE"
}

log "=== Interactive Test Session Started ==="
log "Working directory: $(pwd)"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

# ============================================
# Helpers
# ============================================

print_header() {
    echo -e "${BOLD}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${BOLD}  INTERACTIVE CLI TEST SUITE: aiterm ($TOTAL_TESTS tests)${NC}"
    echo -e "${BOLD}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "  ${BLUE}Keys:${NC} y=pass, n=fail, q=quit"
    echo -e "  ${BLUE}Log:${NC}  $LOG_FILE"
    echo ""
}

run_test() {
    local test_num=$1
    local test_name=$2
    local command=$3
    local expected=$4

    TOTAL=$((TOTAL + 1))

    # Header
    echo ""
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BOLD}TEST $test_num/$TOTAL_TESTS: $test_name${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "  ${BLUE}Command:${NC} $command"
    echo ""

    log "TEST $test_num: $test_name"
    log "  Command: $command"

    # Run command and capture output
    local output
    output=$(bash -c "$command" 2>&1) || true
    log "  Output: $output"

    # Show expected vs actual side by side
    echo -e "${BLUE}EXPECTED:${NC} $expected"
    echo ""
    echo -e "${GREEN}ACTUAL:${NC}"
    echo "$output"
    echo ""

    # Single prompt: pass/fail/quit
    read -p "[y=pass, n=fail, q=quit] " -n 1 -r
    echo ""

    case "$REPLY" in
        [Yy])
            PASS=$((PASS + 1))
            log "  Result: PASS"
            echo -e "${GREEN}✅ PASS${NC}"
            ;;
        [Qq])
            log "User quit at test $test_num"
            echo -e "${YELLOW}Exiting...${NC}"
            print_summary
            exit 0
            ;;
        *)
            FAIL=$((FAIL + 1))
            log "  Result: FAIL"
            echo -e "${RED}❌ FAIL${NC}"
            ;;
    esac
}

print_summary() {
    echo ""
    echo -e "${BOLD}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${BOLD}  RESULTS: $PASS passed, $FAIL failed (of $TOTAL run)${NC}"
    echo -e "${BOLD}═══════════════════════════════════════════════════════════════${NC}"

    if [[ $FAIL -eq 0 ]]; then
        echo -e "${GREEN}${BOLD}🎉 ALL TESTS PASSED!${NC}"
        log "Final: ALL TESTS PASSED ($PASS/$TOTAL)"
    else
        echo -e "${RED}${BOLD}⚠️  $FAIL TEST(S) FAILED${NC}"
        log "Final: $FAIL TESTS FAILED"
    fi

    log "Summary: $PASS passed, $FAIL failed"
    echo -e "Log: ${BLUE}$LOG_FILE${NC}"
    echo ""
}

# ============================================
# Main
# ============================================

print_header

# ============================================
# SMOKE TESTS
# ============================================

run_test 1 "Version Check" \
    "ait --version" \
    "Version string (e.g., 'aiterm 0.3.0')"

run_test 2 "Help Output" \
    "ait --help" \
    "Help text with Commands list showing: doctor, detect, switch, claude, mcp, sessions, ide"

run_test 3 "aiterm Alias" \
    "aiterm --version" \
    "Same version output as 'ait --version'"

# ============================================
# DOGFOODING COMMANDS
# ============================================

run_test 4 "Hello Command" \
    "ait hello" \
    "Friendly greeting with project info (name, version, diagnostics)"

run_test 5 "Hello with Name" \
    "ait hello --name 'Test User'" \
    "Personalized greeting to 'Test User'"

run_test 6 "Goodbye Command" \
    "ait goodbye" \
    "Farewell message with session summary"

run_test 7 "Info Command" \
    "ait info" \
    "Detailed system info: Python version, platform, terminal, paths"

run_test 8 "Info JSON Output" \
    "ait info --json 2>/dev/null || ait info" \
    "JSON formatted output (or standard if --json not supported)"

# ============================================
# CORE COMMANDS
# ============================================

run_test 9 "Doctor Check" \
    "ait doctor" \
    "System diagnostics with pass/warn status indicators"

run_test 10 "Context Detection" \
    "ait detect" \
    "Project context showing: type (python/r-package/etc), path, git info"

run_test 11 "Context Switch" \
    "ait switch" \
    "Terminal profile applied (may show visual change if iTerm2)"

run_test 12 "Detect with Path" \
    "ait detect ." \
    "Same context info for current directory"

# ============================================
# CLAUDE SUBCOMMANDS
# ============================================

run_test 13 "Claude Settings" \
    "ait claude settings" \
    "Display of ~/.claude/settings.json contents (or message if not found)"

run_test 14 "Claude Approvals List" \
    "ait claude approvals list" \
    "List of auto-approval patterns (may be empty)"

run_test 15 "Claude Backup" \
    "ait claude backup --dry-run 2>/dev/null || ait claude backup" \
    "Backup created or dry-run showing what would be backed up"

# ============================================
# MCP SUBCOMMANDS
# ============================================

run_test 16 "MCP List" \
    "ait mcp list" \
    "List of configured MCP servers (filesystem, statistical-research, etc.)"

run_test 17 "MCP Validate" \
    "ait mcp validate" \
    "Validation results for MCP configuration"

run_test 18 "MCP Test All" \
    "ait mcp test-all" \
    "Status of each MCP server (reachable/unreachable)"

# ============================================
# SESSIONS SUBCOMMANDS
# ============================================

run_test 19 "Sessions Live" \
    "ait sessions live" \
    "Session list OR 'No active sessions' (runs outside Claude Code)"

run_test 20 "Sessions Conflicts" \
    "ait sessions conflicts" \
    "Conflict check OR 'No conflicts' message"

run_test 21 "Sessions History" \
    "ait sessions history" \
    "Archived session dates (grouped by date)"

run_test 22 "Sessions Current" \
    "ait sessions current" \
    "'No active session' (tests run outside Claude Code context)"

run_test 23 "Sessions Prune" \
    "ait sessions prune" \
    "Prune stale sessions (removes sessions with dead PIDs)"

# ============================================
# IDE SUBCOMMANDS
# ============================================

run_test 24 "IDE List" \
    "ait ide list" \
    "Table of supported IDEs with installation status"

run_test 25 "IDE Status (VS Code)" \
    "ait ide status vscode" \
    "Detailed VS Code status with config paths"

run_test 26 "IDE Compare" \
    "ait ide compare" \
    "Comparison of configurations across installed IDEs"

run_test 27 "IDE Extensions" \
    "ait ide extensions vscode" \
    "Recommended AI extensions for VS Code"

# ============================================
# OPENCODE SUBCOMMANDS
# ============================================

run_test 28 "OpenCode Config" \
    "ait opencode config" \
    "Current OpenCode configuration (model, MCP servers, etc.)"

run_test 29 "OpenCode Summary" \
    "ait opencode summary" \
    "Complete OpenCode configuration summary"

# ============================================
# TERMINALS SUBCOMMANDS (v0.3.8+)
# ============================================

run_test 30 "Terminals List" \
    "ait terminals list" \
    "Table of supported terminals with installation status, version, and features"

run_test 31 "Terminals Detect" \
    "ait terminals detect" \
    "Current terminal detected (iterm2/ghostty/wezterm/etc) with version and features"

run_test 32 "Terminals Features" \
    "ait terminals features iterm2" \
    "List of iTerm2 features (profiles, tab_title, badge, etc.)"

run_test 33 "Terminals Compare" \
    "ait terminals compare" \
    "Side-by-side comparison of terminal features"

run_test 34 "Terminals Config" \
    "ait terminals config iterm2" \
    "Configuration file path for iTerm2"

# ============================================
# GHOSTTY TERMINAL (v0.3.8+)
# ============================================

run_test 35 "Ghostty in Terminals List" \
    "ait terminals list 2>&1 | grep -i ghostty" \
    "Ghostty row showing: installed status, version (1.x), features (tab_title, themes)"

run_test 36 "Ghostty Features" \
    "ait terminals features ghostty" \
    "Features: tab_title, themes, native_ui + config path"

run_test 37 "Ghostty Config Path" \
    "ait terminals config ghostty" \
    "Config path: ~/.config/ghostty/config"

run_test 38 "Ghostty Detection (if running in Ghostty)" \
    "ait terminals detect" \
    "Should detect 'ghostty' if running in Ghostty terminal"

# ============================================
# ERROR HANDLING
# ============================================

run_test 39 "Invalid Command" \
    "ait nonexistent-command 2>&1" \
    "Error message or usage info (graceful handling)"

run_test 40 "Invalid Subcommand" \
    "ait claude nonexistent 2>&1" \
    "Error message for unknown subcommand"

# ============================================
# VISUAL/TERMINAL FEATURES
# ============================================

run_test 41 "Rich Output Formatting" \
    "ait doctor" \
    "Colored output with tables, checkmarks, emoji"

run_test 42 "Profile Display" \
    "ait profile list 2>/dev/null || echo 'Profile command not implemented'" \
    "List of available terminal profiles"

# ============================================
# Summary
# ============================================

log "=== Session Completed ==="
print_summary
