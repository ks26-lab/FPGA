#!/bin/bash
# ==============================================================================
# setup_zynq.sh
# Environment configuration and dependency verification for EDGE ZYNQ Z7010
# ==============================================================================

set -e

echo "=========================================================="
echo "    EDGE ZYNQ Z7010 FPGA CONTROL SYSTEM — ENVIRONMENT SETUP"
echo "=========================================================="

# 1. Verify Root / Sudo Privileges (Mandatory for /dev/mem access)
if [ "$EUID" -ne 0 ]; then
  echo "[WARNING] Not running as root. /dev/mem access requires root/sudo."
  echo "          Run this script or the CLI with: sudo ./run_cli.sh"
fi

# 2. Check Architecture
ARCH=$(uname -m)
echo "[INFO] Host Architecture: $ARCH"
if [[ "$ARCH" != *"arm"* && "$ARCH" != *"aarch64"* ]]; then
  echo "[NOTICE] Non-ARM processor detected. If running on host PC, use --mock mode."
fi

# 3. Check /dev/mem
if [ -e "/dev/mem" ]; then
  echo "[OK] /dev/mem device node exists."
else
  echo "[ERROR] /dev/mem device node NOT found. Ensure kernel is configured with CONFIG_DEVMEM=y."
  exit 1
fi

# 4. Check Python 3
if command -v python3 &>/dev/null; then
  PY_VER=$(python3 --version)
  echo "[OK] Found Python: $PY_VER"
else
  echo "[ERROR] Python 3 is not installed. Install via: apt update && apt install python3 python3-pip"
  exit 1
fi

# 5. Check FPGA Bitstream State via sysfs (if xilinx-fpga manager driver is present)
if [ -d "/sys/class/fpga_manager/fpga0" ]; then
  FPGA_STATE=$(cat /sys/class/fpga_manager/fpga0/state 2>/dev/null || echo "unknown")
  echo "[INFO] FPGA Manager State: $FPGA_STATE"
fi

# 6. Make launcher executable
chmod +x run_cli.sh 2>/dev/null || true

echo "=========================================================="
echo "[SUCCESS] Zynq environment verified. Ready to run."
echo "Launch universal control system with: sudo ./run_cli.sh"
echo "=========================================================="
