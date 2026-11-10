"""External character image loading."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtGui import QImage, QPixmap


ROOT = Path(__file__).resolve().parent.parent
CHARACTER_PATH = ROOT / "assets" / "images" / "rakko.png"


class ResourceError(RuntimeError):
    pass


def load_character_image() -> QPixmap:
    if not CHARACTER_PATH.is_file():
        raise ResourceError(f"캐릭터 이미지가 없습니다: {CHARACTER_PATH}")

    image = QImage(str(CHARACTER_PATH))
    if image.isNull():
        raise ResourceError(f"캐릭터 이미지를 열 수 없습니다: {CHARACTER_PATH}")
    if image.format() != QImage.Format.Format_ARGB32_Premultiplied:
        image = image.convertToFormat(QImage.Format.Format_ARGB32_Premultiplied)
    return QPixmap.fromImage(image)
