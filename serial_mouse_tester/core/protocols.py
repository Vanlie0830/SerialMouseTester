"""
Serial Mouse Protocol Definitions & Parser

Supports three classic serial mouse protocols with auto-detection:

1. **Microsoft Serial Mouse (2-button)**
   - Baud: 1200, 7N1 (7 data bits, no parity, 1 stop bit)
   - Packet: 3 bytes
     - Byte 0: `01LRYYXX`  (sync=01, L/R buttons, high bits of Y/X delta)
     - Byte 1: `00XXXXXX`  (low 6 bits of X delta)
     - Byte 2: `00YYYYYY`  (low 6 bits of Y delta)

2. **Logitech 3-Button Mouse**
   - Same as Microsoft but sends a 4th byte when middle button state changes
   - Byte 3: `00M00000`  (bit 5 = middle button state)

3. **Mouse Systems (5-byte)**
   - Baud: 1200 or 9600, 8N1 (8 data bits, no parity, 1 stop bit)
   - Packet: 5 bytes
     - Byte 0: `1000MRL?`  (sync=1, middle/right/left buttons, active LOW)
     - Byte 1: X delta (signed 8-bit)
     - Byte 2: Y delta (signed 8-bit, inverted)
     - Byte 3: X delta extension (usually 0)
     - Byte 4: Y delta extension (usually 0)
"""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional, List, Tuple


class ProtocolType(Enum):
    """Supported serial mouse protocol types."""
    MICROSOFT = auto()
    LOGITECH = auto()
    MOUSE_SYSTEMS = auto()
    UNKNOWN = auto()

    def __str__(self) -> str:
        return self.name.replace("_", " ").title()


@dataclass
class MouseState:
    """Parsed mouse state from a complete packet."""
    dx: int = 0
    dy: int = 0
    left_button: bool = False
    right_button: bool = False
    middle_button: bool = False
    protocol: ProtocolType = ProtocolType.UNKNOWN
    raw_bytes: bytes = field(default_factory=bytes)
    timestamp: float = 0.0

    def has_movement(self) -> bool:
        return self.dx != 0 or self.dy != 0

    def buttons_str(self) -> str:
        parts = []
        if self.left_button:
            parts.append("L")
        if self.middle_button:
            parts.append("M")
        if self.right_button:
            parts.append("R")
        return "+".join(parts) if parts else "-"


@dataclass
class ProtocolConfig:
    """Serial port configuration for a protocol."""
    baudrate: int
    bytesize: int
    parity: str
    stopbits: float
    label: str


# Protocol serial port configurations
PROTOCOL_CONFIGS = {
    ProtocolType.MICROSOFT: ProtocolConfig(
        baudrate=1200, bytesize=7, parity="N", stopbits=1,
        label="Microsoft 2-Button (1200, 7N1)"
    ),
    ProtocolType.LOGITECH: ProtocolConfig(
        baudrate=1200, bytesize=7, parity="N", stopbits=1,
        label="Logitech 3-Button (1200, 7N1)"
    ),
    ProtocolType.MOUSE_SYSTEMS: ProtocolConfig(
        baudrate=1200, bytesize=8, parity="N", stopbits=1,
        label="Mouse Systems 5-Byte (1200, 8N1)"
    ),
}


class MicrosoftParser:
    """Parser for Microsoft 2-button serial mouse protocol."""

    PACKET_SIZE = 3

    @staticmethod
    def is_valid_header(b: int) -> bool:
        # Byte 1: 01xxxxxx (bits 7-6 must be 01)
        return (b & 0xC0) == 0x40

    @classmethod
    def parse(cls, data: bytes) -> Optional[MouseState]:
        if len(data) < cls.PACKET_SIZE:
            return None
        b0, b1, b2 = data[0], data[1], data[2]

        if not cls.is_valid_header(b0):
            return None

        # Buttons (active high)
        left = bool(b0 & 0x20)
        right = bool(b0 & 0x10)

        # X delta: bits 1:0 of byte0 (high 2 bits) + byte1 (low 6 bits)
        dx = ((b0 & 0x03) << 6) | (b1 & 0x3F)
        if dx > 127:
            dx -= 256  # sign-extend from 8-bit

        # Y delta: bits 3:2 of byte0 (high 2 bits) + byte2 (low 6 bits)
        dy = ((b0 & 0x0C) << 4) | (b2 & 0x3F)
        if dy > 127:
            dy -= 256  # sign-extend from 8-bit

        return MouseState(
            dx=dx, dy=dy,
            left_button=left, right_button=right,
            protocol=ProtocolType.MICROSOFT,
            raw_bytes=data[:cls.PACKET_SIZE],
        )


