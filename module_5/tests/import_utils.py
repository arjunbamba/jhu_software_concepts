"""Utilities for importing application modules inside tests."""

from __future__ import annotations

import importlib
import sys
from pathlib import Path


SRC_PATH = Path(__file__).resolve().parents[1] / "src"


def import_module(module_name: str):
    """Import ``module_name`` ensuring the src directory is on ``sys.path``."""

    try:
        return importlib.import_module(module_name)
    except ModuleNotFoundError:  # pragma: no cover - defensive fallback
        if str(SRC_PATH) not in sys.path:
            sys.path.insert(0, str(SRC_PATH))
        return importlib.import_module(module_name)
