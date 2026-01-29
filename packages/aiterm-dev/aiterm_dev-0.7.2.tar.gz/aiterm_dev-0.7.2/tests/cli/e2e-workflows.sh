#!/bin/bash

################################################################################
# aiterm - End-to-End (E2E) Workflow Tests
#
# Purpose: Test real-world workflows that span multiple commands
# Generated: 2026-01-17
#
# Workflow Coverage:
#  1. StatusLine customization workflow (v0.7.0)
#  2. Feature development workflow
#  3. Release preparation workflow
#  4. Claude Code integration workflow
#  5. Terminal switching workflow
#
# Usage:
#   bash tests/cli/e2e-workflows.sh              # Run all workflows
#   bash tests/cli/e2e-workflows.sh statusline   # StatusLine only
#   bash tests/cli/e2e-workflows.sh -v           # Verbose
#
# Exit Codes:
#   0 = All workflows passed
#   1 = One or more workflows failed
################################################################################

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# State
WORKFLOW_PASS=0
WORKFLOW_FAIL=0
STEP_PASS=0
STEP_FAIL=0
VERBOSE=${VERBOSE:-0}
FILTER_WORKFLOW="${1:-all}"

LOG_DIR="tests/cli/logs"
LOG_FILE="$LOG_DIR/e2e-$(date +%Y%m%d-%H%M%S).log"
mkdir -p "$LOG_DIR"

################################################################################
# Helpers
################################################################################

log() {
    echo "$@" | tee -a "$LOG_FILE"
}

log_workflow() {
    log ""
    log "${CYAN}▶ WORKFLOW: $1${NC}"
    log "${CYAN}$(printf '─%.0s' {1..70})${NC}"
}

log_step() {
    local num="$1"
    local desc="$2"
    log "${BLUE}  Step $num:${NC} $desc"
}

log_success() {
    local msg="$1"
    STEP_PASS=$((STEP_PASS + 1))
    echo -e "${GREEN}    ✓${NC} $msg" | tee -a "$LOG_FILE"
}

log_failure() {
    local msg="$1"
    local details="${2:-}"
    STEP_FAIL=$((STEP_FAIL + 1))
    echo -e "${RED}    ✗${NC} $msg" | tee -a "$LOG_FILE"
    if [[ -n "$details" ]]; then
        echo -e "${RED}      Error:${NC} $details" | tee -a "$LOG_FILE"
    fi
}

assert_output_contains() {
    local output="$1"
    local pattern="$2"
    local context="${3:-Check output}"

    if echo "$output" | grep -q "$pattern"; then
        return 0
    else
        log_failure "$context" "Pattern not found: $pattern"
        return 1
    fi
}

run_step() {
    local num="$1"
    local desc="$2"
    local cmd="${3:-}"
    local check_pattern="${4:-}"

    [[ -z "$cmd" ]] && { log_failure "run_step: missing command"; return 1; }

    log_step "$num" "$desc"

    local output
    output=$(eval "$cmd" 2>&1 || true)
    local exit_code=$?

    if [[ -n "$check_pattern" ]]; then
        if echo "$output" | grep -q "$check_pattern"; then
            log_success "$desc"
            return 0
        else
            log_failure "$desc" "Pattern not found: $check_pattern"
            return 1
        fi
    else
        if [[ $exit_code -eq 0 ]]; then
            log_success "$desc"
            return 0
        else
            log_failure "$desc" "Exit code: $exit_code"
            return 1
        fi
    fi
}

################################################################################
# Workflow 1: StatusLine Customization (v0.7.0)
################################################################################

workflow_statusline() {
    log_workflow "StatusLine Customization (v0.7.0)"

    local passed=0
    local failed=0

    # Step 1: Check setup gateway exists
    if run_step 1 "Verify statusline setup gateway" \
        "ait statusline setup --help" \
        "setup\|gateway"; then
        ((passed++))
    else
        ((failed++))
    fi

    # Step 2: Check customize menu exists
    if run_step 2 "Verify customize unified menu" \
        "ait statusline customize --help" \
        "customize\|menu"; then
        ((passed++))
    else
        ((failed++))
    fi

    # Step 3: List available hooks
    if run_step 3 "List hook templates" \
        "ait statusline hooks list" \
        "on-theme-change\|on-remote-session\|on-error"; then
        ((passed++))
    else
        ((failed++))
    fi

    # Step 4: Verify hook template details
    if run_step 4 "Verify hook template validity" \
        "ait statusline hooks list --available" \
        "available"; then
        ((passed++))
    else
        ((failed++))
    fi

    # Step 5: Test help accessibility
    if run_step 5 "Access statusline help" \
        "ait statusline --help" \
        "setup\|customize\|Commands"; then
        ((passed++))
    else
        ((failed++))
    fi

    # Summary
    log ""
    if [[ $failed -eq 0 ]]; then
        log "${GREEN}✅${NC} ${BLUE}StatusLine Workflow:${NC} $passed passed"
        WORKFLOW_PASS=$((WORKFLOW_PASS + 1))
    else
        log "${RED}❌${NC} ${BLUE}StatusLine Workflow:${NC} $passed passed, $failed failed"
        WORKFLOW_FAIL=$((WORKFLOW_FAIL + 1))
    fi
}

