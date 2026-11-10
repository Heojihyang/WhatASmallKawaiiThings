"""Transparent, topmost character window with pixel-accurate dragging."""

from __future__ import annotations

import ctypes
import random
import sys
from ctypes import wintypes

from PySide6.QtCore import QPoint, Qt
from PySide6.QtGui import QCursor, QGuiApplication, QMouseEvent, QPixmap
from PySide6.QtWidgets import QLabel, QWidget

ALPHA_HIT_THRESHOLD = 16
WM_NCHITTEST = 0x0084
HTTRANSPARENT = -1
HTCLIENT = 1
GWL_WNDPROC = -4

if sys.platform == "win32":
    LRESULT = ctypes.c_ssize_t
    WNDPROC = ctypes.WINFUNCTYPE(
        LRESULT,
        wintypes.HWND,
        wintypes.UINT,
        wintypes.WPARAM,
        wintypes.LPARAM,
    )
    ctypes.windll.user32.CallWindowProcW.argtypes = [
        ctypes.c_void_p,
        wintypes.HWND,
        wintypes.UINT,
        wintypes.WPARAM,
        wintypes.LPARAM,
    ]
    ctypes.windll.user32.CallWindowProcW.restype = LRESULT
    ctypes.windll.user32.SetWindowLongPtrW.argtypes = [wintypes.HWND, ctypes.c_int, ctypes.c_void_p]
    ctypes.windll.user32.SetWindowLongPtrW.restype = ctypes.c_void_p


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
        self._old_wndproc: int | None = None
        self._wndproc = None

        self._place(saved_position)

    def character_position(self) -> tuple[int, int]:
        origin = self.frameGeometry().topLeft()
        return origin.x(), origin.y()

    def showEvent(self, event) -> None:
        super().showEvent(event)
        self._install_click_through()

    def nativeEvent(self, event_type, message):
        if sys.platform == "win32" and event_type == b"windows_generic_MSG":
            msg = wintypes.MSG.from_address(int(message))
            if msg.message == WM_NCHITTEST and self._hit_test(self._lparam_point(msg.lParam)) == HTTRANSPARENT:
                return True, HTTRANSPARENT
        return super().nativeEvent(event_type, message)

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

    def closeEvent(self, event) -> None:
        if sys.platform == "win32" and self._old_wndproc:
            ctypes.windll.user32.SetWindowLongPtrW(int(self.winId()), GWL_WNDPROC, self._old_wndproc)
            self._old_wndproc = None
        super().closeEvent(event)

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
        max_x = max(area.left(), area.right() - self.width() + 1)
        max_y = max(area.top(), area.bottom() - self.height() + 1)
        return QPoint(
            min(max(point.x(), area.left()), max_x),
            min(max(point.y(), area.top()), max_y),
        )

    def _opaque_at_client(self, point: QPoint) -> bool:
        ratio = self.devicePixelRatioF()
        x = int(point.x() * ratio)
        y = int(point.y() * ratio)
        if not (0 <= x < self._hit_image.width() and 0 <= y < self._hit_image.height()):
            return False
        return self._hit_image.pixelColor(x, y).alpha() > ALPHA_HIT_THRESHOLD

    def _hit_test(self, screen_point: QPoint) -> int:
        local = self.mapFromGlobal(screen_point)
        if self.rect().contains(local) and self._opaque_at_client(local):
            return HTCLIENT
        return HTTRANSPARENT

    def _install_click_through(self) -> None:
        if sys.platform != "win32" or self._wndproc is not None:
            return
        hwnd = int(self.winId())

        def wndproc(window, message, wparam, lparam):
            if window == hwnd and message == WM_NCHITTEST:
                if self._hit_test(self._lparam_point(lparam)) == HTTRANSPARENT:
                    return HTTRANSPARENT
            return ctypes.windll.user32.CallWindowProcW(
                self._old_wndproc, window, message, wparam, lparam
            )

        self._wndproc = WNDPROC(wndproc)
        self._old_wndproc = ctypes.windll.user32.SetWindowLongPtrW(
            hwnd, GWL_WNDPROC, ctypes.cast(self._wndproc, ctypes.c_void_p).value
        )

    @staticmethod
    def _lparam_point(lparam: int) -> QPoint:
        value = ctypes.c_int32(lparam & 0xFFFFFFFF).value
        return QPoint(ctypes.c_int16(value & 0xFFFF).value, ctypes.c_int16((value >> 16) & 0xFFFF).value)
