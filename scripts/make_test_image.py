"""Create the temporary character PNG used until the Rakko art is supplied."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QColor, QImage, QPainter, QPainterPath, QPen


def main() -> None:
    size = 220
    image = QImage(size, size, QImage.Format.Format_ARGB32)
    image.fill(Qt.GlobalColor.transparent)

    painter = QPainter(image)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    body = QPainterPath()
    body.addEllipse(QPointF(110, 118), 72, 64)
    painter.fillPath(body, QColor("#f4e7c8"))
    painter.setPen(QPen(QColor("#8d6a45"), 4))
    painter.drawPath(body)

    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QColor("#5b4636"))
    painter.drawEllipse(78, 104, 14, 18)
    painter.drawEllipse(128, 104, 14, 18)
    painter.setBrush(QColor("#e39a78"))
    painter.drawEllipse(96, 128, 28, 18)
    painter.end()

    destination = Path(__file__).resolve().parent.parent / "assets" / "images" / "rakko.png"
    destination.parent.mkdir(parents=True, exist_ok=True)
    if not image.save(str(destination), "PNG"):
        raise SystemExit(f"이미지를 저장하지 못했습니다: {destination}")


if __name__ == "__main__":
    main()
