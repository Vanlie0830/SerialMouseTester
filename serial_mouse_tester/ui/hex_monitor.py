"""
Hex Monitor Widget

Displays raw serial data as a scrolling hex dump with packet highlighting.
"""

import time
from collections import deque
from datetime import datetime

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QColor, QTextCharFormat, QTextCursor
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPlainTextEdit, QPushButton, QCheckBox, QGroupBox,
)

MAX_LINES = 2000  # Maximum lines to keep in the display


class HexMonitor(QPlainTextEdit):
    """A hex dump display widget with color-coded packet highlighting."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setMaximumBlockCount(MAX_LINES)

        # Monospace font for hex display
        font = QFont("Consolas", 10)
        font.setStyleHint(QFont.Monospace)
        self.setFont(font)

        # Styling
        self.setStyleSheet("""
            QPlainTextEdit {
                background-color: #1e1e2e;
                color: #cdd6f4;
                border: 1px solid #45475a;
                border-radius: 6px;
                padding: 8px;
                selection-background-color: #585b70;
            }
        """)

        self._packet_count = 0
        self._byte_count = 0

    def append_raw_data(self, data: bytes, protocol_hint: str = ""):
        """Append raw bytes as a formatted hex dump line."""
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        hex_str = " ".join(f"{b:02X}" for b in data)
        ascii_str = "".join(chr(b) if 32 <= b < 127 else "." for b in data)

        self._byte_count += len(data)
        self._packet_count += 1

        # Format: [timestamp] HEX... | ASCII
        line = f"[{timestamp}] {hex_str:<60s} | {ascii_str}"

        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.End)

        # Color coding based on data length
        fmt = QTextCharFormat()
        if len(data) == 3:
            fmt.setForeground(QColor("#a6e3a1"))  # Green for Microsoft 3-byte
        elif len(data) == 4:
            fmt.setForeground(QColor("#89b4fa"))  # Blue for Logitech 4-byte
        elif len(data) == 5:
            fmt.setForeground(QColor("#f9e2af"))  # Yellow for Mouse Systems 5-byte
        else:
            fmt.setForeground(QColor("#6c7086"))  # Gray for other

        cursor.insertText(line + "\n", fmt)
        self.setTextCursor(cursor)
        self.ensureCursorVisible()

    def append_parsed_line(self, text: str, color: str = "#cdd6f4"):
        """Append a parsed/annotation line with custom color."""
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.End)

        fmt = QTextCharFormat()
        fmt.setForeground(QColor(color))
        cursor.insertText(f"  └─ [{timestamp}] {text}\n", fmt)
        self.setTextCursor(cursor)
        self.ensureCursorVisible()

    def clear_display(self):
        """Clear all displayed data."""
        self.clear()
        self._packet_count = 0
        self._byte_count = 0

    @property
    def stats(self) -> dict:
        return {
            "packets": self._packet_count,
            "bytes": self._byte_count,
        }


class HexMonitorPanel(QWidget):
    """Full hex monitor panel with controls and statistics."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._auto_scroll = True

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        # Header with stats and controls
        header = QHBoxLayout()

        self._lbl_title = QLabel("📊 Hex Monitor")
        self._lbl_title.setStyleSheet("""
            QLabel {
                font-size: 14px;
                font-weight: bold;
                color: #cdd6f4;
                padding: 4px;
            }
        """)

        self._lbl_stats = QLabel("Packets: 0 | Bytes: 0")
        self._lbl_stats.setStyleSheet("color: #a6adc8; font-size: 11px;")

        self._chk_auto_scroll = QCheckBox("Auto-scroll")
        self._chk_auto_scroll.setChecked(True)
        self._chk_auto_scroll.setStyleSheet("color: #a6adc8; font-size: 11px;")
        self._chk_auto_scroll.toggled.connect(self._toggle_auto_scroll)

        self._btn_clear = QPushButton("🗑 Clear")
        self._btn_clear.setStyleSheet("""
            QPushButton {
                background-color: #45475a;
                color: #cdd6f4;
                border: none;
                border-radius: 4px;
                padding: 4px 12px;
                font-size: 11px;
            }
            QPushButton:hover { background-color: #585b70; }
        """)
        self._btn_clear.clicked.connect(self.clear_all)

        header.addWidget(self._lbl_title)
        header.addStretch()
        header.addWidget(self._lbl_stats)
        header.addWidget(self._chk_auto_scroll)
        header.addWidget(self._btn_clear)

        # Hex display
        self._hex_display = HexMonitor()

        layout.addLayout(header)
        layout.addWidget(self._hex_display)

    def append_raw_data(self, data: bytes, protocol_hint: str = ""):
        """Add raw data to the display."""
        self._hex_display.append_raw_data(data, protocol_hint)
        self._update_stats()

    def append_parsed_line(self, text: str, color: str = "#cdd6f4"):
        """Add parsed data line to the display."""
        self._hex_display.append_parsed_line(text, color)

    def clear_all(self):
        """Clear the display and reset statistics."""
        self._hex_display.clear_display()
        self._update_stats()

    def _update_stats(self):
        stats = self._hex_display.stats
        self._lbl_stats.setText(
            f"Packets: {stats['packets']:,} | Bytes: {stats['bytes']:,}"
        )

    def _toggle_auto_scroll(self, checked: bool):
        self._auto_scroll = checked
