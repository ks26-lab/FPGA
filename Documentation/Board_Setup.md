# AMD EDGE Zynq Z7010 Board Setup & Hardware Execution Guide

This document provides the hardware preparation, cable connection, kernel configuration, and serial terminal setup procedures for running the FPGA control system on the **AMD EDGE Zynq Z7010 SoC development board**.

---

## 1. Hardware Specifications

- **Development Board:** EDGE ZYNQ Z7010 SoC
- **FPGA Part Number:** Xilinx / AMD Zynq-7000 XC7Z010-1CLG400C
- **Processing System (PS):** Dual-Core ARM Cortex-A9 MPCore @ up to 667 MHz
- **Programmable Logic (PL):** 28,000 Logic Cells (~17,600 LUTs, 35,200 FFs, 60 BRAM 18Kb tiles, 80 DSP48E1 slices)
- **On-Board Memory:** 512 MB DDR3 SDRAM
- **Interfaces:** Micro-USB UART (Serial), Micro-USB JTAG (Programming), Micro-SD Slot, 10/100/1000 Ethernet, User LEDs, Pushbuttons, DIP switches

---

## 2. Physical Connections

```text
  ┌─────────────────────────────────────────────────────────────┐
  │                 EDGE ZYNQ Z7010 BOARD                       │
  │                                                             │
  │  [ Micro-USB JTAG ] ──────── USB Cable ────> Host PC (Vivado)
  │                                                             │
  │  [ Micro-USB UART ] ──────── USB Cable ────> Host PC (PuTTY) │
  │                                                             │
  │  [ Micro-SD Card  ] <─────── Boot Image (Linux + boot.bin)  │
  │                                                             │
  │  [ 5V DC Power    ] <─────── 5V 2A Power Adapter / USB      │
  └─────────────────────────────────────────────────────────────┘
```

1. **JTAG Port:** Connect a micro-USB cable from the JTAG port to the Host PC for Vivado Hardware Manager bitstream loading.
2. **UART Port:** Connect a micro-USB cable from the USB-UART port to the Host PC for serial console communication.
3. **Power:** Ensure power jumper is set to USB or external 5V barrel jack as appropriate. Power switch ON.
4. **Status LEDs:** Verify the Power LED (typically RED) is illuminated.

---

## 3. Host Serial Terminal Configuration (PuTTY)

1. Connect the USB-UART cable to the Host PC.
2. Open Windows **Device Manager** -> **Ports (COM & LPT)** to identify the COM port (e.g., `COM4` or `COM5`). On Linux, inspect `/dev/ttyUSB0` or `/dev/ttyACM0`.
3. Launch **PuTTY** and configure:
   - **Connection Type:** `Serial`
   - **Serial line:** `COM4` (adjust to match your detected port)
   - **Speed (Baud rate):** `115200`
   - **Data bits:** `8`
   - **Stop bits:** `1`
   - **Parity:** `None`
   - **Flow control:** `None`
4. Click **Open** to access the Zynq Linux console. Press `Enter` to display the login prompt.
5. Default login: `root` (password: `root` or empty depending on Linux distribution).

---

## 4. Zynq Embedded Linux Environment & Kernel Requirements

The ARM Processing System (PS) runs embedded Linux (PetaLinux 2020.2+, Ubuntu ARM rootfs, or PYNQ Linux).

### Mandatory Kernel Drivers:
To communicate with PL peripherals across the AXI interconnect:
1. **`/dev/mem` Driver:** Must be enabled in the kernel (`CONFIG_DEVMEM=y`).
2. **Strict Devmem Relaxed:** Kernel must allow mapping physical address aperture `0x40000000` to `0x4FFFFFFF`. If strict devmem is enabled, append `iomem=relaxed` to U-Boot bootargs:
   ```text
   setenv bootargs 'console=ttyPS0,115200 root=/dev/mmcblk0p2 rw earlyprintk iomem=relaxed'
   ```

---

## 5. FPGA Bitstream Programming Methods

### Method A: JTAG via Vivado Hardware Manager (Recommended for Development)
1. Launch Vivado on the Host PC.
2. Click **Open Hardware Manager** -> **Open Target** -> **Auto Connect**.
3. Select `xc7z010_1`.
4. Click **Program Device**, browse to the generated bitstream:
   - Strategy A (Individual Scene): `Experiments/Experiment_0X/RTL/<scene>_top.bit`
   - Strategy B (Multi-Scene Unified): `scripts/multi_scene_top.bit`
5. Click **Program**.
6. Verify the green **DONE** LED illuminates on the EDGE ZYNQ board.
7. **Close or minimize Vivado.** Vivado is not needed during runtime.

### Method B: Micro-SD Boot (`boot.bin`)
1. In Vitis / Vivado Bootgen, bundle `FSBL.elf`, `multi_scene_top.bit`, and `u-boot.elf` into `boot.bin`.
2. Copy `boot.bin` and the Linux kernel (`image.ub` or `uImage`) to the FAT32 boot partition of the micro-SD card.
3. Set board boot mode jumpers to **SD Boot**. Power cycle the board.

### Method C: Linux FPGA Manager (Runtime Reconfiguration)
On the Zynq Linux terminal:
```bash
echo 0 > /sys/class/fpga_manager/fpga0/flags
cp multi_scene_top.bit.bin /lib/firmware/
echo multi_scene_top.bit.bin > /sys/class/fpga_manager/fpga0/firmware
```

---

## 6. Application Deployment & Execution

1. Copy the project repository to the Zynq Linux filesystem:
   ```bash
   scp -r V_SPACE root@<board-ip>:/home/root/v_space
   ```
2. Navigate to the deployment directory and configure execution permissions:
   ```bash
   cd /home/root/v_space/scripts
   chmod +x setup_zynq.sh run_cli.sh
   sudo ./setup_zynq.sh
   ```
3. Start the universal control system:
   ```bash
   sudo ./run_cli.sh
   ```
   Or launch directly via Python:
   ```bash
   sudo python3 main.py --hw
   ```

4. If testing on a laptop without physical hardware attached, use the bit-accurate emulator:
   ```bash
   python main.py --mock
   ```
