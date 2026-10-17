@echo off
setlocal enabledelayedexpansion

echo =====================================================================
echo  V_SPACE FPGA - ZYNQ Z7010 MULTI-SCENE VIVADO BUILD AUTOMATION
echo =====================================================================
echo Target Part : XC7Z010-1CLG400C (EDGE ZYNQ Z7010)
echo System Top  : system_wrapper (Zynq PS7 + 5-Scene AXI Subsystems)
echo.

:: 1. Search for Vivado on PATH
where vivado >nul 2>nul
if %ERRORLEVEL% equ 0 (
    set "VIVADO_CMD=vivado"
    goto :FOUND_VIVADO
)

:: 2. Search common Xilinx Windows Installation paths
set "XILINX_ROOTS=C:\Xilinx\Vivado D:\Xilinx\Vivado E:\Xilinx\Vivado"
for %%R in (%XILINX_ROOTS%) do (
    if exist "%%R" (
        for /f "delims=" %%V in ('dir /b /ad "%%R\20*" 2^>nul') do (
            if exist "%%R\%%V\bin\vivado.bat" (
                set "VIVADO_CMD=%%R\%%V\bin\vivado.bat"
                goto :FOUND_VIVADO
            )
        )
    )
)

echo [ERROR] Vivado not found in PATH or standard C:\Xilinx\Vivado directories.
echo Please run this script from a "Vivado Command Prompt" or add Vivado bin to PATH.
echo Example:
echo   call "C:\Xilinx\Vivado\2022.2\settings64.bat"
echo   run_vivado_build.bat
echo.
pause
exit /b 1

:FOUND_VIVADO
echo [INFO] Found Vivado executable: %VIVADO_CMD%
echo.
echo Select Build Mode:
echo   [1] Full Build: Project + Zynq PS BD + Synthesis + Implementation + Bitstream (Default)
echo   [2] Project Setup Only (Create project & Block Design for GUI inspection)
echo   [3] Fast Non-Project Synthesis Check
echo.
set /p BUILD_CHOICE="Enter selection [1-3, default 1]: "

if "%BUILD_CHOICE%"=="2" (
    set "AUTO_RUN=0"
    echo [INFO] Running Project Setup Only...
    call "%VIVADO_CMD%" -mode batch -source build_vivado_project.tcl
) else if "%BUILD_CHOICE%"=="3" (
    echo [INFO] Running Fast RTL Synthesis Check...
    call "%VIVADO_CMD%" -mode batch -source run_synth_fast.tcl
) else (
    set "AUTO_RUN=1"
    echo [INFO] Starting Full Build (Synthesis + Implementation + Bitstream)...
    call "%VIVADO_CMD%" -mode batch -source build_vivado_project.tcl
)

echo.
echo =====================================================================
echo  Build script execution completed.
echo =====================================================================
pause
