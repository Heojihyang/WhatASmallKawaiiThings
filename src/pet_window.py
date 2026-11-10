"""Transparent, topmost character window with pixel-accurate dragging."""

from __future__ import annotations

import random
import sys

from PySide6.QtCore import QPoint, Qt
from PySide6.QtGui import QCursor, QGuiApplication, QMouseEvent, QPixmap
from PySide6.QtWidgets import QLabel, QWidget

ALPHA_HIT_THRESHOLD = 16


class PetWindow(QWidget):
    def __init__(self, image: QPixmap, saved_position: tuple[int, int] | None) -> None:
        super().__init__(
            None,
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.Tool
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.NoDropShadowWindowHint,
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        self._image = image
        self._hit_image = image.toImage()
        self._label = QLabel(self)
        self._label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self._label.setPixmap(image)
        self._label.setFixedSize(image.size())
        self.setFixedSize(image.size())
        self._drag_offset: QPoint | None = None

        self._place(saved_position)

    def character_position(self) -> tuple[int, int]:
        origin = self.frameGeometry().topLeft()
        return origin.x(), origin.y()

    def showEvent(self, event) -> None:
        super().showEvent(event)
        self._apply_input_region()

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.RightButton:
            self.close()
            return
        if event.button() != Qt.MouseButton.LeftButton:
            event.ignore()
            return
        self._drag_offset = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
        event.accept()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self._drag_offset is None or not (event.buttons() & Qt.MouseButton.LeftButton):
            event.ignore()
            return
        target = event.globalPosition().toPoint() - self._drag_offset
        self.move(self._clamp(target))
        event.accept()

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        self._drag_offset = None
        event.accept()

    def _place(self, saved_position: tuple[int, int] | None) -> None:
        if saved_position is not None:
            self.move(self._clamp(QPoint(*saved_position)))
            return
        screen = QGuiApplication.screenAt(QCursor.pos()) or QGuiApplication.primaryScreen()
        area = screen.availableGeometry()
        max_x = max(area.left(), area.right() - self.width() + 1)
        max_y = max(area.top(), area.bottom() - self.height() + 1)
        self.move(
            self._clamp(
                QPoint(
                    random.randint(area.left(), max_x),
                    random.randint(area.top(), max_y),
                )
            )
        )

    def _clamp(self, point: QPoint) -> QPoint:
        anchor = point + QPoint(max(0, self.width() // 2), max(0, self.height() // 2))
        screen = QGuiApplication.screenAt(anchor)
        if screen is None:
            screen = QGuiApplication.screenAt(QCursor.pos()) or QGuiApplication.primaryScreen()
        area = screen.availableGeometry()
        max_x = area.right() - self.width() + 1
        max_y = area.bottom() - self.height() + 1
        if max_x < area.left():
            max_x = area.left()
        if max_y < area.top():
            max_y = area.top()
        return QPoint(
            min(max(point.x(), area.left()), max_x),
            min(max(point.y(), area.top()), max_y),
        )

    def _apply_input_region(self) -> None:
        """Limit both painting and mouse input to opaque character pixels on Windows."""
        if sys.platform != "win32":
            return

        import ctypes

        width = self._hit_image.width()
        height = self._hit_image.height()
        gdi32 = ctypes.windll.gdi32
        user32 = ctypes.windll.user32
        region = gdi32.CreateRectRgn(0, 0, 0, 0)
        try:
            for y in range(height):
                start = None
                for x in range(width + 1):
                    opaque = (
                        x < width
                        and self._hit_image.pixelColor(x, y).alpha() > ALPHA_HIT_THRESHOLD
                    )
                    if opaque and start is None:
                        start = x
                    elif not opaque and start is not None:
                        row = gdi32.CreateRectRgn(start, y, x, y + 1)
                        gdi32.CombineRgn(region, region, row, 2)  # RGN_OR
                        gdi32.DeleteObject(row)
                        start = None
            # SetWindowRgn takes ownership of the region when it succeeds.
            if not user32.SetWindowRgn(int(self.winId()), region, True):
                raise OSError("SetWindowRgn failed")
            region = None
        finally:
            if region:
                gdi32.DeleteObject(region)