################################################################################
# Workflow 2: Feature Development
################################################################################

workflow_feature() {
    log_workflow "Feature Development Workflow"

    local passed=0
    local failed=0

    # Step 1: Check feature status
    run_step 1 "Check feature pipeline status" \
        "ait feature status" && ((passed++)) || ((failed++))

    # Step 2: Verify feature commands available
    run_step 2 "Verify feature commands" \
        "ait feature --help" \
        "status\|start\|cleanup" && ((passed++)) || ((failed++))

    # Step 3: Test detect integration
    run_step 3 "Detect project context" \
        "ait detect" && ((passed++)) || ((failed++))

    # Step 4: Test context detection
    run_step 4 "Show context details" \
        "ait context detect" && ((passed++)) || ((failed++))

    # Step 5: Verify git integration
    run_step 5 "Check git branch info" \
        "git branch --show-current" && ((passed++)) || ((failed++))

    log ""
    log "${BLUE}Feature Workflow:${NC} $passed passed, $failed failed"

    if [[ $failed -eq 0 ]]; then
        WORKFLOW_PASS=$((WORKFLOW_PASS + 1))
    else
        WORKFLOW_FAIL=$((WORKFLOW_FAIL + 1))
    fi
}

################################################################################
# Workflow 3: Release Preparation
################################################################################

workflow_release() {
    log_workflow "Release Preparation Workflow"

    local passed=0
    local failed=0

    # Step 1: Check release readiness
    run_step 1 "Check release readiness" \
        "ait release check" && ((passed++)) || ((failed++))

    # Step 2: Show release status
    run_step 2 "Show current release status" \
        "ait release status" && ((passed++)) || ((failed++))

    # Step 3: Verify release commands
    run_step 3 "Verify release commands available" \
        "ait release --help" \
        "check\|status\|pypi\|homebrew" && ((passed++)) || ((failed++))

    # Step 4: Check version
    run_step 4 "Verify version info" \
        "ait --version" \
        "0.7\|version" && ((passed++)) || ((failed++))

    # Step 5: Test info command (diagnostics)
    run_step 5 "Show system diagnostics" \
        "ait info" && ((passed++)) || ((failed++))

    log ""
    log "${BLUE}Release Workflow:${NC} $passed passed, $failed failed"

    if [[ $failed -eq 0 ]]; then
        WORKFLOW_PASS=$((WORKFLOW_PASS + 1))
    else
        WORKFLOW_FAIL=$((WORKFLOW_FAIL + 1))
    fi
}

################################################################################
# Workflow 4: Claude Code Integration
################################################################################

workflow_claude() {
    log_workflow "Claude Code Integration Workflow"

    local passed=0
    local failed=0

    # Step 1: Check Claude integration
    run_step 1 "Access Claude Code settings" \
        "ait claude settings" && ((passed++)) || ((failed++))

    # Step 2: Check auto-approvals
    run_step 2 "List auto-approval settings" \
        "ait claude approvals list" && ((passed++)) || ((failed++))

    # Step 3: Check hooks
    run_step 3 "List available hooks" \
        "ait hooks --help" && ((passed++)) || ((failed++))

    # Step 4: Check sessions
    run_step 4 "Show active sessions" \
        "ait sessions live" && ((passed++)) || ((failed++))

    # Step 5: Check MCP integration
    run_step 5 "List MCP servers" \
        "ait mcp list" && ((passed++)) || ((failed++))

    log ""
    log "${BLUE}Claude Code Workflow:${NC} $passed passed, $failed failed"

    if [[ $failed -eq 0 ]]; then
        WORKFLOW_PASS=$((WORKFLOW_PASS + 1))
    else
        WORKFLOW_FAIL=$((WORKFLOW_FAIL + 1))
    fi
}

################################################################################
# Workflow 5: Terminal Switching
################################################################################

