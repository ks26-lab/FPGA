# EDGE ZYNQ Z7010 Deployment Guide

This guide details the exact steps to deploy and run the Universal Multi-Scene FPGA Control System on the **EDGE ZYNQ Z7010 SoC development board**.

---

## 1. Prerequisites

- **Board**: EDGE ZYNQ Z7010 SoC (Xilinx XC7Z010-1CLG400C)
- **Host PC**: Windows / Linux with Vivado 2020.2+ and PuTTY
- **Connection**: USB-UART micro-USB cable (for serial terminal) + JTAG / Ethernet / SD card
- **Operating System on Zynq PS**: Linux (Petalinux, Ubuntu ARM, or PYNQ Linux)

---

## 2. Step-by-Step Deployment Procedure

### Step 1: Program the FPGA Bitstream (Vivado)
1. Open Vivado on your host PC.
2. Open Hardware Manager and connect to the EDGE ZYNQ board via JTAG.
3. Program the PL bitstream:
   - For **Strategy A** (individual scene): Select the scene's bitstream (e.g. `underwater_probe_top.bit`, `maze_top.bit`, `mars_habitat_top.bit`, `solar_gimbal_top.bit`, `traffic_top.bit`).
   - For **Strategy B** (multi-scene simultaneous): Select `multi_scene_top.bit`.
4. Once programmed, **close or minimize Vivado**. Vivado is not part of the runtime loop.

### Step 2: Connect via PuTTY
1. Connect the micro-USB cable from the board's USB-UART port to the host PC.
2. In Windows Device Manager, identify the COM port (e.g. `COM5`).
3. Open **PuTTY**:
   - Connection Type: `Serial`
   - Serial line: `COM5` (or `/dev/ttyUSB0` on Linux)
   - Speed: `115200`
   - Data bits: `8`, Stop bits: `1`, Parity: `None`, Flow control: `None`
4. Click **Open** to access the Zynq Linux prompt.

### Step 3: Transfer Application Code to Zynq Linux
Copy the project folder to the board using `scp` or a micro-SD card:
```bash
# On Host PC (terminal / PowerShell):
scp -r c:/Users/karti/Desktop/HACK/V_SPACE root@192.168.1.10:/home/root/v_space
```

### Step 4: Verify Environment & Permissions
On the Zynq board terminal (inside PuTTY):
```bash
cd /home/root/v_space/deploy
sudo ./setup_zynq.sh
```

### Step 5: Start the Universal CLI
Run the launch script:
```bash
sudo ./run_cli.sh
```
You will see:
```text
========================================================
       ZYNQ Z7010 MULTI-SCENE FPGA CONTROL SYSTEM       
========================================================
FPGA STATUS : HARDWARE ACTIVE
TRANSPORT   : AXI
PROCESSOR   : ZYNQ ARM CORTEX-A9
MODE        : FPGA AUTHORITATIVE

Available Scenes:
  1. Solar Gimbal     (scene solar)
  2. Maze Runner      (scene maze)
  3. Mars Habitat     (scene mars)
  4. Underwater Probe (scene underwater)
  5. Traffic          (scene traffic)

Type 'help' for commands.
========================================================
FPGA> 
```

### Step 6: Select Scene & Control the FPGA
```text
FPGA> scene underwater
[SCENE] Underwater Dynamic Probe
[FPGA] Peripheral selected at 0x43C00000 (HARDWARE ACTIVE)

FPGA[underwater]> set depth 40
[FPGA] Depth configuration set to 40.0 m

FPGA[underwater]> target 80
[FPGA] Target depth set to 80.0 m

FPGA[underwater]> current +20
[FPGA] Water current set to +20%

FPGA[underwater]> start
[FPGA] Probe movement started

FPGA[underwater]> status
[Renders live 3-panel status readout directly from FPGA PL registers]
```

---

## 3. Offline / Host PC Development Mode

When developing without the board connected:
```bash
python run_cli.py --mock
```
In mock mode, the CLI clearly tags all telemetry with `[MOCK MODE]`. Hardware mode (`--hw`) will refuse to run on non-Linux hosts and never silently fall back.
