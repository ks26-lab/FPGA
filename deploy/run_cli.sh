#!/bin/bash
# ==============================================================================
# run_cli.sh
# Primary hardware launch script for Zynq ARM Linux (PuTTY / Serial session)
# ==============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Ensure we run from workspace root
cd "$WORKSPACE_ROOT"

# Ensure Python can locate the universal communication modules
export PYTHONPATH="$WORKSPACE_ROOT:$PYTHONPATH"

# Check if running as root
if [ "$EUID" -ne 0 ]; then
  echo "[NOTICE] Elevating permissions with sudo for /dev/mem AXI access..."
  exec sudo env PYTHONPATH="$PYTHONPATH" python3 "$WORKSPACE_ROOT/python/main.py" --hw "$@"
else
  exec python3 "$WORKSPACE_ROOT/python/main.py" --hw "$@"
fi
