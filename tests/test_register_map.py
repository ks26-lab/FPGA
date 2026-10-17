"""
tests.test_register_map
=======================
Unit tests for the AXI register map and bit packing/unpacking helpers.
"""

import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fpga_interface.python.register_map import (
    AXI_BASE_ADDR,
    REG_CONTROL,
    REG_DEPTH_CFG,
    REG_CURRENT,
    REG_STATUS,
    REG_POSITION,
    REG_COUNTERS,
    REG_CYCLES,
    pack_control,
    pack_depth_cfg,
    unpack_depth_cfg,
    pack_current,
    unpack_current,
)
from fpga_interface.python.protocol import (
    depth_to_fpga_units,
    fpga_units_to_depth,
    validate_current,
)


class TestRegisterMap(unittest.TestCase):

    def test_base_address(self):
        self.assertEqual(AXI_BASE_ADDR, 0x43C00000)

    def test_depth_scaling(self):
        # 50.0 m -> 500 FPGA units
        self.assertEqual(depth_to_fpga_units(50.0), 500)
        self.assertAlmostEqual(fpga_units_to_depth(500), 50.0)

        # 80.0 m -> 800 FPGA units
        self.assertEqual(depth_to_fpga_units(80.0), 800)
        self.assertAlmostEqual(fpga_units_to_depth(800), 80.0)

        # 74.3 m -> 743 units
        self.assertEqual(depth_to_fpga_units(74.3), 743)
        self.assertAlmostEqual(fpga_units_to_depth(743), 74.3)

    def test_pack_control(self):
        # cmd_start (bit 0)
        self.assertEqual(pack_control(start=True), 0x01)
        # cmd_stop (bit 1)
        self.assertEqual(pack_control(stop=True), 0x02)
        # cmd_reset (bit 2)
        self.assertEqual(pack_control(reset=True), 0x04)
        # cmd_disturb_strobe (bit 3) with disturb_type=3 (WHALE, bits [5:4])
        # bit 3 = 0x08, bits [5:4] = 3 << 4 = 0x30 => 0x38
        self.assertEqual(pack_control(disturb_strobe=True, disturb_type=3), 0x38)
        # cfg_set_depth_we (bit 6)
        self.assertEqual(pack_control(set_depth_we=True), 0x40)

    def test_pack_unpack_depth_cfg(self):
        # set_depth = 500 (50.0m), target_depth = 800 (80.0m)
        packed = pack_depth_cfg(500, 800)
        # bits [15:0] = 500 (0x01F4), bits [31:16] = 800 (0x0320)
        # packed = 0x032001F4
        self.assertEqual(packed, (800 << 16) | 500)

        unpacked_set, unpacked_tgt = unpack_depth_cfg(packed)
        self.assertEqual(unpacked_set, 500)
        self.assertEqual(unpacked_tgt, 800)

    def test_pack_unpack_current(self):
        # Positive current
        p_val = pack_current(20)
        self.assertEqual(p_val, 20)
        self.assertEqual(unpack_current(p_val), 20)

        # Negative current (-30)
        # Signed 8-bit two's complement of -30 is 226 (0xE2)
        n_val = pack_current(-30)
        self.assertEqual(n_val & 0xFF, 226)
        self.assertEqual(unpack_current(n_val), -30)


if __name__ == "__main__":
    unittest.main()
