"""Launch the desktop pet."""

from __future__ import annotations

import sys

from src.app import run
from src.resources import ResourceError


def main() -> int:
    try:
        return run()
    except ResourceError as error:
        print(error, file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
