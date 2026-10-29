"""
Main Window

The primary application window that integrates all panels:
- Hex monitor (raw data view)
- Mouse visualizer (trajectory + button states)
- Log panel (recording + export)
- Toolbar (connection controls)
- Status bar
"""

import sys
import time
import traceback

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QAction, QFont, QIcon, QKeySequence
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QSplitter, QLabel, QPushButton, QComboBox, QStatusBar,
    QToolBar, QMenuBar, QMessageBox, QFrame, QSizePolicy,
)

from .. import __version__
from ..core.protocols import (
    MousePacketParser, ProtocolType, PROTOCOL_CONFIGS,
)
from ..core.serial_worker import SerialWorker, list_serial_ports
from .hex_monitor import HexMonitorPanel
from .mouse_canvas import MouseVisualizerPanel
from .log_panel import LogPanel
from .settings_dialog import SerialSettingsDialog


# ── Dark Theme Stylesheet ──
DARK_THEME = """
QMainWindow {
    background-color: #11111b;
}
QMenuBar {
    background-color: #1e1e2e;
    color: #cdd6f4;
    border-bottom: 1px solid #313244;
    padding: 2px;
}
QMenuBar::item:selected {
    background-color: #313244;
    border-radius: 4px;
}
QMenu {
    background-color: #1e1e2e;
    color: #cdd6f4;
    border: 1px solid #45475a;
    border-radius: 6px;
    padding: 4px;
}
QMenu::item:selected {
    background-color: #45475a;
    border-radius: 4px;
}
QToolBar {
    background-color: #1e1e2e;
    border-bottom: 1px solid #313244;
    padding: 4px;
    spacing: 4px;
}
QStatusBar {
    background-color: #181825;
    color: #a6adc8;
    border-top: 1px solid #313244;
    font-size: 11px;
}
QLabel {
    color: #cdd6f4;
}
QComboBox {
    background-color: #313244;
    color: #cdd6f4;
    border: 1px solid #45475a;
    border-radius: 4px;
    padding: 6px 12px;
    font-size: 12px;
    min-width: 100px;
}
QComboBox:hover {
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
QPushButton {
    border: none;
    border-radius: 6px;
    padding: 8px 16px;
    font-size: 12px;
    font-weight: bold;
}
QPushButton:disabled {
    background-color: #45475a;
    color: #6c7086;
}
QSplitter::handle {
    background-color: #313244;
    width: 2px;
}
QSplitter::handle:hover {
    background-color: #89b4fa;
}
"""