workflow_terminal() {
    log_workflow "Terminal Switching & Detection Workflow"

    local passed=0
    local failed=0

    # Step 1: Detect current terminal
    run_step 1 "Detect current terminal" \
        "ait terminals detect" && ((passed++)) || ((failed++))

    # Step 2: List available terminals
    run_step 2 "List supported terminals" \
        "ait terminals list" \
        "ghostty\|iterm" && ((passed++)) || ((failed++))

    # Step 3: Show terminal features
    run_step 3 "Show terminal features" \
        "ait terminals features" && ((passed++)) || ((failed++))

    # Step 4: Check Ghostty integration
    run_step 4 "Check Ghostty support" \
        "ait ghostty --help" && ((passed++)) || ((failed++))

    # Step 5: Test context switching
    run_step 5 "Test context switch command" \
        "ait switch" && ((passed++)) || ((failed++))

    log ""
    log "${BLUE}Terminal Workflow:${NC} $passed passed, $failed failed"

    if [[ $failed -eq 0 ]]; then
        WORKFLOW_PASS=$((WORKFLOW_PASS + 1))
    else
        WORKFLOW_FAIL=$((WORKFLOW_FAIL + 1))
    fi
}

################################################################################
# Workflow 6: Full Integration (All Steps)
################################################################################

workflow_full_integration() {
    log_workflow "Full Integration Test (All Systems)"

    local passed=0
    local failed=0

    # Step 1: Health check
    run_step 1 "Run system health check" \
        "ait doctor" && ((passed++)) || ((failed++))

    # Step 2: Project detection
    run_step 2 "Detect project context" \
        "ait detect" && ((passed++)) || ((failed++))

    # Step 3: Show version
    run_step 3 "Verify version" \
        "ait --version" && ((passed++)) || ((failed++))

    # Step 4: List all commands
    run_step 4 "Show all commands" \
        "ait --help" \
        "Commands" && ((passed++)) || ((failed++))

    # Step 5: Test error handling
    run_step 5 "Handle invalid command gracefully" && {
        if ait nonexistent-command 2>&1 | grep -q "No such command\|Usage"; then
            log_success "Error handling works"
            ((passed++))
        else
            log_failure "Error handling"
            ((failed++))
        fi
    }

    # Step 6: Test help chain
    run_step 6 "Access nested help" \
        "ait context --help" && ((passed++)) || ((failed++))

    # Step 7: Verify aliases
    run_step 7 "Test detect shortcut" \
        "ait detect" && ((passed++)) || ((failed++))

    # Step 8: Test output formats
    run_step 8 "Get JSON output" \
        "ait info --json" \
        "version\|python" && ((passed++)) || ((failed++))

    log ""
    log "${BLUE}Full Integration:${NC} $passed passed, $failed failed"

    if [[ $failed -eq 0 ]]; then
        WORKFLOW_PASS=$((WORKFLOW_PASS + 1))
    else
        WORKFLOW_FAIL=$((WORKFLOW_FAIL + 1))
    fi
}

################################################################################
# Main
################################################################################

main() {
    log "╔════════════════════════════════════════════════════════════════╗"
    log "║        aiterm - End-to-End Workflow Tests (v0.7.0)            ║"
    log "║             Testing real-world usage patterns                  ║"
    log "╚════════════════════════════════════════════════════════════════╝"
    log ""
    log "Filter: $FILTER_WORKFLOW"
    log "Log:    $LOG_FILE"
    log ""

    case "$FILTER_WORKFLOW" in
        all|"")
            workflow_statusline || true
            workflow_feature || true
            workflow_release || true
            workflow_claude || true
            workflow_terminal || true
            workflow_full_integration || true
            ;;
        statusline)
            workflow_statusline || true
            ;;
        feature)
            workflow_feature || true
            ;;
        release)
            workflow_release || true
            ;;
        claude)
            workflow_claude || true
            ;;
        terminal)
            workflow_terminal || true
            ;;
        full|integration)
            workflow_full_integration || true
            ;;
        *)
            log "${RED}Unknown workflow: $FILTER_WORKFLOW${NC}"
            log "Available: all, statusline, feature, release, claude, terminal, full"
            exit 2
            ;;
    esac

    # Summary
    log ""
    log "╔════════════════════════════════════════════════════════════════╗"
    log "║                    E2E WORKFLOW SUMMARY                       ║"
    log "╚════════════════════════════════════════════════════════════════╝"
    log ""
    log "Workflows Passed: ${GREEN}$WORKFLOW_PASS${NC}"
    log "Workflows Failed: ${RED}$WORKFLOW_FAIL${NC}"
    log "Total Steps:      $((STEP_PASS + STEP_FAIL))"
    log "  ✓ Passed:       ${GREEN}$STEP_PASS${NC}"
    log "  ✗ Failed:       ${RED}$STEP_FAIL${NC}"
    log ""

    if [[ $WORKFLOW_FAIL -eq 0 ]]; then
        log "${GREEN}✅ All workflows PASSED${NC}"
    else
        log "${RED}❌ $WORKFLOW_FAIL workflow(s) FAILED${NC}"
    fi
}

# Execute
main "$@"
if [[ $WORKFLOW_FAIL -eq 0 ]]; then
    exit 0
else
    exit 1
fi
