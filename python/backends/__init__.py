"""
Execution backends for FPGA Hardware and Software RTL Emulation.
"""

from .base_backend import BaseExecutionBackend
from .fpga_backend import FPGAHardwareBackend
from .laptop_fpga_backend import LaptopFPGAEmulator

def detect_and_create_backend(requested_mode: str = "auto") -> BaseExecutionBackend:
    """
    Factory creating appropriate execution backend.
    
    Modes:
    - 'auto': Tests if /dev/mem and Zynq FPGA hardware is available.
              Uses FPGAHardwareBackend if available, else falls back to LaptopFPGAEmulator.
    - 'fpga': Forces FPGAHardwareBackend; fails if hardware is absent.
    - 'emulator': Forces LaptopFPGAEmulator.
    """
    mode = requested_mode.lower().strip()
    
    if mode == "fpga":
        backend = FPGAHardwareBackend()
        if not backend.is_available():
            raise RuntimeError(
                "FPGA hardware execution requested (--mode fpga), but /dev/mem is not available "
                "or not running on Zynq ARM Linux."
            )
        return backend
    
    elif mode == "emulator":
        return LaptopFPGAEmulator()
    
    elif mode == "auto":
        fpga = FPGAHardwareBackend()
        if fpga.is_available():
            return fpga
        return LaptopFPGAEmulator()
    
    else:
        raise ValueError(f"Unknown execution mode '{requested_mode}'. Supported: 'auto', 'fpga', 'emulator'.")

__all__ = [
    "BaseExecutionBackend",
    "FPGAHardwareBackend",
    "LaptopFPGAEmulator",
    "detect_and_create_backend",
]