class LogitechParser:
    """
    Parser for Logitech 3-button serial mouse protocol.

    Logitech extends Microsoft protocol: normally 3-byte packets,
    but a 4th byte `0x20` or `0x00` (middle button state) is sent
    when the middle button state changes.
    """

    MICROSOFT_PACKET = 3
    MIDDLE_BUTTON_PACKET = 1  # additional byte for middle button

    def __init__(self):
        self._middle_button = False

    def is_valid_header(self, b: int) -> bool:
        return (b & 0xC0) == 0x40

    def parse(self, data: bytes) -> Optional[MouseState]:
        """Parse incoming data. May consume 3 or 4 bytes."""
        if len(data) < self.MICROSOFT_PACKET:
            return None

        b0 = data[0]
        if not self.is_valid_header(b0):
            return None

        # Parse as Microsoft first
        state = MicrosoftParser.parse(data)
        if state is None:
            return None

        state.protocol = ProtocolType.LOGITECH

        # Check if there's a 4th byte (middle button update)
        if len(data) >= 4:
            b3 = data[3]
            # Logitech middle button byte: 0x20 = pressed, 0x00 = released
            # (bit 5 set when middle button pressed)
            self._middle_button = bool(b3 & 0x20)

        state.middle_button = self._middle_button
        return state

    @property
    def bytes_consumed(self) -> List[int]:
        return [self.MICROSOFT_PACKET, self.MICROSOFT_PACKET + 1]


class MouseSystemsParser:
    """Parser for Mouse Systems 5-byte serial mouse protocol."""

    PACKET_SIZE = 5

    @staticmethod
    def is_valid_header(b: int) -> bool:
        # Byte 1: 1xxxxxxx (bit 7 must be 1)
        return (b & 0x80) != 0

    @classmethod
    def parse(cls, data: bytes) -> Optional[MouseState]:
        if len(data) < cls.PACKET_SIZE:
            return None
        b0 = data[0]

        if not cls.is_valid_header(b0):
            return None

        # Buttons are active LOW in Mouse Systems protocol
        left = not bool(b0 & 0x01)
        right = not bool(b0 & 0x02)
        middle = not bool(b0 & 0x04)

        # X delta: signed 8-bit from byte 1
        dx = data[1] if data[1] < 128 else data[1] - 256

        # Y delta: signed 8-bit from byte 2, inverted (Y grows downward in serial)
        dy = data[2] if data[2] < 128 else data[2] - 256
        dy = -dy  # invert Y axis

        return MouseState(
            dx=dx, dy=dy,
            left_button=left, right_button=right, middle_button=middle,
            protocol=ProtocolType.MOUSE_SYSTEMS,
            raw_bytes=data[:cls.PACKET_SIZE],
        )


