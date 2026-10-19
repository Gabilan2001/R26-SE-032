"""Shared pytest configuration for cross-module unit tests."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

# Backend roots used by unit tests (import order matters per test file).
BACKEND_PATHS = {
    "nutrient": PROJECT_ROOT / "Nutrient_Deficiency" / "backend",
    "fruit": PROJECT_ROOT / "Tomato_fruit_disease" / "backend",
    "monitoring": PROJECT_ROOT / "Disease_Monitoring" / "backend",
    "price": PROJECT_ROOT / "price_prediction" / "backend",
}


def _prepend_path(path: Path) -> None:
    path_str = str(path)
    if path_str not in sys.path:
        sys.path.insert(0, path_str)


def use_backend(name: str) -> None:
    """Put one backend on sys.path for isolated imports."""
    _prepend_path(BACKEND_PATHS[name])
