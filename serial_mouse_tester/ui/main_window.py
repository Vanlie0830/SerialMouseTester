"""
Main Window (VVT-style refactor)

Architecture:
- Sidebar navigation (panel switching)
- QStackedWidget content area
- Centralized SignalRegistry (no lambda sea)
- Evidence-based error handling
"""

import sys
import time
import traceback

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QStackedWidget, QLabel, QPushButton, QComboBox, QStatusBar,
    QToolBar, QMessageBox,
)

from .. import __version__
from ..core.protocols import (
    MousePacketParser, ProtocolType, PROTOCOL_CONFIGS,
)
from ..core.serial_worker import SerialWorker, list_serial_ports
from .theme import Palette, Fonts, FULL_QSS
from .sidebar import Sidebar
from .hex_monitor import HexMonitorPanel
from .mouse_canvas import MouseVisualizerPanel
from .log_panel import LogPanel
from .settings_dialog import SerialSettingsDialog


class SignalRegistry:
    """Centralized signal-to-slot registry (VVT pattern)."""
    def __init__(self):
        self._handlers: dict = {}

    def register(self, event, handler):
        self._handlers.setdefault(event, []).append(handler)

    def emit(self, event, *args, **kwargs):
        for handler in self._handlers.get(event, []):
            try:
                handler(*args, **kwargs)
            except Exception as e:
                print(f"[SignalRegistry] '{event}': {e}", file=sys.stderr)


