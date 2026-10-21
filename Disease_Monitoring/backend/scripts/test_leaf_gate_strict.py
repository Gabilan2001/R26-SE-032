"""
Strict LEAF gate regression tests (no retrain).

Usage (from backend/):
  python scripts/test_leaf_gate_strict.py
"""

from __future__ import annotations

import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from ml.predict.cv_pregate import REJECT_MESSAGE_LEAF, validate_crop_image  # noqa: E402
from ml.predict.gate_predictor import is_valid_fruit, is_valid_leaf  # noqa: E402
from scripts.test_fruit_gate_strict import (  # noqa: E402
    _apple_regression,
    _banana,
    _building,
    _document,
    _face,
    _green_tomato,
    _orange,
    _red_tomato,
    _textured_apple,
)


def _tomato_leaf_bytes():
    p = BACKEND / "data" / "observations" / "CASE-2783DA2A" / "OBS-AB097DEF.jpg"
    return p.read_bytes() if p.exists() else None


def _check(name: str, data: bytes, crop: str, expect_accept: bool) -> bool:
    r = validate_crop_image(data, crop)
    if crop == "FRUIT":
        ok, _, reason = is_valid_fruit(data)
    else:
        ok, _, reason = is_valid_leaf(data)
    passed = (ok == expect_accept) and (r.accepted == expect_accept)
    if expect_accept is False and crop == "LEAF" and reason:
        passed = passed and ("leaf" in reason.lower())
    tag = "PASS" if passed else "FAIL"
    print(
        f"[{tag}] {name:22s} crop={crop:5s} expect={'ACCEPT' if expect_accept else 'REJECT'} "
        f"got={'ACCEPT' if ok else 'REJECT'} "
        f"leaf={r.details.get('leaf_score', 0):.2f} fruit={r.details.get('fruit_score', 0):.2f} "
        f"citrus={r.details.get('citrus', 0):.2f}"
    )
    if not expect_accept and crop == "LEAF" and ok is False:
        assert reason == REJECT_MESSAGE_LEAF or (reason and "leaf" in reason.lower())
    return passed


def main():
    results = []
    leaf = _tomato_leaf_bytes()

    if leaf is not None:
        results.append(_check("tomato_leaf", leaf, "LEAF", True))
    else:
        print("[SKIP] tomato leaf observation image missing")

    # LEAF rejects — non-leaf / wrong modality
    results.append(_check("apple_regression", _apple_regression(), "LEAF", False))
    results.append(_check("textured_apple", _textured_apple(), "LEAF", False))
    results.append(_check("orange", _orange(), "LEAF", False))
    results.append(_check("banana", _banana(), "LEAF", False))
    results.append(_check("face", _face(), "LEAF", False))
    results.append(_check("document", _document(), "LEAF", False))
    results.append(_check("building", _building(), "LEAF", False))
    results.append(_check("green_tomato", _green_tomato(), "LEAF", False))
    results.append(_check("red_tomato", _red_tomato(), "LEAF", False))

    if leaf is not None:
        results.append(_check("tomato_leaf_in_FRUIT", leaf, "FRUIT", False))

    failed = results.count(False)
    print(f"\n{len(results) - failed}/{len(results)} checks matched expectation")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
