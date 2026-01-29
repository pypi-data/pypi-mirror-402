#!/bin/bash
# install-symlink.sh - Install aiterm integration into flow-cli
#
# This script creates a symlink from flow-cli to aiterm's integration file,
# enabling the `tm` dispatcher command in flow-cli.
#
# Usage:
#   ./install-symlink.sh              # Auto-detect flow-cli location
#   FLOW_PLUGIN_DIR=/path ./install-symlink.sh  # Specify location

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Get aiterm directory (parent of this script)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
AITERM_DIR="$(dirname "$SCRIPT_DIR")"

# Source file
SOURCE="$SCRIPT_DIR/aiterm.zsh"

# Find flow-cli directory
find_flow_cli() {
    # Check environment variable first
    if [[ -n "$FLOW_PLUGIN_DIR" && -d "$FLOW_PLUGIN_DIR" ]]; then
        echo "$FLOW_PLUGIN_DIR"
        return 0
    fi

    # Common locations
    local locations=(
        "$HOME/projects/dev-tools/flow-cli"
        "$HOME/.local/share/flow-cli"
        "$HOME/.flow-cli"
        "${XDG_DATA_HOME:-$HOME/.local/share}/flow-cli"
    )

    for loc in "${locations[@]}"; do
        if [[ -d "$loc" && -f "$loc/flow.plugin.zsh" ]]; then
            echo "$loc"
            return 0
        fi
    done

    # Try to find via zsh plugin managers
    if [[ -d "$HOME/.oh-my-zsh/custom/plugins/flow-cli" ]]; then
        echo "$HOME/.oh-my-zsh/custom/plugins/flow-cli"
        return 0
    fi

    if [[ -d "$HOME/.zsh/plugins/flow-cli" ]]; then
        echo "$HOME/.zsh/plugins/flow-cli"
        return 0
    fi

    return 1
}

# Main
main() {
    echo -e "${BLUE}aiterm flow-cli Integration Installer${NC}"
    echo ""

    # Check source exists
    if [[ ! -f "$SOURCE" ]]; then
        echo -e "${RED}Error: Source file not found: $SOURCE${NC}"
        exit 1
    fi

    # Find flow-cli
    FLOW_DIR=$(find_flow_cli)
    if [[ -z "$FLOW_DIR" ]]; then
        echo -e "${RED}Error: flow-cli not found${NC}"
        echo ""
        echo "Please set FLOW_PLUGIN_DIR to your flow-cli location:"
        echo "  FLOW_PLUGIN_DIR=/path/to/flow-cli $0"
        exit 1
    fi

    echo -e "Found flow-cli: ${GREEN}$FLOW_DIR${NC}"

    # Target directory and file
    TARGET_DIR="$FLOW_DIR/zsh/functions"
    TARGET="$TARGET_DIR/aiterm-integration.zsh"

    # Create target directory if needed
    if [[ ! -d "$TARGET_DIR" ]]; then
        echo -e "Creating: ${YELLOW}$TARGET_DIR${NC}"
        mkdir -p "$TARGET_DIR"
    fi

    # Check if symlink already exists
    if [[ -L "$TARGET" ]]; then
        EXISTING=$(readlink "$TARGET")
        if [[ "$EXISTING" == "$SOURCE" ]]; then
            echo -e "${GREEN}Already installed (symlink exists)${NC}"
            echo ""
            echo "To reinstall, remove the symlink first:"
            echo "  rm $TARGET"
            exit 0
        else
            echo -e "${YELLOW}Existing symlink points to: $EXISTING${NC}"
            echo -e "Updating to: ${GREEN}$SOURCE${NC}"
            rm "$TARGET"
        fi
    elif [[ -f "$TARGET" ]]; then
        echo -e "${YELLOW}Warning: Regular file exists at $TARGET${NC}"
        echo "Backing up to ${TARGET}.bak"
        mv "$TARGET" "${TARGET}.bak"
    fi

    # Create symlink
    ln -sf "$SOURCE" "$TARGET"

    echo -e "${GREEN}Symlink created:${NC}"
    echo "  $TARGET"
    echo "  -> $SOURCE"
    echo ""

    # Verify
    if [[ -L "$TARGET" && -e "$TARGET" ]]; then
        echo -e "${GREEN}Installation successful!${NC}"
        echo ""
        echo "To activate, restart your shell or run:"
        echo "  source ~/.zshrc"
        echo ""
        echo "Then try:"
        echo "  tm help"
    else
        echo -e "${RED}Installation failed - symlink not working${NC}"
        exit 1
    fi
}

# Uninstall option
if [[ "$1" == "--uninstall" || "$1" == "-u" ]]; then
    FLOW_DIR=$(find_flow_cli)
    if [[ -n "$FLOW_DIR" ]]; then
        TARGET="$FLOW_DIR/zsh/functions/aiterm-integration.zsh"
        if [[ -L "$TARGET" ]]; then
            rm "$TARGET"
            echo -e "${GREEN}Symlink removed: $TARGET${NC}"
        else
            echo "No symlink found at $TARGET"
        fi
    else
        echo "flow-cli not found"
    fi
    exit 0
fi

# Help
if [[ "$1" == "--help" || "$1" == "-h" ]]; then
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Install aiterm integration into flow-cli via symlink."
    echo ""
    echo "Options:"
    echo "  --uninstall, -u    Remove the symlink"
    echo "  --help, -h         Show this help"
    echo ""
    echo "Environment:"
    echo "  FLOW_PLUGIN_DIR    Path to flow-cli (auto-detected if not set)"
    exit 0
fi

main "$@"