class MainWindow(QMainWindow):
    """Main window with sidebar navigation and panel switching."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"\U0001f5b1 Serial Mouse Tester {__version__}")
        self.setMinimumSize(1100, 700)

        self._serial_worker = None
        self._parser = MousePacketParser()
        self._registry = SignalRegistry()
        self._packet_count = 0
        self._total_bytes = 0
        self._connection_start = 0.0
        self._last_parse_ms = 0.0
        self._last_recv_bytes = 0

        self._build_ui()
        self._build_menu()
        self._build_toolbar()
        self._build_statusbar()
        self._register_events()

        self._stats_timer = QTimer(self)
        self._stats_timer.timeout.connect(self._update_statusbar)
        self._stats_timer.start(500)

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QHBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._sidebar = Sidebar()
        self._sidebar.navigate.connect(self._on_navigate)

        self._stack = QStackedWidget()
        self._hex_panel = HexMonitorPanel()
        self._stack.addWidget(self._hex_panel)
        self._mouse_panel = MouseVisualizerPanel()
        self._stack.addWidget(self._mouse_panel)
        self._log_panel = LogPanel()
        self._stack.addWidget(self._log_panel)
        self._stack.addWidget(self._build_settings_panel())

        layout.addWidget(self._sidebar)
        layout.addWidget(self._stack, stretch=1)
        self._stack.setCurrentIndex(0)

    def _build_settings_panel(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        title = QLabel("\u2699 Settings")
        title.setFont(QFont(Fonts.UI, Fonts.HEADING_SIZE, QFont.Bold))
        title.setStyleSheet(f"color: {Palette.TEXT};")

        btn_serial = QPushButton("  \U0001f50c Serial Port Configuration")
        btn_serial.setProperty("variant", "primary")
        btn_serial.setFixedHeight(48)
        btn_serial.clicked.connect(self._open_settings)

        btn_reset = QPushButton("  \U0001f504 Reset Mouse View")
        btn_reset.setProperty("variant", "secondary")
        btn_reset.setFixedHeight(48)
        btn_reset.clicked.connect(self._mouse_panel.reset)

        btn_clear = QPushButton("  \U0001f5d1 Clear All Data")
        btn_clear.setProperty("variant", "danger")
        btn_clear.setFixedHeight(48)
        btn_clear.clicked.connect(self._clear_all)

        info = QLabel(
            f"Serial Mouse Tester {__version__}\n"
            f"Python + PySide6 (Qt6) | Catppuccin Mocha\n"
            f"VVT-style development discipline\n\n"
            f"Protocols: Microsoft, Logitech, Mouse Systems\n"
            f"Features: Auto-detect, Hex Monitor, Trajectory, CSV Export"
        )
        info.setStyleSheet(f"color: {Palette.SUBTEXT0}; font-size: 12px;")
        info.setWordWrap(True)

        layout.addWidget(title)
        layout.addWidget(btn_serial)
        layout.addWidget(btn_reset)
        layout.addWidget(btn_clear)
        layout.addStretch()
        layout.addWidget(info)
        return widget

    def _build_menu(self):
        menubar = self.menuBar()
        file_menu = menubar.addMenu("&File")
        file_menu.addAction("\U0001f50c &Connect", self._toggle_connection)
        file_menu.addAction("\u2387 &Disconnect", self._disconnect)
        file_menu.addSeparator()
        file_menu.addAction("\U0001f4be &Export CSV...", self._log_panel._export_csv)
        file_menu.addSeparator()
        file_menu.addAction("\U0001f6aa E&xit", self.close)

        settings_menu = menubar.addMenu("&Settings")
        settings_menu.addAction("\u2699 &Serial Port Settings...", self._open_settings)
        settings_menu.addSeparator()
        settings_menu.addAction("\U0001f504 &Reset Mouse View", self._mouse_panel.reset)

        view_menu = menubar.addMenu("&View")
        view_menu.addAction("\U0001f4ca &Hex Monitor", lambda: self._on_navigate("hex"))
        view_menu.addAction("\U0001f5b1 &Mouse View", lambda: self._on_navigate("mouse"))
        view_menu.addAction("\U0001f4be &Data Log", lambda: self._on_navigate("log"))
        view_menu.addAction("\u2699 &Settings", lambda: self._on_navigate("settings"))

        help_menu = menubar.addMenu("&Help")
        help_menu.addAction("\u2139 &About", self._show_about)

    def _build_toolbar(self):
        toolbar = QToolBar("Main")
        toolbar.setMovable(False)
        self.addToolBar(toolbar)

        toolbar.addWidget(QLabel(" Port: "))
        self._cmb_port = QComboBox()
        self._cmb_port.setMinimumWidth(180)
        self._refresh_port_list()
        toolbar.addWidget(self._cmb_port)

        toolbar.addWidget(QLabel(" Baud: "))
        self._cmb_baud = QComboBox()
        self._cmb_baud.addItems(["300","600","1200","2400","4800","9600","19200","38400","57600","115200"])
        self._cmb_baud.setCurrentText("1200")
        self._cmb_baud.setFixedWidth(80)
        toolbar.addWidget(self._cmb_baud)

        toolbar.addWidget(QLabel(" Proto: "))
        self._cmb_proto = QComboBox()
        self._cmb_proto.addItems(["Auto", "Microsoft", "Logitech", "MouseSys"])
        self._cmb_proto.setFixedWidth(100)
        toolbar.addWidget(self._cmb_proto)

        toolbar.addSeparator()
        self._btn_connect = QPushButton("\U0001f50c Connect")
        self._btn_connect.setProperty("variant", "primary")
        self._btn_connect.clicked.connect(self._toggle_connection)
        toolbar.addWidget(self._btn_connect)

        self._btn_disconnect = QPushButton("\u2387 Disconnect")
        self._btn_disconnect.setProperty("variant", "danger")
        self._btn_disconnect.setEnabled(False)
        self._btn_disconnect.clicked.connect(self._disconnect)
        toolbar.addWidget(self._btn_disconnect)

    def _build_statusbar(self):
        self._statusbar = QStatusBar()
        self.setStatusBar(self._statusbar)
        self._lbl_conn = QLabel("\u26aa Disconnected")
        self._lbl_conn.setStyleSheet(f"color: {Palette.RED}; font-weight: bold; padding: 0 8px;")
        self._statusbar.addWidget(self._lbl_conn)
        self._lbl_protocol = QLabel("Protocol: \u2014")
        self._statusbar.addWidget(self._lbl_protocol)
        self._lbl_packets = QLabel("Packets: 0")
        self._statusbar.addWidget(self._lbl_packets)
        self._lbl_perf = QLabel("parse: —")
        self._lbl_perf.setStyleSheet(f"color: {Palette.OVERLAY0}; font-size: 10px; padding: 0 8px;")
        self._statusbar.addWidget(self._lbl_perf)

        self._lbl_version = QLabel(f"  {__version__}  ")
        self._lbl_version.setStyleSheet(f"color: {Palette.OVERLAY0};")
        self._statusbar.addPermanentWidget(self._lbl_version)

    def _register_events(self):
        self._registry.register("connection_changed", self._on_connection_changed)
        self._registry.register("data_received", self._on_data_received)
        self._registry.register("serial_error", self._on_serial_error)
        self._registry.register("port_info", self._on_port_info)

    def _on_navigate(self, panel_id):
        panel_map = {"hex": 0, "mouse": 1, "log": 2, "settings": 3}
        self._stack.setCurrentIndex(panel_map.get(panel_id, 0))

    def _refresh_port_list(self):
        self._cmb_port.clear()
        ports = list_serial_ports()
        if ports:
            for p in ports:
                self._cmb_port.addItem(f"{p['device']} ({p['description'][:30]})", p["device"])
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
        baudrate = int(self._cmb_baud.currentText())
        proto_idx = self._cmb_proto.currentIndex()
        proto_map = {0: ProtocolType.UNKNOWN, 1: ProtocolType.MICROSOFT, 2: ProtocolType.LOGITECH, 3: ProtocolType.MOUSE_SYSTEMS}
        protocol = proto_map.get(proto_idx, ProtocolType.UNKNOWN)
        bytesize, parity, stopbits = 7, "N", 1
        if protocol in PROTOCOL_CONFIGS:
            cfg = PROTOCOL_CONFIGS[protocol]
            baudrate, bytesize, parity, stopbits = cfg.baudrate, cfg.bytesize, cfg.parity, cfg.stopbits
        self._parser.reset()
        if protocol != ProtocolType.UNKNOWN:
            self._parser.set_protocol(protocol)
        self._serial_worker = SerialWorker(port_name=port_name, baudrate=baudrate, bytesize=bytesize, parity=parity, stopbits=stopbits)
        self._serial_worker.data_received.connect(lambda d: self._registry.emit("data_received", d))
        self._serial_worker.error_occurred.connect(lambda m: self._registry.emit("serial_error", m))
        self._serial_worker.connection_changed.connect(lambda c: self._registry.emit("connection_changed", c))
        self._serial_worker.port_info.connect(lambda m: self._registry.emit("port_info", m))
        self._connection_start = time.time()
        self._packet_count = 0
        self._total_bytes = 0
        self._serial_worker.start()

    def _disconnect(self):
        # Non-blocking disconnect: signal thread to stop, don't wait
        if self._serial_worker:
            self._serial_worker.stop()
            # Don't set to None yet - let connection_changed(False) handle cleanup
            self._btn_disconnect.setEnabled(False)  # Prevent double-click
            self._btn_connect.setEnabled(False)     # Disable until disconnect completes

    def _on_data_received(self, data):
        t0 = time.perf_counter()
        self._total_bytes += len(data)
        self._hex_panel.append_raw_data(data)
        t_parse_start = time.perf_counter()
        states = self._parser.feed(data)
        t_parse_end = time.perf_counter()
        # RS-232: phase timing instrumentation
        self._last_parse_ms = (t_parse_end - t_parse_start) * 1000
        self._last_recv_bytes = len(data)
        for state in states:
            self._packet_count += 1
            self._mouse_panel.update_mouse(state.dx, state.dy, state.left_button, state.right_button, state.middle_button)
            self._log_panel.add_state(state)
        proto = self._parser.protocol
        if proto != ProtocolType.UNKNOWN:
            self._lbl_protocol.setText(f"Protocol: {proto}")
            self._sidebar.update_protocol(str(proto))

    def _on_connection_changed(self, connected):
        if connected:
            self._lbl_conn.setText("\U0001f7e2 Connected")
            self._lbl_conn.setStyleSheet(f"color: {Palette.GREEN}; font-weight: bold; padding: 0 8px;")
            self._btn_connect.setEnabled(False)
            self._btn_disconnect.setEnabled(True)
            self._cmb_port.setEnabled(False)
            self._cmb_baud.setEnabled(False)
            self._cmb_proto.setEnabled(False)
            detail = f"{self._cmb_port.currentData()} @ {self._cmb_baud.currentText()} baud"
            self._sidebar.update_connection(True, detail)
        else:
            self._lbl_conn.setText("\u26aa Disconnected")
            self._lbl_conn.setStyleSheet(f"color: {Palette.RED}; font-weight: bold; padding: 0 8px;")
            self._btn_connect.setEnabled(True)
            self._btn_disconnect.setEnabled(False)
            self._cmb_port.setEnabled(True)
            self._cmb_baud.setEnabled(True)
            self._cmb_proto.setEnabled(True)
            self._sidebar.update_connection(False)
            # Clean up worker reference after thread confirms it stopped
            if self._serial_worker:
                self._serial_worker.deleteLater()
                self._serial_worker = None

    def _on_serial_error(self, msg):
        self._statusbar.showMessage(f"\u274c {msg}", 8000)
        self._lbl_conn.setText("\u26a0 Error")
        self._lbl_conn.setStyleSheet(f"color: {Palette.PEACH}; font-weight: bold; padding: 0 8px;")

    def _on_port_info(self, msg):
        self._statusbar.showMessage(msg, 3000)

    def _open_settings(self):
        dialog = SerialSettingsDialog(self)
        if dialog.exec():
            settings = dialog.get_settings()
            if "baudrate" in settings:
                self._cmb_baud.setCurrentText(str(settings["baudrate"]))

    def _clear_all(self):
        self._hex_panel.clear_all()
        self._log_panel._clear_log()
        self._mouse_panel.reset()
        self._packet_count = 0
        self._total_bytes = 0

    def _update_statusbar(self):
        self._lbl_packets.setText(f"Packets: {self._packet_count:,}")
        self._sidebar.update_packets(self._packet_count, self._total_bytes)
        # RS-232: phase timing instrumentation
        parse_ms = getattr(self, '_last_parse_ms', 0)
        recv_b = getattr(self, '_last_recv_bytes', 0)
        self._lbl_perf.setText(f"parse: {parse_ms:.1f}ms | rx: {recv_b}B")

    def _show_about(self):
        QMessageBox.about(self, "About Serial Mouse Tester",
            f"<h2>\U0001f5b1 Serial Mouse Tester</h2>"
            f"<p><b>Version:</b> {__version__}</p>"
            f"<p><b>Author:</b> Bear Brother & Hui Bao</p>"
            f"<p>VVT-style development discipline.</p>")

    def closeEvent(self, event):
        self._disconnect()
        self._log_panel.stop_recording()
        event.accept()


def main():
    def exception_hook(exc_type, exc_value, exc_tb):
        error_msg = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
        print(f"[FATAL] {error_msg}", file=sys.stderr)
        try:
            QMessageBox.critical(None, "Unexpected Error",
                f"An unexpected error occurred:\n\n{exc_value}\n\n"
                f"The application will continue running.")
        except Exception:
            pass
    sys.excepthook = exception_hook
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setStyleSheet(FULL_QSS)
    app.setFont(QFont(Fonts.UI, Fonts.UI_SIZE))
    window = MainWindow()
    window.show()
    return app.exec()
