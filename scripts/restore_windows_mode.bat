@echo off
REM ============================================================
REM  Serial Mouse Tester - Restore Windows Mode
REM  Re-enables Windows built-in Serial Mouse driver
REM  so the serial mouse works normally in Windows
REM ============================================================
echo.
echo ========================================
echo  Restore Windows Serial Mouse Mode
echo ========================================
echo.
echo This will RE-ENABLE Windows Microsoft Serial Mouse driver.
echo Your serial mouse will work normally in Windows.
echo.

REM Check admin privileges
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Please run this script as Administrator!
    echo Right-click the file and select "Run as administrator"
    echo.
    pause
    exit /b 1
)

echo [1/1] Enabling Microsoft Serial Mouse driver...
powershell -Command "Enable-PnpDevice -InstanceId 'SERENUM\MOUSE\7&1EFE3534&0&0000' -Confirm:$false" 2>nul
if %errorlevel% equ 0 (
    echo       OK - Windows Serial Mouse driver enabled
) else (
    echo       Trying alternative method...
    powershell -Command "Get-PnpDevice -InstanceId 'SERENUM\MOUSE\7&1EFE3534&0&0000' | Enable-PnpDevice -Confirm:$false" 2>nul
    echo       Done
)

echo.
echo ========================================
echo  DONE! Serial mouse restored for Windows.
echo ========================================
echo.
pause
