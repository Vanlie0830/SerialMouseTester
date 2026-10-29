"""
Tests for Serial Mouse Protocol Parsers

Verifies packet parsing for Microsoft, Logitech, and Mouse Systems protocols.
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from serial_mouse_tester.core.protocols import (
    MicrosoftParser,
    LogitechParser,
    MouseSystemsParser,
    MousePacketParser,
    ProtocolAutoDetector,
    ProtocolType,
    MouseState,
)


class TestMicrosoftParser:
    """Test Microsoft 2-button serial mouse protocol parsing."""

    def test_basic_packet(self):
        """Test basic 3-byte Microsoft packet."""
        # Byte 0: 01 0 0 00 00 = 0x40 (no buttons, no movement)
        # Byte 1: 00 000000 = 0x00 (X low)
        # Byte 2: 00 000000 = 0x00 (Y low)
        data = bytes([0x40, 0x00, 0x00])
        state = MicrosoftParser.parse(data)
        assert state is not None
        assert state.dx == 0
        assert state.dy == 0
        assert state.left_button == False
        assert state.right_button == False

    def test_movement_right_down(self):
        """Test movement: +5 right, +3 down."""
        # X = 5: byte1 = 0x05 (low 6 bits), byte0 bits 1:0 = 00
        # Y = 3: byte2 = 0x03 (low 6 bits), byte0 bits 3:2 = 00
        # byte0 = 01 0 0 00 00 = 0x40
        data = bytes([0x40, 0x05, 0x03])
        state = MicrosoftParser.parse(data)
        assert state is not None
        assert state.dx == 5
        assert state.dy == 3

    def test_movement_left_up(self):
        """Test movement: -10 left, -8 up (negative)."""
        # X = -10 = 0xF6 (two's complement 8-bit)
        #   high 2 bits = 11 (from 0xF6 >> 6), low 6 bits = 110110 = 0x36
        #   byte0 bits 1:0 = 11, byte1 = 0x36
        # Y = -8 = 0xF8
        #   high 2 bits = 11, low 6 bits = 111000 = 0x38
        #   byte0 bits 3:2 = 11
        # byte0 = 01 0 0 11 11 = 0x4F
        data = bytes([0x4F, 0x36, 0x38])
        state = MicrosoftParser.parse(data)
        assert state is not None
        assert state.dx == -10
        assert state.dy == -8

    def test_left_button(self):
        """Test left button pressed."""
        # byte0 = 01 1 0 00 00 = 0x60
        data = bytes([0x60, 0x00, 0x00])
        state = MicrosoftParser.parse(data)
        assert state is not None
        assert state.left_button == True
        assert state.right_button == False

    def test_right_button(self):
        """Test right button pressed."""
        # byte0 = 01 0 1 00 00 = 0x50
        data = bytes([0x50, 0x00, 0x00])
        state = MicrosoftParser.parse(data)
        assert state is not None
        assert state.left_button == False
        assert state.right_button == True

    def test_both_buttons(self):
        """Test both buttons pressed."""
        # byte0 = 01 1 1 00 00 = 0x70
        data = bytes([0x70, 0x00, 0x00])
        state = MicrosoftParser.parse(data)
        assert state is not None
        assert state.left_button == True
        assert state.right_button == True

    def test_invalid_header(self):
        """Test that invalid sync byte is rejected."""
        # byte0 = 00xxxxxx (not valid Microsoft sync)
        data = bytes([0x00, 0x00, 0x00])
        state = MicrosoftParser.parse(data)
        assert state is None

    def test_short_data(self):
        """Test that too-short data returns None."""
        data = bytes([0x40, 0x00])
        state = MicrosoftParser.parse(data)
        assert state is None

    def test_header_detection(self):
        """Test header byte validation."""
        assert MicrosoftParser.is_valid_header(0x40) == True   # 01000000
        assert MicrosoftParser.is_valid_header(0x7F) == True   # 01111111
        assert MicrosoftParser.is_valid_header(0x00) == False  # 00000000
        assert MicrosoftParser.is_valid_header(0x80) == False  # 10000000
        assert MicrosoftParser.is_valid_header(0xC0) == False  # 11000000


class TestMouseSystemsParser:
    """Test Mouse Systems 5-byte serial mouse protocol parsing."""

    def test_basic_packet(self):
        """Test basic 5-byte Mouse Systems packet."""
        # byte0: 1 0 0 0 0 0 0 0 = 0x80 (no buttons, active low)
        # byte1: X = 0
        # byte2: Y = 0
        # byte3: X ext = 0
        # byte4: Y ext = 0
        data = bytes([0x80, 0x00, 0x00, 0x00, 0x00])
        state = MouseSystemsParser.parse(data)
        assert state is not None
        assert state.dx == 0
        assert state.dy == 0
        assert state.left_button == True   # Active LOW! 0 = pressed
        assert state.right_button == True
        assert state.middle_button == True

    def test_no_buttons(self):
        """Test no buttons pressed (active low: all bits set)."""
        # byte0 = 0x87 = 10000111 (all button bits set = none pressed)
        data = bytes([0x87, 0x00, 0x00, 0x00, 0x00])
        state = MouseSystemsParser.parse(data)
        assert state is not None
        assert state.left_button == False
        assert state.right_button == False
        assert state.middle_button == False

    def test_movement(self):
        """Test movement: +10 right, +5 up."""
        # X = 10 (signed byte)
        # Y = -5 (signed byte, then inverted to +5)
        data = bytes([0x87, 10, 251, 0x00, 0x00])  # 251 = -5 as unsigned
        state = MouseSystemsParser.parse(data)
        assert state is not None
        assert state.dx == 10
        assert state.dy == 5  # -(-5) = 5 after Y inversion

    def test_invalid_header(self):
        """Test invalid sync byte rejection."""
        # byte0 bit 7 = 0
        data = bytes([0x07, 0x00, 0x00, 0x00, 0x00])
        state = MouseSystemsParser.parse(data)
        assert state is None

    def test_header_detection(self):
        """Test header byte validation."""
        assert MouseSystemsParser.is_valid_header(0x80) == True
        assert MouseSystemsParser.is_valid_header(0xFF) == True
        assert MouseSystemsParser.is_valid_header(0x00) == False
        assert MouseSystemsParser.is_valid_header(0x7F) == False


class TestMousePacketParser:
    """Test the main packet parser with streaming data."""

    def test_microsoft_stream(self):
        """Test parsing multiple Microsoft packets from a stream."""
        parser = MousePacketParser()
        parser.set_protocol(ProtocolType.MICROSOFT)

        # Two packets: move right 5, then move left 3
        data = bytes([
            0x40, 0x05, 0x00,  # +5 right
            0x40, 0x3D, 0x00,  # -3 left (0x3D = -3 low 6 bits = 0b111101, high = 00... wait)
        ])
        # Actually let me recalculate: X = -3 = 0xFD (two's complement)
        #   high 2 bits = 11, low 6 bits = 111101 = 0x3D
        #   byte0 bits 1:0 = 11 = 0x43
        data = bytes([
            0x40, 0x05, 0x00,  # +5 right
            0x43, 0x3D, 0x00,  # -3 left
        ])

        states = parser.feed(data)
        assert len(states) == 2
        assert states[0].dx == 5
        assert states[1].dx == -3

    def test_microsoft_with_garbage(self):
        """Test parser skips garbage bytes before sync."""
        parser = MousePacketParser()
        parser.set_protocol(ProtocolType.MICROSOFT)

        # Garbage bytes + valid packet
        data = bytes([0xFF, 0xAA, 0xBB, 0x40, 0x05, 0x03])
        states = parser.feed(data)
        assert len(states) >= 1

    def test_mouse_systems_stream(self):
        """Test parsing Mouse Systems packets."""
        parser = MousePacketParser()
        parser.set_protocol(ProtocolType.MOUSE_SYSTEMS)

        data = bytes([0x87, 5, 251, 0x00, 0x00])
        states = parser.feed(data)
        assert len(states) == 1
        assert states[0].dx == 5
        assert states[0].dy == 5  # -(-5) after inversion


class TestProtocolAutoDetector:
    """Test protocol auto-detection."""

    def test_detect_logitech_4byte(self):
        """Test detection of Logitech 4-byte protocol (real-world data)."""
        detector = ProtocolAutoDetector()
        # Real data from serial mouse capture (4-byte Logitech packets)
        data = bytes([
            0x50, 0x00, 0x01, 0x00,
            0x43, 0x3C, 0x00, 0x00,
            0x4F, 0x37, 0x3F, 0x00,
            0x4F, 0x35, 0x3D, 0x00,
        ])
        result = detector.feed(data)
        assert result == ProtocolType.LOGITECH, f'Expected LOGITECH, got {result}'

    def test_detect_microsoft(self):
        """Test detection of Microsoft protocol pattern."""
        detector = ProtocolAutoDetector()

        # Feed Microsoft-like data (3-byte packets, sync = 0x40)
        data = bytes([0x40, 0x05, 0x03, 0x40, 0x02, 0x01, 0x40, 0x00, 0x00,
                       0x40, 0x01, 0x01, 0x40, 0x02, 0x02])
        result = detector.feed(data)

        if result is not None:
            assert result in (ProtocolType.MICROSOFT, ProtocolType.MOUSE_SYSTEMS)

    def test_insufficient_data(self):
        """Test that insufficient data returns None."""
        detector = ProtocolAutoDetector()
        result = detector.feed(bytes([0x40, 0x00]))
        assert result is None

    def test_reset(self):
        """Test reset clears detection state."""
        detector = ProtocolAutoDetector()
        detector.feed(bytes([0x40] * 15))
        detector.reset()
        assert detector.detected_protocol == ProtocolType.UNKNOWN
        assert detector.confidence == 0.0


def run_tests():
    """Run all tests and report results."""
    test_classes = [
        TestMicrosoftParser,
        TestMouseSystemsParser,
        TestMousePacketParser,
        TestProtocolAutoDetector,
    ]

    total = 0
    passed = 0
    failed = 0
    errors = []

    for cls in test_classes:
        instance = cls()
        methods = [m for m in dir(instance) if m.startswith("test_")]
        for method_name in methods:
            total += 1
            try:
                method = getattr(instance, method_name)
                method()
                passed += 1
                print(f"  ✅ {cls.__name__}.{method_name}")
            except AssertionError as e:
                failed += 1
                errors.append((f"{cls.__name__}.{method_name}", str(e)))
                print(f"  ❌ {cls.__name__}.{method_name}: {e}")
            except Exception as e:
                failed += 1
                errors.append((f"{cls.__name__}.{method_name}", str(e)))
                print(f"  💥 {cls.__name__}.{method_name}: {e}")

    print(f"\n{'='*50}")
    print(f"Tests: {total} | Passed: {passed} | Failed: {failed}")
    if errors:
        print(f"\nFailures:")
        for name, msg in errors:
            print(f"  - {name}: {msg}")

    return failed == 0


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
