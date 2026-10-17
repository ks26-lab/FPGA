# Zynq Linux Setup & Hardware Execution Procedure

## 1. Operating System Environment

The EDGE ZYNQ Z7010 SoC contains dual ARM Cortex-A9 cores running embedded Linux.
Supported operating environments:
- Petalinux 2020.2+
- Ubuntu 18.04/20.04 ARM rootfs
- PYNQ Linux v2.6+

### Kernel Requirements:
1. `CONFIG_DEVMEM=y` (allows memory-mapped access to physical PL peripherals via `/dev/mem`).
2. `CONFIG_STRICT_DEVMEM=n` (or boot with `iomem=relaxed` in U-Boot kernel arguments to access physical addresses in the `0x40000000 - 0x7FFFFFFF` PL aperture).

---

## 2. Vivado PL Bitstream Programming

Before running software, the Zynq Programmable Logic must be configured:

### Method A: JTAG via Vivado Hardware Manager
1. Open Vivado on Host PC.
2. Connect JTAG micro-USB cable.
3. Open Target -> Program Device.
4. Select bitstream (`.bit`) and debug probes (`.ltx` if present).
5. Verify `DONE` LED illuminates green on the EDGE ZYNQ board.

### Method B: SD Card Boot (`boot.bin`)
Package `FSBL.elf`, `bitstream.bit`, and `u-boot.elf` into `boot.bin` via Vivado / Vitis Bootgen and copy to FAT32 boot partition of micro-SD card.

### Method C: Linux FPGA Manager
On Zynq Linux command line:
```bash
echo 0 > /sys/class/fpga_manager/fpga0/flags
cp bitstream.bit.bin /lib/firmware/
echo bitstream.bit.bin > /sys/class/fpga_manager/fpga0/firmware
```

---

## 3. PuTTY Runtime Configuration

1. Launch PuTTY on Host PC.
2. Select **Serial** connection.
3. Set **Serial line** to the Silicon Labs / FTDI COM port (e.g. `COM4`).
4. Set **Speed** to `115200`.
5. Press Enter to bring up the login prompt (`root` / `root`).

---

## 4. Starting the Control System

```bash
cd /home/root/v_space/deploy
sudo ./setup_zynq.sh
sudo ./run_cli.sh
```

If testing on developer laptop without physical board:
```powershell
python run_cli.py --mock
```

---

## 5. Strict Hardware Error Policy

If hardware mode is chosen (`--hw`), the software strictly mandates live physical AXI access:
- If `/dev/mem` cannot be opened or memory-mapped:
  ```text
  FATAL: ERROR: FPGA hardware interface unavailable.
  Failed to memory-map AXI address 0x43C00000.
  Check board connection and AXI peripheral mapping.
  ```
- The software **NEVER** silently falls back to a software mock when hardware mode was requested.
