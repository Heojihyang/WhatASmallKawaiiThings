"""External character image loading."""

from __future__ import annotations

import base64
import binascii
from pathlib import Path

from PySide6.QtGui import QImage, QPixmap


ROOT = Path(__file__).resolve().parent.parent
IMAGE_DIR = ROOT / "assets" / "images"
CHARACTER_PATH = IMAGE_DIR / "rakko.png"
CHARACTER_SOURCE = IMAGE_DIR / "rakko.png.b64"


class ResourceError(RuntimeError):
    pass


def ensure_character_image() -> Path:
    """Restore rakko.png from its verified text source when the binary is absent."""
    if CHARACTER_PATH.is_file():
        return CHARACTER_PATH
    if not CHARACTER_SOURCE.is_file():
        raise ResourceError(f"캐릭터 이미지가 없습니다: {CHARACTER_PATH}")
    try:
        encoded = "".join(CHARACTER_SOURCE.read_text(encoding="ascii").split())
        data = base64.b64decode(encoded, validate=True)
    except (OSError, binascii.Error, UnicodeError) as error:
        raise ResourceError(f"캐릭터 이미지를 복원할 수 없습니다: {CHARACTER_SOURCE}") from error
    if not data.startswith(b"\x89PNG\r\n\x1a\n"):
        raise ResourceError(f"캐릭터 이미지 형식이 잘못되었습니다: {CHARACTER_SOURCE}")
    CHARACTER_PATH.write_bytes(data)
    return CHARACTER_PATH


def load_character_image() -> QPixmap:
    path = ensure_character_image()
    image = QImage(str(path))
    if image.isNull():
        raise ResourceError(f"캐릭터 이미지를 열 수 없습니다: {path}")
    if image.format() != QImage.Format.Format_ARGB32_Premultiplied:
        image = image.convertToFormat(QImage.Format.Format_ARGB32_Premultiplied)
    return QPixmap.fromImage(image)
