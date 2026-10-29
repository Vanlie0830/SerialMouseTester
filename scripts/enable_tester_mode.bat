@echo off
REM ============================================================
REM  Serial Mouse Tester - Enable Tester Mode
REM  Disables Windows built-in Serial Mouse driver
REM  so SerialMouseTester.exe can access COM4
REM ============================================================
echo.
echo ========================================
echo  Enable SerialMouseTester Mode
echo ========================================
echo.
echo This will DISABLE Windows Microsoft Serial Mouse driver.
echo Your serial mouse will only work in SerialMouseTester.
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

echo [1/2] Disabling Microsoft Serial Mouse driver...
powershell -Command "Disable-PnpDevice -InstanceId 'SERENUM\MOUSE\7&1EFE3534&0&0000' -Confirm:$false" 2>nul
if %errorlevel% equ 0 (
    echo       OK - Windows Serial Mouse driver disabled
) else (
    echo       Trying alternative method...
    powershell -Command "Get-PnpDevice -InstanceId 'SERENUM\MOUSE\7&1EFE3534&0&0000' | Disable-PnpDevice -Confirm:$false" 2>nul
    echo       Done
)

echo.
echo [2/2] Waiting 2 seconds for COM4 to be released...
timeout /t 2 /nobreak >nul

echo.
echo ========================================
echo  DONE! COM4 is now available.
echo  You can now run SerialMouseTester.exe
echo ========================================
echo.
pause