class ProtocolAutoDetector:
    """
    Auto-detect serial mouse protocol from incoming byte stream.

    Strategy:
    1. Analyze first N bytes to determine protocol
    2. Microsoft/Logitech: byte pattern `01xxxxxx` repeated every 3 bytes
    3. Mouse Systems: byte pattern `1xxxxxxx` repeated every 5 bytes
    """

    MIN_BYTES_FOR_DETECTION = 15  # ~5 packets to be confident

    def __init__(self):
        self._buffer = bytearray()
        self._detected_protocol: ProtocolType = ProtocolType.UNKNOWN
        self._confidence = 0.0

    @property
    def detected_protocol(self) -> ProtocolType:
        return self._detected_protocol

    @property
    def confidence(self) -> float:
        return self._confidence

    def feed(self, data: bytes) -> Optional[ProtocolType]:
        """
        Feed raw bytes and attempt protocol detection.
        Returns ProtocolType when detection is confident, else None.
        """
        self._buffer.extend(data)

        if self._detected_protocol != ProtocolType.UNKNOWN:
            return self._detected_protocol

        if len(self._buffer) < self.MIN_BYTES_FOR_DETECTION:
            return None

        # Score all three protocols
        ms_score = self._score_mouse_systems()
        msft_score = self._score_microsoft()
        logi_score = self._score_logitech()

        # Pick the highest score above threshold (0.7)
        best_score = max(ms_score, msft_score, logi_score)

        if best_score < 0.7:
            return None

        if logi_score >= msft_score and logi_score >= ms_score and logi_score > 0.7:
            self._detected_protocol = ProtocolType.LOGITECH
            self._confidence = logi_score
        elif msft_score >= ms_score and msft_score > 0.7:
            self._detected_protocol = ProtocolType.MICROSOFT
            self._confidence = msft_score
        elif ms_score > 0.7:
            self._detected_protocol = ProtocolType.MOUSE_SYSTEMS
            self._confidence = ms_score

        return self._detected_protocol if self._detected_protocol != ProtocolType.UNKNOWN else None

    def _score_mouse_systems(self) -> float:
        """Score how well the buffer matches Mouse Systems pattern (5-byte, bit7=1)."""
        if len(self._buffer) < 15:
            return 0.0
        score = 0
        total = 0
        for i in range(0, min(len(self._buffer), 25), 5):
            if i < len(self._buffer):
                total += 1
                if self._buffer[i] & 0x80:
                    score += 1
        return score / max(total, 1)

    def _score_microsoft(self) -> float:
        """Score how well the buffer matches Microsoft pattern (3-byte, bits7-6=01)."""
        if len(self._buffer) < 15:
            return 0.0
        score = 0
        total = 0
        for i in range(0, min(len(self._buffer), 27), 3):
            if i < len(self._buffer):
                total += 1
                if (self._buffer[i] & 0xC0) == 0x40:
                    score += 1
        return score / max(total, 1)

    def _score_logitech(self) -> float:
        """
        Score how well the buffer matches Logitech pattern (4-byte, bits7-6=01 every 4 bytes).
        Logitech = Microsoft 3-byte + 1 middle-button byte = 4-byte packets.
        """
        if len(self._buffer) < 16:
            return 0.0
        score = 0
        total = 0
        for i in range(0, min(len(self._buffer), 32), 4):
            if i < len(self._buffer):
                total += 1
                if (self._buffer[i] & 0xC0) == 0x40:
                    score += 1
        return score / max(total, 1)

    def reset(self):
        """Reset detection state."""
        self._buffer.clear()
        self._detected_protocol = ProtocolType.UNKNOWN
        self._confidence = 0.0


