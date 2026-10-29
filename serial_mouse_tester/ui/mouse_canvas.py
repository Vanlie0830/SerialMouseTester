"""
Mouse Movement Canvas Widget

Real-time visualization of serial mouse movement trajectory and button states.
"""

from collections import deque
from typing import Optional, Tuple

from PySide6.QtCore import Qt, QPointF, QRectF, Signal
from PySide6.QtGui import (
    QPainter, QPen, QColor, QBrush, QPainterPath, QFont, QRadialGradient,
)
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGroupBox

MAX_TRAIL_POINTS = 5000  # Maximum trail points to display


class MouseCanvas(QWidget):
    """Canvas widget that draws mouse movement trajectory in real-time."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(400, 300)

        # Position tracking
        self._pos_x = 0.0
        self._pos_y = 0.0
        self._trail: deque[Tuple[float, float]] = deque(maxlen=MAX_TRAIL_POINTS)

        # Button states
        self._left_btn = False
        self._right_btn = False
        self._middle_btn = False

        # Visual settings
        self._scale = 2.0  # pixels per unit
        self._center_x = self.width() / 2
        self._center_y = self.height() / 2

        # Background grid
        self._grid_size = 20

    def update_mouse(self, dx: int, dy: int,
                     left: bool, right: bool, middle: bool):
        """Update mouse state and add to trail."""
        self._pos_x += dx * self._scale
        self._pos_y += dy * self._scale

        self._trail.append((self._pos_x, self._pos_y))

        self._left_btn = left
        self._right_btn = right
        self._middle_btn = middle

        self.update()  # Trigger repaint

    def reset_view(self):
        """Reset position and clear trail."""
        self._pos_x = 0.0
        self._pos_y = 0.0
        self._trail.clear()
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w = self.width()
        h = self.height()
        self._center_x = w / 2
        self._center_y = h / 2

        # ── Background ──
        painter.fillRect(self.rect(), QColor("#181825"))

        # ── Grid ──
        grid_pen = QPen(QColor("#313244"), 0.5)
        painter.setPen(grid_pen)
        for x in range(0, w, self._grid_size):
            painter.drawLine(x, 0, x, h)
        for y in range(0, h, self._grid_size):
            painter.drawLine(0, y, w, y)

        # ── Center cross ──
        cross_pen = QPen(QColor("#45475a"), 1, Qt.DashLine)
        painter.setPen(cross_pen)
        painter.drawLine(int(self._center_x), 0, int(self._center_x), h)
        painter.drawLine(0, int(self._center_y), w, int(self._center_y))

        # ── Trail ──
        if len(self._trail) > 1:
            path = QPainterPath()
            first_x, first_y = self._trail[0]
            path.moveTo(self._center_x + first_x, self._center_y + first_y)

            for tx, ty in list(self._trail)[1:]:
                path.lineTo(self._center_x + tx, self._center_y + ty)

            # Trail gradient effect (older = more transparent)
            trail_pen = QPen(QColor("#89b4fa"), 2, Qt.SolidLine, Qt.RoundCap)
            painter.setPen(trail_pen)
            painter.drawPath(path)

        # ── Current position dot ──
        dot_x = self._center_x + self._pos_x
        dot_y = self._center_y + self._pos_y

        # Glow effect
        glow = QRadialGradient(dot_x, dot_y, 15)
        if self._left_btn or self._right_btn or self._middle_btn:
            glow.setColorAt(0, QColor("#f38ba8"))
            glow.setColorAt(1, QColor("#f38ba8", 0))
        else:
            glow.setColorAt(0, QColor("#a6e3a1"))
            glow.setColorAt(1, QColor("#a6e3a1", 0))
        painter.setBrush(QBrush(glow))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(QPointF(dot_x, dot_y), 15, 15)

        # Core dot
        dot_color = QColor("#f38ba8") if (self._left_btn or self._right_btn) else QColor("#a6e3a1")
        painter.setBrush(QBrush(dot_color))
        painter.setPen(QPen(QColor("#cdd6f4"), 1))
        painter.drawEllipse(QPointF(dot_x, dot_y), 5, 5)

        # ── Position label ──
        painter.setPen(QPen(QColor("#a6adc8"), 1))
        font = QFont("Consolas", 9)
        painter.setFont(font)
        painter.drawText(10, h - 10,
                         f"X: {self._pos_x:+.0f}  Y: {self._pos_y:+.0f}")

        painter.end()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._center_x = self.width() / 2
        self._center_y = self.height() / 2


class MouseVisualizerPanel(QWidget):
    """Complete mouse visualization panel with canvas and button indicators."""

    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        # Header
        header = QLabel("🖱 Mouse Trajectory")
        header.setStyleSheet("""
            QLabel {
                font-size: 14px;
                font-weight: bold;
                color: #cdd6f4;
                padding: 4px;
            }
        """)

        # Canvas
        self._canvas = MouseCanvas()

        # Button indicators
        btn_group = QGroupBox("Button States")
        btn_group.setStyleSheet("""
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
        """)

        btn_layout = QHBoxLayout(btn_group)

        self._lbl_left = self._create_button_label("Left (L)")
        self._lbl_middle = self._create_button_label("Middle (M)")
        self._lbl_right = self._create_button_label("Right (R)")

        btn_layout.addWidget(self._lbl_left)
        btn_layout.addWidget(self._lbl_middle)
        btn_layout.addWidget(self._lbl_right)

        # Position info
        self._lbl_pos = QLabel("Position: (0, 0)")
        self._lbl_pos.setStyleSheet("color: #a6adc8; font-size: 11px; padding: 2px;")

        layout.addWidget(header)
        layout.addWidget(self._canvas, stretch=1)
        layout.addWidget(btn_group)
        layout.addWidget(self._lbl_pos)

    def _create_button_label(self, text: str) -> QLabel:
        label = QLabel(f"  {text}  ")
        label.setAlignment(Qt.AlignCenter)
        label.setFixedHeight(36)
        self._set_button_style(label, False)
        return label

    def _set_button_style(self, label: QLabel, active: bool):
        if active:
            label.setStyleSheet("""
                QLabel {
                    background-color: #f38ba8;
                    color: #1e1e2e;
                    border: 2px solid #f38ba8;
                    border-radius: 8px;
                    font-size: 12px;
                    font-weight: bold;
                    padding: 4px;
                }
            """)
        else:
            label.setStyleSheet("""
                QLabel {
                    background-color: #313244;
                    color: #6c7086;
                    border: 2px solid #45475a;
                    border-radius: 8px;
                    font-size: 12px;
                    padding: 4px;
                }
            """)

    def update_mouse(self, dx: int, dy: int,
                     left: bool, right: bool, middle: bool):
        """Update the visualization with new mouse state."""
        self._canvas.update_mouse(dx, dy, left, right, middle)

        self._set_button_style(self._lbl_left, left)
        self._set_button_style(self._lbl_middle, middle)
        self._set_button_style(self._lbl_right, right)

    def reset(self):
        """Reset the canvas and button states."""
        self._canvas.reset_view()
        self._set_button_style(self._lbl_left, False)
        self._set_button_style(self._lbl_middle, False)
        self._set_button_style(self._lbl_right, False)
        self._lbl_pos.setText("Position: (0, 0)")
