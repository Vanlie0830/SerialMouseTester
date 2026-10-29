@echo off
REM ============================================================
REM  Serial Mouse Tester - Quick Mode Toggle
REM  Detects current mode and switches automatically
REM ============================================================
echo.
echo ========================================
echo  Serial Mouse - Quick Mode Toggle
echo ========================================
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

REM Check current state
echo Checking current mode...
powershell -Command "$d = Get-PnpDevice -InstanceId 'SERENUM\MOUSE\7&1EFE3534&0&0000' -ErrorAction SilentlyContinue; if ($d.Status -eq 'OK') { Write-Host 'MODE: Windows (driver active)' } else { Write-Host 'MODE: Tester (driver disabled)' }"

echo.
echo [A] Switch to Tester Mode (for SerialMouseTester.exe)
echo [B] Switch to Windows Mode (normal mouse use)
echo [Q] Quit
echo.
choice /C ABQ /N /M "Select an option: "

if %errorlevel%==1 goto tester
if %errorlevel%==2 goto windows
if %errorlevel%==3 goto quit

:tester
echo.
echo Disabling Windows Serial Mouse driver...
powershell -Command "Disable-PnpDevice -InstanceId 'SERENUM\MOUSE\7&1EFE3534&0&0000' -Confirm:$false" 2>nul
echo DONE! COM4 is available for SerialMouseTester.exe
goto end

:windows
echo.
echo Enabling Windows Serial Mouse driver...
powershell -Command "Enable-PnpDevice -InstanceId 'SERENUM\MOUSE\7&1EFE3534&0&0000' -Confirm:$false" 2>nul
echo DONE! Serial mouse restored for Windows
goto end

:quit
exit /b 0

:end
echo.
pause
