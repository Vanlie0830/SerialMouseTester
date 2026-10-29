# 🖱 Serial Mouse Tester

**Version: v00.00.1a** | A modern serial mouse testing and analysis tool.

A professional-grade GUI application for testing and analyzing classic serial mice (老古董串列滑鼠). Built with Python + PySide6 (Qt).

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🔍 **Protocol Auto-Detection** | Automatically identifies Microsoft, Logitech, or Mouse Systems protocols |
| 📊 **Hex Monitor** | Real-time raw data display with color-coded packet highlighting |
| 🖱 **Mouse Trajectory Visualizer** | Live movement trail rendering with button state indicators |
| ⚙ **Serial Configuration** | COM port selection, baud rate, data bits, parity, stop bits |
| 💾 **Data Recording** | CSV export with timestamp, deltas, cumulative position, button states |
| 🎨 **Modern Dark UI** | Catppuccin Mocha theme with smooth interactions |

## 📡 Supported Protocols

| Protocol | Baud Rate | Config | Packet Size | Buttons |
|----------|-----------|--------|-------------|---------|
| **Microsoft 2-Button** | 1200 | 7N1 | 3 bytes | Left, Right |
| **Logitech 3-Button** | 1200 | 7N1 | 3-4 bytes | Left, Middle, Right |
| **Mouse Systems** | 1200 | 8N1 | 5 bytes | Left, Middle, Right |

### Microsoft Protocol (3-byte)
```
Byte 0: 01LRYYXX  (sync=01, L/R buttons, high bits of Y/X delta)
Byte 1: 00XXXXXX  (low 6 bits of X delta)
Byte 2: 00YYYYYY  (low 6 bits of Y delta)
```

### Mouse Systems Protocol (5-byte)
```
Byte 0: 1000MRL?  (sync=1, middle/right/left buttons, active LOW)
Byte 1: X delta   (signed 8-bit)
Byte 2: Y delta   (signed 8-bit, inverted)
Byte 3: X extension
Byte 4: Y extension
```

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- pip

### Installation
```bash
# Clone the repository
git clone https://github.com/Vanlie0830/SerialMouseTester.git
cd SerialMouseTester

# Install dependencies
pip install -r requirements.txt

# Run the application
python run.py
```

### Usage
1. **Connect** a serial mouse to your computer (via USB-to-Serial adapter if needed)
2. **Select** the COM port from the toolbar
3. **Choose** protocol (or leave as Auto-Detect)
4. **Click** Connect
5. **Watch** the mouse data appear in real-time!

## 🛠 Development

### Project Structure
```
SerialMouseTester/
├── serial_mouse_tester/
│   ├── __init__.py           # Package init + version
│   ├── core/
│   │   ├── protocols.py      # Protocol parsing & auto-detection
│   │   ├── serial_worker.py  # Serial port reading thread
│   │   └── logger.py         # CSV/data recording
│   └── ui/
│       ├── main_window.py    # Main application window
│       ├── hex_monitor.py    # Raw data hex display
│       ├── mouse_canvas.py   # Movement visualization
│       ├── log_panel.py      # Recording & export panel
│       └── settings_dialog.py # Configuration dialog
├── tests/
│   └── test_protocols.py     # Protocol parser tests
├── run.py                    # Entry point
├── requirements.txt          # Python dependencies
├── VERSION                   # Version file
├── CHANGELOG.md              # Version history
└── README.md                 # This file
```

### Running Tests
```bash
python tests/test_protocols.py
```

## 📋 Version History

| Version | Date | Changes |
|---------|------|---------|
| v00.00.1a | 2026-03-10 | Initial release: 3 protocols, auto-detect, dark UI, CSV export |

## 📄 License

MIT License - See LICENSE file for details.

---

**Built with ❤️ by Bear Brother & Hui Bao**
