#!/usr/bin/env python3
"""Evaluation-friendly launcher for SentinelTrace.

Run from this project folder with: ``python3 run.py``
"""
from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from sentineltrace.server import main  # noqa: E402 - src path is configured above


if __name__ == "__main__":
    main()
