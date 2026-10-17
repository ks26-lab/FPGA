#!/usr/bin/env python3
"""
run_cli.py
==========
Workspace root entrypoint for the Universal Zynq Z7010 Multi-Scene FPGA Control System.
"""

import sys
import os

WORKSPACE_ROOT = os.path.dirname(os.path.abspath(__file__))
if WORKSPACE_ROOT not in sys.path:
    sys.path.insert(0, WORKSPACE_ROOT)

from python.main import main

if __name__ == "__main__":
    main()
