# Changelog

All notable changes to Serial Mouse Tester will be documented in this file.

Format: `v{major:02d}.{minor:02d}.{patch:d}{letter}`
- Patch number increments for feature additions
- Letter increments for bug fixes and minor improvements
- Minor version increments for significant milestones

## [v00.00.2b] - 2026-03-10

### Added (RS-232 Expert patterns)
- 📡 **Display merging**: 30ms quiet-period grouping (serial streams have no message boundaries)
- 🛡 **Timer/flag safety**: unconditionally kill old timers on disconnect (no zombie state)
- 📊 **Phase timing instrumentation**: parse latency + RX byte count shown in status bar
- 🚫 **No-flush policy**: documented and enforced (WriteFile success = driver owns it)
- 🔍 **Evidence-based error logging**: non-fatal close errors logged with actual message

## [v00.00.2a] - 2026-03-10

### Added (VVT-style refactoring)
- 🎨 **Centralized theme module** (`theme.py`) - Catppuccin Mocha palette as single source of truth
- 📱 **Sidebar navigation** with panel switching (Hex / Mouse / Log / Settings)
- 📊 **Card-based status display** in sidebar (Connection / Protocol / Packets)
- 🔌 **SignalRegistry** - centralized event dispatch (no lambda sea)
- ⚙ **Settings panel** with inline quick actions
- 🛡 **Evidence-based error handling** - errors show actual evidence, not guesses

### Changed
- 🏗 UI refactored: QSplitter layout → Sidebar + QStackedWidget panels
- 🎨 All QSS styles centralized in theme.py (change theme in ONE place)
- 📡 Serial events routed through SignalRegistry

## [v00.00.1c] - 2026-03-10

### Fixed
- 🐛 **Window maximize crash** - `QColor(str, int)` invalid constructor in MouseCanvas glow effect
- 🛡 **Global exception handler** - unhandled errors show dialog instead of crashing
- 🛡 **paintEvent protection** - painting errors are caught and logged, never crash

## [v00.00.1b] - 2026-03-10

### Added
- 📦 **Windows EXE packaging** via PyInstaller (single-file, no console, 45.3 MB)
- 🔧 **PyInstaller spec file** for reproducible builds
- 🗜 UPX compression enabled

## [v00.00.1a] - 2026-03-10

### Added
- 🎯 **Protocol auto-detection** for Microsoft, Logitech, and Mouse Systems serial mice
- 📊 **Hex Monitor** with real-time raw data display and color-coded packets
- 🖱 **Mouse Trajectory Visualizer** with live movement trail and button indicators
- ⚙ **Serial Port Configuration** dialog (COM port, baud rate, data bits, parity, stop bits)
- 💾 **Data Recording & CSV Export** with timestamp, deltas, cumulative position
- 🎨 **Modern Dark Theme** (Catppuccin Mocha inspired)
- 📡 **Status Bar** with connection state, protocol, packet count, byte count, elapsed time
- 🧪 **Protocol Parser Tests** for Microsoft and Mouse Systems
- 📁 **Project Structure** with core/ui separation
- 📖 **Help** menu with About dialog and Protocol Reference
- ⌨ **Keyboard Shortcuts** (Ctrl+Shift+C/D for connect/disconnect, Ctrl+E for export)

### Technical Details
- Python 3.9+ / PySide6 (Qt6) / pyserial
- Threaded serial reading with Qt signals
- Protocol parsers: Microsoft (3-byte), Logitech (3/4-byte), Mouse Systems (5-byte)
- Auto-detection uses byte-pattern scoring (bit 7/6 analysis)
