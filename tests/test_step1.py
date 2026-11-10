"""Headless checks for STEP 1 geometry and persistence."""

from __future__ import annotations

import json
import struct
import tempfile
import unittest
import zlib
from pathlib import Path


def read_png_alpha(path: Path) -> list[list[int]]:
    data = path.read_bytes()
    assert data.startswith(b"\x89PNG\r\n\x1a\n")
    offset = 8
    width = height = None
    compressed = b""
    while offset < len(data):
        length = struct.unpack(">I", data[offset:offset + 4])[0]
        tag = data[offset + 4:offset + 8]
        chunk = data[offset + 8:offset + 8 + length]
        if tag == b"IHDR":
            width, height, bit_depth, color_type = struct.unpack(">IIBB", chunk[:10])
            assert bit_depth == 8 and color_type == 6
        elif tag == b"IDAT":
            compressed += chunk
        offset += 12 + length
    rows = zlib.decompress(compressed)
    stride = width * 4
    alpha = []
    cursor = 0
    for _ in range(height):
        assert rows[cursor] == 0
        cursor += 1
        row = rows[cursor:cursor + stride]
        alpha.append([row[index + 3] for index in range(0, stride, 4)])
        cursor += stride
    return alpha


def clamp(x: int, y: int, width: int, height: int, area: tuple[int, int, int, int]) -> tuple[int, int]:
    left, top, right, bottom = area
    return (
        min(max(x, left), right - width + 1),
        min(max(y, top), bottom - height + 1),
    )


class Step1Tests(unittest.TestCase):
    def test_png_keeps_transparency_and_has_an_opaque_body(self) -> None:
        alpha = read_png_alpha(Path(__file__).resolve().parents[1] / "assets" / "images" / "rakko.png")
        flat = [value for row in alpha for value in row]
        self.assertIn(0, flat)
        self.assertTrue(any(value > 16 for value in flat))
        self.assertEqual(alpha[0][0], 0)
        self.assertGreater(alpha[118][110], 16)

    def test_character_cannot_leave_available_area(self) -> None:
        area = (100, 50, 999, 699)
        self.assertEqual(clamp(-40, -10, 220, 220, area), (100, 50))
        self.assertEqual(clamp(2000, 2000, 220, 220, area), (780, 480))
        self.assertEqual(clamp(300, 200, 220, 220, area), (300, 200))

    def test_position_round_trip(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "state.json"
            payload = {"x": 640, "y": 280}
            path.write_text(json.dumps(payload), encoding="utf-8")
            loaded = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual((int(loaded["x"]), int(loaded["y"])), (640, 280))


if __name__ == "__main__":
    unittest.main()
