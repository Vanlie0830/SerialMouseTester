#!/usr/bin/env python3
"""
Serial Mouse Tester - Entry Point
A modern serial mouse testing tool with protocol auto-detection.
"""
import sys
import os

# Ensure the package is importable
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from serial_mouse_tester.ui.main_window import main

if __name__ == "__main__":
    sys.exit(main())
