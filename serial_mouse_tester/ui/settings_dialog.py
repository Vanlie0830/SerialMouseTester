"""
Settings Dialog

Serial port configuration dialog for protocol selection and communication parameters.
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QComboBox, QPushButton, QGroupBox, QSpinBox,
    QDialogButtonBox, QCheckBox,
)

from ..core.protocols import ProtocolType, PROTOCOL_CONFIGS
from ..core.serial_worker import list_serial_ports


class SerialSettingsDialog(QDialog):
    """Dialog for configuring serial port communication parameters."""

    def __init__(self, parent=None, current_settings: dict = None):
        super().__init__(parent)
        self.setWindowTitle("⚙ Serial Port Settings")
        self.setMinimumWidth(480)
        self._result_settings = {}
        self._current = current_settings or {}

        self.setStyleSheet("""
            QDialog {
                background-color: #1e1e2e;
                color: #cdd6f4;
            }
            QGroupBox {
                color: #cdd6f4;
                font-size: 12px;
                font-weight: bold;
                border: 1px solid #45475a;
                border-radius: 6px;
                margin-top: 8px;
                padding-top: 16px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 6px;
            }
            QComboBox, QSpinBox {
                background-color: #313244;
                color: #cdd6f4;
                border: 1px solid #45475a;
                border-radius: 4px;
                padding: 6px;
                font-size: 12px;
            }
            QComboBox:hover, QSpinBox:hover {
                border-color: #89b4fa;
            }
            QComboBox::drop-down {
                border: none;
                width: 24px;
            }
            QComboBox QAbstractItemView {
                background-color: #313244;
                color: #cdd6f4;
                selection-background-color: #585b70;
            }
            QLabel {
                color: #cdd6f4;
                font-size: 12px;
            }
            QCheckBox {
                color: #cdd6f4;
                font-size: 12px;
                spacing: 8px;
            }
            QPushButton {
                background-color: #89b4fa;
                color: #1e1e2e;
                border: none;
                border-radius: 6px;
                padding: 8px 20px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #74c7ec; }
            QPushButton:disabled {
                background-color: #45475a;
                color: #6c7086;
            }
        """)

        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        # ── Protocol Selection ──
        proto_group = QGroupBox("🎯 Protocol")
        proto_layout = QFormLayout(proto_group)

        self._cmb_protocol = QComboBox()
        self._cmb_protocol.addItem("🔍 Auto-Detect", ProtocolType.UNKNOWN)
        self._cmb_protocol.addItem("Microsoft 2-Button (1200, 7N1)", ProtocolType.MICROSOFT)
        self._cmb_protocol.addItem("Logitech 3-Button (1200, 7N1)", ProtocolType.LOGITECH)
        self._cmb_protocol.addItem("Mouse Systems 5-Byte (1200, 8N1)", ProtocolType.MOUSE_SYSTEMS)
        self._cmb_protocol.currentIndexChanged.connect(self._on_protocol_changed)
        proto_layout.addRow("Protocol:", self._cmb_protocol)

        self._lbl_proto_desc = QLabel("Auto-detect: Analyzes incoming byte patterns to identify the protocol.")
        self._lbl_proto_desc.setWordWrap(True)
        self._lbl_proto_desc.setStyleSheet("color: #a6adc8; font-size: 11px; font-style: italic;")
        proto_layout.addRow("", self._lbl_proto_desc)

        # ── Serial Port ──
        port_group = QGroupBox("🔌 Serial Port")
        port_layout = QFormLayout(port_group)

        self._cmb_port = QComboBox()
        self._refresh_ports()
        port_layout.addRow("Port:", self._cmb_port)

        self._btn_refresh = QPushButton("🔄 Refresh Ports")
        self._btn_refresh.setFixedWidth(140)
        self._btn_refresh.setStyleSheet("""
            QPushButton {
                background-color: #45475a;
                color: #cdd6f4;
                border: none;
                border-radius: 4px;
                padding: 6px;
                font-size: 11px;
            }
            QPushButton:hover { background-color: #585b70; }
        """)
        self._btn_refresh.clicked.connect(self._refresh_ports)
        port_layout.addRow("", self._btn_refresh)

        # ── Communication Parameters ──
        comm_group = QGroupBox("📡 Communication Parameters")
        comm_layout = QFormLayout(comm_group)

        self._cmb_baudrate = QComboBox()
        self._cmb_baudrate.addItems([
            "300", "600", "1200", "2400", "4800", "9600",
            "19200", "38400", "57600", "115200",
        ])
        self._cmb_baudrate.setCurrentText("1200")
        comm_layout.addRow("Baud Rate:", self._cmb_baudrate)

        self._cmb_bytesize = QComboBox()
        self._cmb_bytesize.addItems(["5", "6", "7", "8"])
        self._cmb_bytesize.setCurrentText("7")
        comm_layout.addRow("Data Bits:", self._cmb_bytesize)

        self._cmb_parity = QComboBox()
        self._cmb_parity.addItems(["None", "Even", "Odd", "Mark", "Space"])
        comm_layout.addRow("Parity:", self._cmb_parity)

        self._cmb_stopbits = QComboBox()
        self._cmb_stopbits.addItems(["1", "1.5", "2"])
        comm_layout.addRow("Stop Bits:", self._cmb_stopbits)

        # ── Options ──
        opts_group = QGroupBox("📋 Options")
        opts_layout = QVBoxLayout(opts_group)

        self._chk_auto_scroll = QCheckBox("Auto-scroll hex monitor")
        self._chk_auto_scroll.setChecked(True)
        self._chk_timestamps = QCheckBox("Show timestamps in hex monitor")
        self._chk_timestamps.setChecked(True)
        self._chk_parse_annotations = QCheckBox("Show parsed packet annotations")
        self._chk_parse_annotations.setChecked(True)

        opts_layout.addWidget(self._chk_auto_scroll)
        opts_layout.addWidget(self._chk_timestamps)
        opts_layout.addWidget(self._chk_parse_annotations)

        # ── Buttons ──
        btn_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btn_box.button(QDialogButtonBox.Ok).setText("✅ Apply")
        btn_box.button(QDialogButtonBox.Cancel).setText("❌ Cancel")
        btn_box.accepted.connect(self._on_accept)
        btn_box.rejected.connect(self.reject)

        layout.addWidget(proto_group)
        layout.addWidget(port_group)
        layout.addWidget(comm_group)
        layout.addWidget(opts_group)
        layout.addWidget(btn_box)

    def _refresh_ports(self):
        self._cmb_port.clear()
        ports = list_serial_ports()
        if ports:
            for p in ports:
                label = f"{p['device']} — {p['description']}"
                self._cmb_port.addItem(label, p["device"])
        else:
            self._cmb_port.addItem("No serial ports found", "")

    def _on_protocol_changed(self, index: int):
        protocol = self._cmb_protocol.currentData()
        if protocol in PROTOCOL_CONFIGS:
            cfg = PROTOCOL_CONFIGS[protocol]
            self._cmb_baudrate.setCurrentText(str(cfg.baudrate))
            self._cmb_bytesize.setCurrentText(str(cfg.bytesize))
            self._cmb_parity.setCurrentText(
                {"N": "None", "E": "Even", "O": "Odd", "M": "Mark", "S": "Space"}[cfg.parity]
            )
            self._cmb_stopbits.setCurrentText(str(cfg.stopbits))
            self._lbl_proto_desc.setText(
                f"Configuration: {cfg.baudrate} baud, "
                f"{cfg.bytesize}{cfg.parity}{cfg.stopbits}"
            )
        elif protocol == ProtocolType.UNKNOWN:
            self._lbl_proto_desc.setText(
                "Auto-detect: Analyzes incoming byte patterns to identify the protocol."
            )

    def _on_accept(self):
        self._result_settings = {
            "port": self._cmb_port.currentData() or "",
            "protocol": self._cmb_protocol.currentData(),
            "baudrate": int(self._cmb_baudrate.currentText()),
            "bytesize": int(self._cmb_bytesize.currentText()),
            "parity": {"None": "N", "Even": "E", "Odd": "O", "Mark": "M", "Space": "S"}[
                self._cmb_parity.currentText()
            ],
            "stopbits": float(self._cmb_stopbits.currentText()),
            "auto_scroll": self._chk_auto_scroll.isChecked(),
            "show_timestamps": self._chk_timestamps.isChecked(),
            "show_annotations": self._chk_parse_annotations.isChecked(),
        }
        self.accept()

    def get_settings(self) -> dict:
        return self._result_settings

    def set_current_settings(self, settings: dict):
        """Pre-populate dialog with current settings."""
        if settings.get("protocol") is not None:
            idx = self._cmb_protocol.findData(settings["protocol"])
            if idx >= 0:
                self._cmb_protocol.setCurrentIndex(idx)

        if "baudrate" in settings:
            self._cmb_baudrate.setCurrentText(str(settings["baudrate"]))
        if "bytesize" in settings:
            self._cmb_bytesize.setCurrentText(str(settings["bytesize"]))
        if "parity" in settings:
            parity_map = {"N": "None", "E": "Even", "O": "Odd", "M": "Mark", "S": "Space"}
            self._cmb_parity.setCurrentText(parity_map.get(settings["parity"], "None"))
        if "stopbits" in settings:
            self._cmb_stopbits.setCurrentText(str(settings["stopbits"]))
