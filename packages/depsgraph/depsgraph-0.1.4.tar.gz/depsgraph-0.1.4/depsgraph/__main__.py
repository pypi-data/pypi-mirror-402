"""CLI entry point for python -m depsgraph."""

from __future__ import annotations

import sys

from depsgraph import main


def _run() -> int:
    return main()


if __name__ == "__main__":
    raise SystemExit(_run())
