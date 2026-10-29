"""
Serial Port Communication Worker

Runs in a separate QThread, continuously reading from the serial port
and emitting signals to the UI thread.
"""

import time
from typing import Optional

import serial
import serial.tools.list_ports
from PySide6.QtCore import QThread, Signal


def list_serial_ports() -> list[dict]:
    """List all available serial ports on the system."""
    ports = []
    for port_info in serial.tools.list_ports.comports():
        ports.append({
            "device": port_info.device,
            "name": port_info.name,
            "description": port_info.description,
            "hwid": port_info.hwid,
            "manufacturer": port_info.manufacturer or "Unknown",
        })
    return ports


class SerialWorker(QThread):
    """
    Background thread for reading serial mouse data.

    Signals:
        data_received(bytes): Raw bytes read from serial port
        error_occurred(str): Error message
        connection_changed(bool): True when connected, False when disconnected
        port_info(str): Status message about the port
    """

    data_received = Signal(bytes)
    error_occurred = Signal(str)
    connection_changed = Signal(bool)
    port_info = Signal(str)

    def __init__(
        self,
        port_name: str,
        baudrate: int = 1200,
        bytesize: int = 7,
        parity: str = "N",
        stopbits: float = 1,
        parent=None,
    ):
        super().__init__(parent)
        self._port_name = port_name
        self._baudrate = baudrate
        self._bytesize = bytesize
        self._parity = parity
        self._stopbits = stopbits
        self._running = False
        self._serial: Optional[serial.Serial] = None

        # Statistics
        self._bytes_read = 0
        self._last_activity = 0.0

    @property
    def port_name(self) -> str:
        return self._port_name

    @property
    def bytes_read(self) -> int:
        return self._bytes_read

    @property
    def is_connected(self) -> bool:
        return self._serial is not None and self._serial.is_open

    def run(self):
        """Main thread loop - read serial data continuously."""
        self._running = True
        try:
            # Open serial port
            parity_map = {"N": serial.PARITY_NONE, "E": serial.PARITY_EVEN,
                          "O": serial.PARITY_ODD, "M": serial.PARITY_MARK,
                          "S": serial.PARITY_SPACE}
            stopbits_map = {1: serial.STOPBITS_ONE, 1.5: serial.STOPBITS_ONE_POINT_FIVE,
                            2: serial.STOPBITS_TWO}
            bytesize_map = {5: serial.FIVEBITS, 6: serial.SIXBITS,
                            7: serial.SEVENBITS, 8: serial.EIGHTBITS}

            self._serial = serial.Serial(
                port=self._port_name,
                baudrate=self._baudrate,
                bytesize=bytesize_map.get(self._bytesize, serial.SEVENBITS),
                parity=parity_map.get(self._parity, serial.PARITY_NONE),
                stopbits=stopbits_map.get(self._stopbits, serial.STOPBITS_ONE),
                timeout=0.01,  # 10ms read timeout for responsive polling
            )

            self.port_info.emit(
                f"Connected to {self._port_name} @ {self._baudrate} baud "
                f"({self._bytesize}{self._parity}{self._stopbits})"
            )
            self.connection_changed.emit(True)

            # Main read loop
            while self._running:
                try:
                    if self._serial.in_waiting > 0:
                        data = self._serial.read(self._serial.in_waiting)
                        if data:
                            self._bytes_read += len(data)
                            self._last_activity = time.time()
                            self.data_received.emit(data)
                    else:
                        self.msleep(5)  # Small sleep to prevent CPU hogging
                except serial.SerialException as e:
                    self.error_occurred.emit(f"Serial read error: {e}")
                    break
                except OSError as e:
                    self.error_occurred.emit(f"OS error: {e}")
                    break

        except serial.SerialException as e:
            self.error_occurred.emit(f"Failed to open {self._port_name}: {e}")
        except Exception as e:
            self.error_occurred.emit(f"Unexpected error: {e}")
        finally:
            self._close_port()
            self.connection_changed.emit(False)

    def _close_port(self):
        """Safely close the serial port."""
        if self._serial and self._serial.is_open:
            try:
                self._serial.close()
                self.port_info.emit(f"Disconnected from {self._port_name}")
            except Exception:
                pass
        self._serial = None

    def stop(self):
        """Signal the thread to stop and wait for it to finish."""
        self._running = False
        self.wait(3000)  # Wait up to 3 seconds for thread to finish

    def get_statistics(self) -> dict:
        """Return connection statistics."""
        return {
            "port": self._port_name,
            "baudrate": self._baudrate,
            "bytes_read": self._bytes_read,
            "connected": self.is_connected,
            "last_activity": self._last_activity,
        }
