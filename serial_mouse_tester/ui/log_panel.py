"""
Log Panel Widget

Data recording controls, CSV export, and event log display.
"""

import csv
import os
import time
from datetime import datetime

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QTableWidget, QTableWidgetItem,
    QFileDialog, QGroupBox, QHeaderView, QMessageBox,
)

from ..core.logger import DataLogger
from ..core.protocols import MouseState

MAX_TABLE_ROWS = 5000


class LogPanel(QWidget):
    """Panel for data recording, display, and export."""

    # Signals
    export_requested = Signal(str)  # filepath

    def __init__(self, parent=None):
        super().__init__(parent)
        self._logger = DataLogger()
        self._cumulative_x = 0
        self._cumulative_y = 0

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        # ── Controls ──
        ctrl_layout = QHBoxLayout()

        self._btn_record = QPushButton("⏺ Start Recording")
        self._btn_record.setStyleSheet("""
            QPushButton {
                background-color: #a6e3a1;
                color: #1e1e2e;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #94e2d5; }
            QPushButton:pressed { background-color: #74c7ec; }
        """)
        self._btn_record.clicked.connect(self._toggle_recording)

        self._btn_export = QPushButton("💾 Export CSV")
        self._btn_export.setStyleSheet("""
            QPushButton {
                background-color: #89b4fa;
                color: #1e1e2e;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #74c7ec; }
        """)
        self._btn_export.clicked.connect(self._export_csv)

        self._btn_clear = QPushButton("🗑 Clear")
        self._btn_clear.setStyleSheet("""
            QPushButton {
                background-color: #45475a;
                color: #cdd6f4;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 12px;
            }
            QPushButton:hover { background-color: #585b70; }
        """)
        self._btn_clear.clicked.connect(self._clear_log)

        self._lbl_status = QLabel("⚪ Not recording")
        self._lbl_status.setStyleSheet("color: #a6adc8; font-size: 11px;")

        self._lbl_count = QLabel("Records: 0")
        self._lbl_count.setStyleSheet("color: #a6adc8; font-size: 11px;")

        ctrl_layout.addWidget(self._btn_record)
        ctrl_layout.addWidget(self._btn_export)
        ctrl_layout.addWidget(self._btn_clear)
        ctrl_layout.addStretch()
        ctrl_layout.addWidget(self._lbl_count)
        ctrl_layout.addWidget(self._lbl_status)

        # ── Data Table ──
        self._table = QTableWidget()
        self._table.setColumnCount(10)
        self._table.setHorizontalHeaderLabels([
            "Time", "Protocol", "dX", "dY", "X", "Y",
            "L", "M", "R", "Raw Hex",
        ])
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self._table.setAlternatingRowColors(True)
        self._table.setFont(QFont("Consolas", 9))
        self._table.setStyleSheet("""
            QTableWidget {
                background-color: #1e1e2e;
                color: #cdd6f4;
                alternate-background-color: #232336;
                border: 1px solid #45475a;
                border-radius: 6px;
                gridline-color: #313244;
            }
            QTableWidget::item {
                padding: 4px;
            }
            QHeaderView::section {
                background-color: #313244;
                color: #cdd6f4;
                border: 1px solid #45475a;
                padding: 6px;
                font-weight: bold;
            }
        """)
        self._table.setEditTriggers(QTableWidget.NoEditTriggers)

        layout.addLayout(ctrl_layout)
        layout.addWidget(self._table, stretch=1)

    def add_state(self, state: MouseState):
        """Add a parsed mouse state to the table and logger."""
        self._cumulative_x += state.dx
        self._cumulative_y += state.dy

        # Log to CSV if recording
        if self._logger.is_recording:
            self._logger.log_state(state, self._cumulative_x, self._cumulative_y)

        # Add to table
        row = self._table.rowCount()
        if row >= MAX_TABLE_ROWS:
            self._table.removeRow(0)
            row -= 1

        self._table.insertRow(row)

        time_str = datetime.fromtimestamp(state.timestamp or time.time()).strftime("%H:%M:%S.%f")[:-3]

        items = [
            time_str,
            str(state.protocol),
            f"{state.dx:+d}",
            f"{state.dy:+d}",
            f"{self._cumulative_x}",
            f"{self._cumulative_y}",
            "●" if state.left_button else "○",
            "●" if state.middle_button else "○",
            "●" if state.right_button else "○",
            state.raw_bytes.hex().upper() if state.raw_bytes else "",
        ]

        for col, text in enumerate(items):
            item = QTableWidgetItem(text)
            # Color buttons
            if col in (6, 7, 8):
                btn_idx = {6: "left", 7: "middle", 8: "right"}
                is_active = [state.left_button, state.middle_button, state.right_button][col - 6]
                if is_active:
                    item.setForeground(Qt.red)
                else:
                    item.setForeground(Qt.gray)
            self._table.setItem(row, col, item)

        # Auto-scroll to bottom
        self._table.scrollToBottom()
        self._lbl_count.setText(f"Records: {self._table.rowCount():,}")

    def _toggle_recording(self):
        if self._logger.is_recording:
            filepath = self._logger.stop_recording()
            self._btn_record.setText("⏺ Start Recording")
            self._btn_record.setStyleSheet("""
                QPushButton {
                    background-color: #a6e3a1;
                    color: #1e1e2e;
                    border: none;
                    border-radius: 6px;
                    padding: 8px 16px;
                    font-size: 12px;
                    font-weight: bold;
                }
                QPushButton:hover { background-color: #94e2d5; }
            """)
            self._lbl_status.setText(f"✅ Saved: {os.path.basename(filepath) if filepath else 'N/A'}")
        else:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            default_name = f"serial_mouse_log_{timestamp}.csv"
            filepath, _ = QFileDialog.getSaveFileName(
                self, "Save Recording As", default_name,
                "CSV Files (*.csv);;All Files (*.*)"
            )
            if filepath:
                if self._logger.start_recording(filepath):
                    self._btn_record.setText("⏹ Stop Recording")
                    self._btn_record.setStyleSheet("""
                        QPushButton {
                            background-color: #f38ba8;
                            color: #1e1e2e;
                            border: none;
                            border-radius: 6px;
                            padding: 8px 16px;
                            font-size: 12px;
                            font-weight: bold;
                        }
                        QPushButton:hover { background-color: #eba0ac; }
                    """)
                    self._lbl_status.setText(f"⏺ Recording: {os.path.basename(filepath)}")

    def _export_csv(self):
        """Export current table data to CSV."""
        if self._table.rowCount() == 0:
            QMessageBox.information(self, "Export", "No data to export.")
            return

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_name = f"serial_mouse_export_{timestamp}.csv"
        filepath, _ = QFileDialog.getSaveFileName(
            self, "Export CSV", default_name,
            "CSV Files (*.csv);;All Files (*.*)"
        )
        if not filepath:
            return

        try:
            with open(filepath, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                # Header
                headers = []
                for col in range(self._table.columnCount()):
                    headers.append(self._table.horizontalHeaderItem(col).text())
                writer.writerow(headers)
                # Data
                for row in range(self._table.rowCount()):
                    row_data = []
                    for col in range(self._table.columnCount()):
                        item = self._table.item(row, col)
                        row_data.append(item.text() if item else "")
                    writer.writerow(row_data)

            QMessageBox.information(self, "Export",
                                    f"Exported {self._table.rowCount()} records to:\n{filepath}")
            self.export_requested.emit(filepath)
        except (OSError, IOError) as e:
            QMessageBox.warning(self, "Export Error", f"Failed to export: {e}")

    def _clear_log(self):
        self._table.setRowCount(0)
        self._cumulative_x = 0
        self._cumulative_y = 0
        self._lbl_count.setText("Records: 0")

    def get_logger(self) -> DataLogger:
        return self._logger

    def stop_recording(self):
        """Stop recording if active (called on app close)."""
        if self._logger.is_recording:
            self._logger.stop_recording()
