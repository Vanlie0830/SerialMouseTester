"""
Sidebar Navigation Widget (VVT-style panel navigation)

Left sidebar with navigation buttons and card-based status display.
Events are dispatched through a centralized signal registry.
"""

from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QFont, QIcon
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QGridLayout, QSizePolicy,
)

from .theme import Palette, Fonts, SIDEBAR_QSS, CARD_QSS


class NavButton(QPushButton):
    """Navigation button with icon + label."""
    def __init__(self, icon_text: str, label: str, panel_id: str, parent=None):
        super().__init__(f"  {icon_text}  {label}", parent)
        self.panel_id = panel_id
        self.setProperty("nav", "true")
        self.setProperty("active", "false")
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedHeight(44)


class StatusCard(QFrame):
    """Card-style status display (icon + label + value + subtitle)."""
    def __init__(self, icon: str, title: str, parent=None):
        super().__init__(parent)
        self.setProperty("card", "true")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(2)

        # Title row (icon + label)
        title_row = QHBoxLayout()
        icon_lbl = QLabel(icon)
        icon_lbl.setFont(QFont(Fonts.UI, 14))
        title_lbl = QLabel(title)
        title_lbl.setProperty("card-title", "true")
        title_row.addWidget(icon_lbl)
        title_row.addWidget(title_lbl)
        title_row.addStretch()

        # Value
        self._value_lbl = QLabel("—")
        self._value_lbl.setProperty("card-value", "true")

        # Subtitle
        self._sub_lbl = QLabel("")
        self._sub_lbl.setProperty("card-sub", "true")

        layout.addLayout(title_row)
        layout.addWidget(self._value_lbl)
        layout.addWidget(self._sub_lbl)

    def set_value(self, value: str, color: str = None):
        self._value_lbl.setText(value)
        if color:
            self._value_lbl.setStyleSheet(f"color: {color}; font-size: 24px; font-weight: bold;")

    def set_subtitle(self, text: str):
        self._sub_lbl.setText(text)


class Sidebar(QWidget):
    """
    Left sidebar with navigation and status cards.

    Signals:
        navigate(str): Emitted when a nav button is clicked with panel_id
    """

    navigate = Signal(str)  # panel_id

    # Panel definitions: (icon, label, panel_id)
    PANELS = [
        ("📊", "Hex Monitor", "hex"),
        ("🖱", "Mouse View", "mouse"),
        ("💾", "Data Log", "log"),
        ("⚙", "Settings", "settings"),
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("Sidebar")
        self.setStyleSheet(SIDEBAR_QSS + CARD_QSS)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 12, 8, 12)
        layout.setSpacing(4)

        # ── App Title ──
        title = QLabel("🖱 Serial Mouse Tester")
        title.setFont(QFont(Fonts.UI, 13, QFont.Bold))
        title.setStyleSheet(f"color: {Palette.TEXT}; padding: 8px;")
        title.setWordWrap(True)

        subtitle = QLabel("v00.00.2b")
        subtitle.setFont(QFont(Fonts.UI, 9))
        subtitle.setStyleSheet(f"color: {Palette.OVERLAY0}; padding: 0 8px 8px 8px;")

        layout.addWidget(title)
        layout.addWidget(subtitle)

        # Separator
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet(f"color: {Palette.SURFACE0}; max-height: 1px;")
        layout.addWidget(sep)

        # ── Navigation Buttons ──
        self._nav_buttons: dict[str, NavButton] = {}
        for icon, label, panel_id in self.PANELS:
            btn = NavButton(icon, label, panel_id)
            btn.clicked.connect(lambda checked, pid=panel_id: self._on_nav_click(pid))
            self._nav_buttons[panel_id] = btn
            layout.addWidget(btn)

        layout.addStretch()

        # ── Status Cards ──
        sep2 = QFrame()
        sep2.setFrameShape(QFrame.HLine)
        sep2.setStyleSheet(f"color: {Palette.SURFACE0}; max-height: 1px;")
        layout.addWidget(sep2)

        cards_title = QLabel("  STATUS")
        cards_title.setFont(QFont(Fonts.UI, 9, QFont.Bold))
        cards_title.setStyleSheet(f"color: {Palette.OVERLAY0}; padding: 4px;")
        layout.addWidget(cards_title)

        self._card_conn = StatusCard("🔌", "Connection", self)
        self._card_conn.set_value("Offline", Palette.RED)
        self._card_conn.set_subtitle("No port connected")
        layout.addWidget(self._card_conn)

        self._card_proto = StatusCard("📡", "Protocol", self)
        self._card_proto.set_value("—", Palette.SUBTEXT0)
        self._card_proto.set_subtitle("Auto-detect mode")
        layout.addWidget(self._card_proto)

        self._card_packets = StatusCard("📦", "Packets", self)
        self._card_packets.set_value("0", Palette.BLUE)
        self._card_packets.set_subtitle("0 bytes received")
        layout.addWidget(self._card_packets)

    def _on_nav_click(self, panel_id: str):
        """Handle navigation button click and update active state."""
        for pid, btn in self._nav_buttons.items():
            btn.setProperty("active", str(pid == panel_id).lower())
            btn.style().unpolish(btn)
            btn.style().polish(btn)
        self.navigate.emit(panel_id)

    def set_active_panel(self, panel_id: str):
        """Programmatically set the active panel."""
        self._on_nav_click(panel_id)

    # ── Status Card Updates ──

    def update_connection(self, connected: bool, detail: str = ""):
        if connected:
            self._card_conn.set_value("Online", Palette.GREEN)
        else:
            self._card_conn.set_value("Offline", Palette.RED)
        self._card_conn.set_subtitle(detail)

    def update_protocol(self, protocol_name: str, detail: str = ""):
        self._card_proto.set_value(protocol_name, Palette.MAUVE)
        self._card_proto.set_subtitle(detail)

    def update_packets(self, count: int, byte_count: int):
        self._card_packets.set_value(f"{count:,}", Palette.BLUE)
        self._card_packets.set_subtitle(f"{byte_count:,} bytes received")
