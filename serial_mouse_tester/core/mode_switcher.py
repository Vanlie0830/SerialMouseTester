"""
Mode Switcher Module

Handles switching between Tester Mode and Windows Mode
by enabling/disabling the Windows Microsoft Serial Mouse driver.

Requires administrator privileges - uses UAC elevation on demand.
"""

import subprocess
import sys
import ctypes

# The Windows Serial Mouse PnP device instance ID
SERIAL_MOUSE_DEVICE = "SERENUM\\MOUSE\\7&1EFE3534&0&0000"

# PowerShell commands
PS_GET_STATUS = (
    f"Get-PnpDevice -InstanceId '{SERIAL_MOUSE_DEVICE}' "
    f"-ErrorAction SilentlyContinue | Select-Object -ExpandProperty Status"
)
PS_DISABLE = (
    f"Disable-PnpDevice -InstanceId '{SERIAL_MOUSE_DEVICE}' -Confirm:$false"
)
PS_ENABLE = (
    f"Enable-PnpDevice -InstanceId '{SERIAL_MOUSE_DEVICE}' -Confirm:$false"
)


def is_admin() -> bool:
    """Check if current process has administrator privileges."""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception:
        return False


def get_driver_status() -> str:
    """
    Get the current status of the Microsoft Serial Mouse driver.
    Returns: 'OK' (active), 'Error' (disabled), 'Unknown' (not found), or error message.
    """
    try:
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command", PS_GET_STATUS],
            capture_output=True, text=True, timeout=10,
        )
        status = result.stdout.strip()
        return status if status else "Unknown"
    except Exception as e:
        return f"Error: {e}"


def run_elevated_powershell(command: str) -> tuple[bool, str]:
    """
    Run a PowerShell command with UAC elevation (shows UAC prompt).
    
    Uses ShellExecuteW with 'runas' verb to trigger the UAC dialog.
    Returns (success, message).
    """
    try:
        # ShellExecuteW with 'runas' = request elevation (UAC prompt)
        ret = ctypes.windll.shell32.ShellExecuteW(
            None,       # hwnd
            "runas",    # verb = run as administrator
            "powershell.exe",
            f'-NoProfile -Command "{command}"',
            None,       # directory
            0,          # SW_HIDE
        )

        if ret > 32:
            return True, "Command sent with elevation (confirm UAC if prompted)"
        else:
            return False, f"ShellExecute failed (error code: {ret})"
    except Exception as e:
        return False, f"Error: {e}"


def enable_tester_mode() -> tuple[bool, str]:
    """Disable Windows Serial Mouse driver to free COM port for testing."""
    return run_elevated_powershell(PS_DISABLE)


def restore_windows_mode() -> tuple[bool, str]:
    """Enable Windows Serial Mouse driver for normal mouse use."""
    return run_elevated_powershell(PS_ENABLE)
