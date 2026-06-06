#!/bin/bash
# ============================================================================
# Alga Agent Installer Wrapper
# ============================================================================
# This script forwards to scripts/install.sh.
# ============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ -f "$SCRIPT_DIR/scripts/install.sh" ]; then
    exec bash "$SCRIPT_DIR/scripts/install.sh" "$@"
else
    # Fallback if scripts/install.sh is not present locally (e.g., downloaded standalone)
    curl -fsSL https://raw.githubusercontent.com/hahnavi/alga-agent/alga-agent/scripts/install.sh | bash -s -- "$@"
fi
