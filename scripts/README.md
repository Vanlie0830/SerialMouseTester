# 🔧 Mode Switching Scripts

The Windows built-in **Microsoft Serial Mouse** driver automatically claims COM4 when a serial mouse is detected. This prevents SerialMouseTester.exe from accessing the port.

Use these scripts (run as **Administrator**) to switch between modes:

## Scripts

| Script | Function |
|--------|----------|
| `enable_tester_mode.bat` | Disable Windows driver → COM4 free for SerialMouseTester |
| `restore_windows_mode.bat` | Enable Windows driver → mouse works normally in Windows |
| `toggle_mode.bat` | Interactive toggle (detects current mode, switch with A/B) |

## Quick Start

1. **Right-click** `enable_tester_mode.bat` → **Run as administrator**
2. Run `SerialMouseTester.exe`
3. Connect to COM4 and test your serial mouse!
4. When done, **right-click** `restore_windows_mode.bat` → **Run as administrator**

## Why This Happens

Windows automatically detects serial mice (Microsoft Serial Mouse protocol) and loads its built-in driver (`SERENUM\MOUSE\`). This driver takes exclusive access to COM4, blocking other applications.

```
Before:  Windows Serial Mouse Driver → COM4 → Serial Mouse
After:   SerialMouseTester.exe → COM4 → Serial Mouse
```

## Troubleshooting

- **"Access Denied" in SerialMouseTester** → Run `enable_tester_mode.bat` first
- **Mouse doesn't work in Windows** → Run `restore_windows_mode.bat`
- **Scripts fail** → Make sure to run as Administrator (right-click → Run as admin)