class MousePacketParser:
    """
    Main packet parser that handles all supported protocols.
    Maintains state across packets (especially for Logitech middle button).
    """

    def __init__(self):
        self._protocol: ProtocolType = ProtocolType.UNKNOWN
        self._buffer = bytearray()
        self._logitech_parser = LogitechParser()
        self._auto_detector = ProtocolAutoDetector()
        self._middle_button = False

    @property
    def protocol(self) -> ProtocolType:
        return self._protocol

    @protocol.setter
    def protocol(self, value: ProtocolType):
        self._protocol = value
        self._buffer.clear()

    def set_protocol(self, protocol: ProtocolType):
        """Manually set the protocol (bypasses auto-detection)."""
        self._protocol = protocol
        self._buffer.clear()
        self._auto_detector.reset()

    def feed(self, data: bytes) -> List[MouseState]:
        """
        Feed raw serial data and return parsed mouse states.
        Returns a list because multiple packets may be in one read.
        """
        self._buffer.extend(data)
        results = []

        # Auto-detection phase
        if self._protocol == ProtocolType.UNKNOWN:
            detected = self._auto_detector.feed(data)
            if detected is not None:
                self._protocol = detected
                self._buffer.clear()
                self._buffer.extend(data)  # re-process with known protocol
            else:
                return results  # still detecting

        # Parse according to protocol
        while True:
            state = self._parse_next_packet()
            if state is None:
                break
            state.timestamp = __import__("time").time()
            results.append(state)

        return results

    def _parse_next_packet(self) -> Optional[MouseState]:
        if self._protocol == ProtocolType.MICROSOFT:
            return self._parse_microsoft()
        elif self._protocol == ProtocolType.LOGITECH:
            return self._parse_logitech()
        elif self._protocol == ProtocolType.MOUSE_SYSTEMS:
            return self._parse_mouse_systems()
        return None

    def _parse_microsoft(self) -> Optional[MouseState]:
        need = MicrosoftParser.PACKET_SIZE
        if len(self._buffer) < need:
            return None

        # Find sync byte (01xxxxxx)
        sync_idx = -1
        for i in range(min(len(self._buffer), need * 2)):
            if MicrosoftParser.is_valid_header(self._buffer[i]):
                sync_idx = i
                break

        if sync_idx == -1:
            # Discard garbage
            self._buffer.clear()
            return None

        if sync_idx > 0:
            self._buffer = self._buffer[sync_idx:]  # discard garbage before sync

        if len(self._buffer) < need:
            return None

        state = MicrosoftParser.parse(bytes(self._buffer[:need]))
        if state is not None:
            self._buffer = self._buffer[need:]
            return state
        else:
            # Bad packet, skip 1 byte and retry
            self._buffer = self._buffer[1:]
            return None

    def _parse_logitech(self) -> Optional[MouseState]:
        need = MicrosoftParser.PACKET_SIZE
        if len(self._buffer) < need:
            return None

        # Find sync byte
        sync_idx = -1
        for i in range(min(len(self._buffer), need * 2)):
            if MicrosoftParser.is_valid_header(self._buffer[i]):
                sync_idx = i
                break

        if sync_idx == -1:
            self._buffer.clear()
            return None

        if sync_idx > 0:
            self._buffer = self._buffer[sync_idx:]

        if len(self._buffer) < need:
            return None

        # Check if 4th byte might be a middle-button update
        total_need = need
        if len(self._buffer) >= need + 1:
            b3 = self._buffer[need]
            # Logitech middle byte: upper bits are 0, bit 5 is middle button
            if (b3 & 0xC0) == 0x00:  # Not a sync byte → likely middle button byte
                total_need = need + 1
                self._middle_button = bool(b3 & 0x20)

        state = MicrosoftParser.parse(bytes(self._buffer[:need]))
        if state is not None:
            state.protocol = ProtocolType.LOGITECH
            state.middle_button = self._middle_button
            self._buffer = self._buffer[total_need:]
            return state
        else:
            self._buffer = self._buffer[1:]
            return None

    def _parse_mouse_systems(self) -> Optional[MouseState]:
        need = MouseSystemsParser.PACKET_SIZE
        if len(self._buffer) < need:
            return None

        # Find sync byte (bit 7 = 1)
        sync_idx = -1
        for i in range(min(len(self._buffer), need * 2)):
            if MouseSystemsParser.is_valid_header(self._buffer[i]):
                sync_idx = i
                break

        if sync_idx == -1:
            self._buffer.clear()
            return None

        if sync_idx > 0:
            self._buffer = self._buffer[sync_idx:]

        if len(self._buffer) < need:
            return None

        state = MouseSystemsParser.parse(bytes(self._buffer[:need]))
        if state is not None:
            self._buffer = self._buffer[need:]
            return state
        else:
            self._buffer = self._buffer[1:]
            return None

    def reset(self):
        """Reset parser state."""
        self._protocol = ProtocolType.UNKNOWN
        self._buffer.clear()
        self._auto_detector.reset()
        self._middle_button = False
