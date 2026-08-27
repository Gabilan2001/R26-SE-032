"""Verify MATCH/MISMATCH on leaf + fruit demo crop sequences."""
from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "backend"))

from config.observation_config import MATCH_THRESHOLD  # noqa: E402
from consistency.consistency_checker import check_consistency  # noqa: E402
from consistency.similarity import cosine_similarity  # noqa: E402
from severity.fruit.fruit_severity import predict_fruit_severity  # noqa: E402
from severity.leaf.efficientnet_severity import predict_leaf_severity  # noqa: E402

LEAF_KIT = PROJECT_ROOT / "demo_data" / "observation_sequences"
FRUIT_KIT = PROJECT_ROOT / "demo_data" / "observation_sequences_fruit"


def _emb_leaf(p: Path):
    return predict_leaf_severity(p.read_bytes())["embedding"]


def _emb_fruit(p: Path):
    return predict_fruit_severity(p.read_bytes())["embedding"]


def _check_case(case_dir: Path, emb_fn, label: str) -> bool:
    p1, p2, p3 = case_dir / "obs_01.jpg", case_dir / "obs_02.jpg", case_dir / "obs_03.jpg"
    if not p1.is_file():
        print(f"SKIP missing {case_dir.name}")
        return True
    e1, e2, e3 = emb_fn(p1), emb_fn(p2), emb_fn(p3)
    s12 = cosine_similarity(e1, e2)
    s23 = cosine_similarity(e2, e3)
    s13 = cosine_similarity(e1, e3)
    st12, a12, _ = check_consistency(s12, False)
    st23, a23, _ = check_consistency(s23, False)
    st13, a13, _ = check_consistency(s13, False)
    ok = min(s12, s23, s13) >= MATCH_THRESHOLD and a12 and a23 and a13
    print(
        f"{'OK' if ok else 'FAIL'} {label}/{case_dir.name} "
        f"12={s12:.3f}({st12}) 23={s23:.3f}({st23}) 13={s13:.3f}({st13})"
    )
    return ok


def _mismatch(same: Path, other: Path, emb_fn, label: str) -> bool:
    e0 = emb_fn(same)
    em = emb_fn(other)
    sim = cosine_similarity(e0, em)
    status, accepted, _ = check_consistency(sim, False)
    ok = status == "MISMATCH" and not accepted
    print(
        f"{'OK' if ok else 'FAIL'} {label} mismatch sim={sim:.3f} "
        f"status={status} accepted={accepted}"
    )
    return ok


def main() -> int:
    fails = 0
    leaf_cases = [
        LEAF_KIT / "case_LOW_01",
        LEAF_KIT / "case_LOW_04",
        LEAF_KIT / "case_HIGH_01",
        LEAF_KIT / "case_HIGH_20",
    ]
    for c in leaf_cases:
        if not _check_case(c, _emb_leaf, "LEAF"):
            fails += 1
    leaf_mm = LEAF_KIT / "mismatch" / "other_leaf.jpg"
    if leaf_mm.is_file():
        if not _mismatch(LEAF_KIT / "case_LOW_04" / "obs_01.jpg", leaf_mm, _emb_leaf, "LEAF"):
            fails += 1

    fruit_cases = [
        FRUIT_KIT / "case_FRUIT_LOW_01",
        FRUIT_KIT / "case_FRUIT_LOW_05",
        FRUIT_KIT / "case_FRUIT_HIGH_02",
        FRUIT_KIT / "case_FRUIT_HIGH_05",
    ]
    for c in fruit_cases:
        if c.is_dir() and not _check_case(c, _emb_fruit, "FRUIT"):
            fails += 1
    fruit_mm = FRUIT_KIT / "mismatch" / "other_fruit.jpg"
    if fruit_mm.is_file() and (FRUIT_KIT / "case_FRUIT_HIGH_05" / "obs_01.jpg").is_file():
        if not _mismatch(
            FRUIT_KIT / "case_FRUIT_HIGH_05" / "obs_01.jpg",
            fruit_mm,
            _emb_fruit,
            "FRUIT",
        ):
            fails += 1

    print(f"\nfails={fails}")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
