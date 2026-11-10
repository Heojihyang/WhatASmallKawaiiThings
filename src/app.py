"""Desktop pet application entry."""

from __future__ import annotations

import sys

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from src.pet_window import PetWindow
from src.resources import load_character_image
from src.state import load_position, save_position


def run() -> int:
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(True)

    image = load_character_image()
    window = PetWindow(image, load_position())

    def persist() -> None:
        save_position(window.character_position())

    app.aboutToQuit.connect(persist)
    window.show()
    return app.exec()
