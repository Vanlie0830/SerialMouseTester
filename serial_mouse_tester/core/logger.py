"""
Data Logger Module

Records parsed mouse states and raw bytes to CSV or log files.
"""

import csv
import os
import time
from datetime import datetime
from typing import Optional, TextIO

from .protocols import MouseState, ProtocolType


class DataLogger:
    """
    Records mouse events to CSV or plain-text log files.

    CSV columns:
        timestamp, protocol, dx, dy, x_pos, y_pos,
        left_btn, right_btn, middle_btn, raw_hex
    """

    def __init__(self):
        self._file: Optional[TextIO] = None
        self._csv_writer = None
        self._log_file: Optional[TextIO] = None
        self._is_recording = False
        self._record_count = 0
        self._start_time = 0.0
        self._filepath = ""

    @property
    def is_recording(self) -> bool:
        return self._is_recording

    @property
    def record_count(self) -> int:
        return self._record_count

    @property
    def filepath(self) -> str:
        return self._filepath

    def start_recording(self, filepath: str) -> bool:
        """Start recording to a CSV file."""
        if self._is_recording:
            self.stop_recording()

        try:
            self._filepath = filepath
            self._file = open(filepath, "w", newline="", encoding="utf-8")
            self._csv_writer = csv.writer(self._file)
            self._csv_writer.writerow([
                "timestamp", "datetime", "protocol", "dx", "dy",
                "cumulative_x", "cumulative_y",
                "left_btn", "right_btn", "middle_btn", "buttons",
                "raw_hex",
            ])
            self._is_recording = True
            self._record_count = 0
            self._start_time = time.time()
            return True
        except (OSError, IOError) as e:
            print(f"Failed to start recording: {e}")
            return False

    def stop_recording(self) -> Optional[str]:
        """Stop recording and return the file path."""
        if not self._is_recording:
            return None

        try:
            if self._file:
                self._file.close()
        except Exception:
            pass

        self._file = None
        self._csv_writer = None
        self._is_recording = False
        filepath = self._filepath
        self._filepath = ""
        return filepath

    def log_state(self, state: MouseState, cum_x: int = 0, cum_y: int = 0):
        """Write a parsed mouse state to the CSV file."""
        if not self._is_recording or not self._csv_writer:
            return

        timestamp = state.timestamp or time.time()
        dt_str = datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]

        self._csv_writer.writerow([
            f"{timestamp:.6f}",
            dt_str,
            str(state.protocol),
            state.dx,
            state.dy,
            cum_x,
            cum_y,
            int(state.left_button),
            int(state.right_button),
            int(state.middle_button),
            state.buttons_str(),
            state.raw_bytes.hex().upper(),
        ])
        self._record_count += 1

    def log_raw(self, data: bytes):
        """Write raw bytes to a separate log file (if open)."""
        if self._log_file:
            timestamp = time.time()
            dt_str = datetime.fromtimestamp(timestamp).strftime("%H:%M:%S.%f")[:-3]
            hex_str = " ".join(f"{b:02X}" for b in data)
            self._log_file.write(f"[{dt_str}] RX ({len(data)} bytes): {hex_str}\n")
            self._log_file.flush()

    def open_log(self, filepath: str) -> bool:
        """Open a raw data log file for writing."""
        try:
            self._log_file = open(filepath, "a", encoding="utf-8")
            return True
        except (OSError, IOError):
            return False

    def close_log(self):
        """Close the raw data log file."""
        if self._log_file:
            try:
                self._log_file.close()
            except Exception:
                pass
            self._log_file = None

    def get_recording_duration(self) -> float:
        """Get recording duration in seconds."""
        if self._is_recording:
            return time.time() - self._start_time
        return 0.0