class MainWindow(QMainWindow):
    """Main application window for Serial Mouse Tester."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"🖱 Serial Mouse Tester {__version__}")
        self.setMinimumSize(1200, 800)

        # State
        self._serial_worker: SerialWorker = None
        self._parser = MousePacketParser()
        self._current_settings = {
            "port": "",
            "protocol": ProtocolType.UNKNOWN,
            "baudrate": 1200,
            "bytesize": 7,
            "parity": "N",
            "stopbits": 1,
            "auto_scroll": True,
            "show_timestamps": True,
            "show_annotations": True,
        }
        self._packet_count = 0
        self._total_bytes = 0
        self._connection_start = 0.0

        self._build_ui()
        self._build_menu()
        self._build_toolbar()
        self._build_statusbar()

        # Statistics timer
        self._stats_timer = QTimer(self)
        self._stats_timer.timeout.connect(self._update_statusbar)
        self._stats_timer.start(500)

    def _build_ui(self):
        """Build the central widget with panels."""
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(6, 6, 6, 6)
        main_layout.setSpacing(4)

        # ── Splitter: Left (Hex + Log) / Right (Mouse Viz) ──
        self._splitter = QSplitter(Qt.Horizontal)

        # Left panel: Hex Monitor (top) + Log Panel (bottom)
        left_splitter = QSplitter(Qt.Vertical)
        self._hex_panel = HexMonitorPanel()
        self._log_panel = LogPanel()
        left_splitter.addWidget(self._hex_panel)
        left_splitter.addWidget(self._log_panel)
        left_splitter.setStretchFactor(0, 3)  # Hex gets more space
        left_splitter.setStretchFactor(1, 2)  # Log gets less

        # Right panel: Mouse Visualizer
        self._mouse_panel = MouseVisualizerPanel()

        self._splitter.addWidget(left_splitter)
        self._splitter.addWidget(self._mouse_panel)
        self._splitter.setStretchFactor(0, 5)  # Left side wider
        self._splitter.setStretchFactor(1, 3)  # Right side narrower

        main_layout.addWidget(self._splitter)

    def _build_menu(self):
        """Build the menu bar."""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("&File")

        self._act_connect = QAction("🔌 &Connect", self)
        self._act_connect.setShortcut(QKeySequence("Ctrl+Shift+C"))
        self._act_connect.triggered.connect(self._toggle_connection)
        file_menu.addAction(self._act_connect)

        self._act_disconnect = QAction("⏏ &Disconnect", self)
        self._act_disconnect.setShortcut(QKeySequence("Ctrl+Shift+D"))
        self._act_disconnect.setEnabled(False)
        self._act_disconnect.triggered.connect(self._disconnect)
        file_menu.addAction(self._act_disconnect)

        file_menu.addSeparator()

        act_export = QAction("💾 &Export CSV...", self)
        act_export.setShortcut(QKeySequence("Ctrl+E"))
        act_export.triggered.connect(self._log_panel._export_csv)
        file_menu.addAction(act_export)

        file_menu.addSeparator()

        act_exit = QAction("🚪 E&xit", self)
        act_exit.setShortcut(QKeySequence("Alt+F4"))
        act_exit.triggered.connect(self.close)
        file_menu.addAction(act_exit)

        # Settings menu
        settings_menu = menubar.addMenu("&Settings")

        act_serial = QAction("⚙ &Serial Port Settings...", self)
        act_serial.setShortcut(QKeySequence("Ctrl+,"))
        act_serial.triggered.connect(self._open_settings)
        settings_menu.addAction(act_serial)

        settings_menu.addSeparator()

        act_reset_view = QAction("🔄 &Reset Mouse View", self)
        act_reset_view.triggered.connect(self._reset_mouse_view)
        settings_menu.addAction(act_reset_view)

        # View menu
        view_menu = menubar.addMenu("&View")

        act_clear_hex = QAction("🗑 Clear Hex Monitor", self)
        act_clear_hex.triggered.connect(self._hex_panel.clear_all)
        view_menu.addAction(act_clear_hex)

        act_clear_log = QAction("🗑 Clear Log Table", self)
        act_clear_log.triggered.connect(self._log_panel._clear_log)
        view_menu.addAction(act_clear_log)

        act_clear_all = QAction("🗑 Clear &All", self)
        act_clear_all.setShortcut(QKeySequence("Ctrl+Shift+X"))
        act_clear_all.triggered.connect(self._clear_all)
        view_menu.addAction(act_clear_all)

        # Help menu
        help_menu = menubar.addMenu("&Help")

        act_about = QAction("ℹ &About", self)
        act_about.triggered.connect(self._show_about)
        help_menu.addAction(act_about)

        act_protocols = QAction("📖 &Protocol Reference", self)
        act_protocols.triggered.connect(self._show_protocol_reference)
        help_menu.addAction(act_protocols)

    def _build_toolbar(self):
        """Build the main toolbar."""
        toolbar = QToolBar("Main Toolbar")
        toolbar.setMovable(False)
        self.addToolBar(toolbar)

        # Port selector
        toolbar.addWidget(QLabel(" Port: "))
        self._cmb_port = QComboBox()
        self._cmb_port.setMinimumWidth(180)
        self._refresh_port_list()
        toolbar.addWidget(self._cmb_port)

        # Baud rate
        toolbar.addWidget(QLabel(" Baud: "))
        self._cmb_baud = QComboBox()
        self._cmb_baud.addItems([
            "300", "600", "1200", "2400", "4800", "9600",
            "19200", "38400", "57600", "115200",
        ])
        self._cmb_baud.setCurrentText("1200")
        self._cmb_baud.setFixedWidth(80)
        toolbar.addWidget(self._cmb_baud)

        # Protocol
        toolbar.addWidget(QLabel(" Protocol: "))
        self._cmb_proto = QComboBox()
        self._cmb_proto.addItems(["Auto-Detect", "Microsoft", "Logitech", "Mouse Systems"])
        self._cmb_proto.setFixedWidth(120)
        toolbar.addWidget(self._cmb_proto)

        toolbar.addSeparator()

        # Connect button
        self._btn_connect = QPushButton("🔌 Connect")
        self._btn_connect.setStyleSheet("""
            QPushButton {
                background-color: #a6e3a1;
                color: #1e1e2e;
            }
            QPushButton:hover { background-color: #94e2d5; }
        """)
        self._btn_connect.clicked.connect(self._toggle_connection)
        toolbar.addWidget(self._btn_connect)

        # Disconnect button
        self._btn_disconnect = QPushButton("⏏ Disconnect")
        self._btn_disconnect.setStyleSheet("""
            QPushButton {
                background-color: #f38ba8;
                color: #1e1e2e;
            }
            QPushButton:hover { background-color: #eba0ac; }
        """)
        self._btn_disconnect.setEnabled(False)
        self._btn_disconnect.clicked.connect(self._disconnect)
        toolbar.addWidget(self._btn_disconnect)

        toolbar.addSeparator()

        # Refresh ports button
        self._btn_refresh = QPushButton("🔄")
        self._btn_refresh.setFixedWidth(36)
        self._btn_refresh.setStyleSheet("""
            QPushButton {
                background-color: #45475a;
                color: #cdd6f4;
            }
            QPushButton:hover { background-color: #585b70; }
        """)
        self._btn_refresh.clicked.connect(self._refresh_port_list)
        toolbar.addWidget(self._btn_refresh)

    def _build_statusbar(self):
        """Build the status bar."""
        self._statusbar = QStatusBar()
        self.setStatusBar(self._statusbar)

        # Connection status
        self._lbl_conn = QLabel("⚪ Disconnected")
        self._lbl_conn.setStyleSheet("color: #f38ba8; font-weight: bold; padding: 0 8px;")
        self._statusbar.addWidget(self._lbl_conn)

        # Protocol
        self._lbl_protocol = QLabel("Protocol: —")
        self._lbl_protocol.setStyleSheet("padding: 0 8px;")
        self._statusbar.addWidget(self._lbl_protocol)

        # Packet count
        self._lbl_packets = QLabel("Packets: 0")
        self._lbl_packets.setStyleSheet("padding: 0 8px;")
        self._statusbar.addWidget(self._lbl_packets)

        # Bytes
        self._lbl_bytes = QLabel("Bytes: 0")
        self._lbl_bytes.setStyleSheet("padding: 0 8px;")
        self._statusbar.addWidget(self._lbl_bytes)

        # Elapsed
        self._lbl_elapsed = QLabel("Time: —")
        self._lbl_elapsed.setStyleSheet("padding: 0 8px;")
        self._statusbar.addWidget(self._lbl_elapsed)

        # Version
        self._lbl_version = QLabel(f"  {__version__}  ")
        self._lbl_version.setStyleSheet("color: #6c7086; padding: 0 8px;")
        self._statusbar.addPermanentWidget(self._lbl_version)

    # ── Connection Management ──

    def _refresh_port_list(self):
        self._cmb_port.clear()
        ports = list_serial_ports()
        if ports:
            for p in ports:
                label = f"{p['device']} ({p['description'][:30]})"
                self._cmb_port.addItem(label, p["device"])
        else:
            self._cmb_port.addItem("No ports found", "")

    def _toggle_connection(self):
        if self._serial_worker and self._serial_worker.is_connected:
            self._disconnect()
        else:
            self._connect()

    def _connect(self):
        port_name = self._cmb_port.currentData()
        if not port_name:
            QMessageBox.warning(self, "Connection", "Please select a serial port.")
            return

        # Get settings
        baudrate = int(self._cmb_baud.currentText())
        proto_idx = self._cmb_proto.currentIndex()

        proto_map = {0: ProtocolType.UNKNOWN, 1: ProtocolType.MICROSOFT,
                     2: ProtocolType.LOGITECH, 3: ProtocolType.MOUSE_SYSTEMS}
        protocol = proto_map.get(proto_idx, ProtocolType.UNKNOWN)

        # Apply protocol defaults if not auto-detect
        bytesize = 7
        parity = "N"
        stopbits = 1
        if protocol in PROTOCOL_CONFIGS:
            cfg = PROTOCOL_CONFIGS[protocol]
            baudrate = cfg.baudrate
            bytesize = cfg.bytesize
            parity = cfg.parity
            stopbits = cfg.stopbits
            self._cmb_baud.setCurrentText(str(baudrate))

        # Reset parser
        self._parser.reset()
        if protocol != ProtocolType.UNKNOWN:
            self._parser.set_protocol(protocol)

        # Create and start worker
        self._serial_worker = SerialWorker(
            port_name=port_name,
            baudrate=baudrate,
            bytesize=bytesize,
            parity=parity,
            stopbits=stopbits,
        )
        self._serial_worker.data_received.connect(self._on_data_received)
        self._serial_worker.error_occurred.connect(self._on_serial_error)
        self._serial_worker.connection_changed.connect(self._on_connection_changed)
        self._serial_worker.port_info.connect(self._on_port_info)

        self._connection_start = time.time()
        self._packet_count = 0
        self._total_bytes = 0

        self._serial_worker.start()

    def _disconnect(self):
        if self._serial_worker:
            self._serial_worker.stop()
            self._serial_worker = None

    # ── Data Handling ──

    def _on_data_received(self, data: bytes):
        """Handle raw serial data from the worker thread."""
        self._total_bytes += len(data)

        # Show raw data in hex monitor
        self._hex_panel.append_raw_data(data)

        # Parse packets
        states = self._parser.feed(data)
        for state in states:
            self._packet_count += 1

            # Update visualizer
            self._mouse_panel.update_mouse(
                state.dx, state.dy,
                state.left_button, state.right_button, state.middle_button,
            )

            # Add to log table
            self._log_panel.add_state(state)

            # Show parsed annotation in hex monitor
            if self._current_settings.get("show_annotations", True):
                self._hex_panel.append_parsed_line(
                    f"  {state.protocol} | dX={state.dx:+d} dY={state.dy:+d} "
                    f"[{state.buttons_str()}]",
                    color="#a6e3a1",
                )

        # Update protocol display
        proto = self._parser.protocol
        if proto != ProtocolType.UNKNOWN:
            self._lbl_protocol.setText(f"Protocol: {proto}")

    def _on_serial_error(self, msg: str):
        self._statusbar.showMessage(f"❌ {msg}", 5000)
        self._lbl_conn.setText("⚠ Error")
        self._lbl_conn.setStyleSheet("color: #fab387; font-weight: bold; padding: 0 8px;")

    def _on_connection_changed(self, connected: bool):
        if connected:
            self._lbl_conn.setText("🟢 Connected")
            self._lbl_conn.setStyleSheet("color: #a6e3a1; font-weight: bold; padding: 0 8px;")
            self._btn_connect.setEnabled(False)
            self._btn_disconnect.setEnabled(True)
            self._act_connect.setEnabled(False)
            self._act_disconnect.setEnabled(True)
            self._cmb_port.setEnabled(False)
            self._cmb_baud.setEnabled(False)
            self._cmb_proto.setEnabled(False)
        else:
            self._lbl_conn.setText("⚪ Disconnected")
            self._lbl_conn.setStyleSheet("color: #f38ba8; font-weight: bold; padding: 0 8px;")
            self._btn_connect.setEnabled(True)
            self._btn_disconnect.setEnabled(False)
            self._act_connect.setEnabled(True)
            self._act_disconnect.setEnabled(False)
            self._cmb_port.setEnabled(True)
            self._cmb_baud.setEnabled(True)
            self._cmb_proto.setEnabled(True)

    def _on_port_info(self, msg: str):
        self._statusbar.showMessage(msg, 3000)

    # ── UI Actions ──

    def _open_settings(self):
        dialog = SerialSettingsDialog(self)
        dialog.set_current_settings(self._current_settings)
        if dialog.exec():
            settings = dialog.get_settings()
            self._current_settings.update(settings)

            # Update toolbar
            if "baudrate" in settings:
                self._cmb_baud.setCurrentText(str(settings["baudrate"]))
            if "protocol" in settings:
                proto_idx = {ProtocolType.UNKNOWN: 0, ProtocolType.MICROSOFT: 1,
                             ProtocolType.LOGITECH: 2, ProtocolType.MOUSE_SYSTEMS: 3}
                self._cmb_proto.setCurrentIndex(proto_idx.get(settings["protocol"], 0))

    def _reset_mouse_view(self):
        self._mouse_panel.reset()

    def _clear_all(self):
        self._hex_panel.clear_all()
        self._log_panel._clear_log()
        self._mouse_panel.reset()
        self._packet_count = 0
        self._total_bytes = 0

    def _update_statusbar(self):
        self._lbl_packets.setText(f"Packets: {self._packet_count:,}")
        self._lbl_bytes.setText(f"Bytes: {self._total_bytes:,}")

        if self._serial_worker and self._serial_worker.is_connected:
            elapsed = time.time() - self._connection_start
            mins, secs = divmod(int(elapsed), 60)
            hours, mins = divmod(mins, 60)
            self._lbl_elapsed.setText(f"Time: {hours:02d}:{mins:02d}:{secs:02d}")
        else:
            self._lbl_elapsed.setText("Time: —")

    def _show_about(self):
        QMessageBox.about(
            self,
            "About Serial Mouse Tester",
            f"<h2>🖱 Serial Mouse Tester</h2>"
            f"<p><b>Version:</b> {__version__}</p>"
            f"<p><b>Author:</b> Bear Brother & Hui Bao</p>"
            f"<p>A modern serial mouse testing and analysis tool.</p>"
            f"<p>Supports Microsoft, Logitech, and Mouse Systems protocols "
            f"with auto-detection.</p>"
            f"<hr>"
            f"<p style='color: #6c7086; font-size: 11px;'>"
            f"Built with Python + PySide6</p>",
        )

    def _show_protocol_reference(self):
        QMessageBox.information(
            self,
            "Protocol Reference",
            "<h3>📡 Serial Mouse Protocols</h3>"
            "<table cellpadding='4'>"
            "<tr><td><b>Microsoft 2-Button</b></td><td>1200 baud, 7N1</td>"
            "<td>3-byte packets</td></tr>"
            "<tr><td><b>Logitech 3-Button</b></td><td>1200 baud, 7N1</td>"
            "<td>3/4-byte packets</td></tr>"
            "<tr><td><b>Mouse Systems</b></td><td>1200 baud, 8N1</td>"
            "<td>5-byte packets</td></tr>"
            "</table>"
            "<p style='margin-top: 8px;'>Auto-detection analyzes byte patterns "
            "to identify the protocol automatically.</p>",
        )

    def closeEvent(self, event):
        """Clean up on window close."""
        self._disconnect()
        self._log_panel.stop_recording()
        event.accept()


def main():
    """Application entry point."""
    # Global exception handler - prevent crashes
    def exception_hook(exc_type, exc_value, exc_tb):
        error_msg = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
        print(f"[FATAL] Unhandled exception:\n{error_msg}", file=sys.stderr)
        # Show error dialog instead of crashing
        try:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.critical(
                None, "Unexpected Error",
                f"An unexpected error occurred:\n\n{exc_value}\n\n"
                f"The application will continue running."
            )
        except Exception:
            pass

    sys.excepthook = exception_hook

    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setStyleSheet(DARK_THEME)

    # Set application-wide font
    font = QFont("Segoe UI", 10)
    app.setFont(font)

    window = MainWindow()
    window.show()

    return app.exec()
