"""Seed DEMO LEAF observation records into the existing SQLite schema.

Creates Day 1 / Day 3 / Day 7 sequences from demo_data/observation_sequences/.

Marked as DEMO/SEEDED in weather_context. Does not retrain models.

  python scripts/seed_leaf_demo_observations.py --replace-demo
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
BACKEND = PROJECT_ROOT / "backend"
sys.path.insert(0, str(BACKEND))

from config.observation_config import (  # noqa: E402
    DB_PATH,
    OBSERVATIONS_DATA_DIR,
    SEVERITY_AREA_THRESHOLD,
)
from consistency.similarity import cosine_similarity  # noqa: E402
from observation.observation_repository import (  # noqa: E402
    create_case,
    init_observation_db,
    insert_observation,
    save_observation_image,
)
from observation.recommendation_service import get_worsening_recommendation  # noqa: E402
from observation.trend_analysis import compute_overall_status, compute_trend  # noqa: E402
from severity.leaf.efficientnet_severity import predict_leaf_severity  # noqa: E402

LEAF_KIT = PROJECT_ROOT / "demo_data" / "observation_sequences"
DEMO_PREFIX = "DEMO-LEAF-"

TREND_TEMPLATES = [
    ("improving_recover", [45.0, 32.0, 18.0], ["early_blight", "early_blight", "early_blight"]),
    ("worsening", [15.0, 22.0, 38.0], ["late_blight", "late_blight", "late_blight"]),
    ("stable_low", [20.0, 21.0, 19.0], ["leaf_miner", "leaf_miner", "leaf_miner"]),
    ("stable_high", [40.0, 42.0, 41.0], ["early_blight", "early_blight", "early_blight"]),
    ("recovering", [35.0, 28.0, 12.0], ["late_blight", "late_blight", "late_blight"]),
]

LOW_BANK = [5.0, 8.0, 12.0, 18.0, 22.0, 27.0, 30.0]
HIGH_BANK = [31.0, 35.0, 40.0, 48.0, 55.0, 65.0, 75.0]


def _pct_to_score(pct: float) -> float:
    return round(float(pct) / 100.0, 4)


def _class_for_pct(pct: float) -> str:
    return "HIGH" if pct > SEVERITY_AREA_THRESHOLD * 100.0 else "LOW"


def _delete_existing_demo(conn: sqlite3.Connection) -> int:
    rows = conn.execute(
        "SELECT case_id FROM monitoring_cases WHERE label LIKE ?",
        (f"{DEMO_PREFIX}%",),
    ).fetchall()
    case_ids = [r[0] for r in rows]
    for case_id in case_ids:
        conn.execute("DELETE FROM observations WHERE case_id = ?", (case_id,))
        conn.execute("DELETE FROM monitoring_cases WHERE case_id = ?", (case_id,))
    conn.commit()
    return len(case_ids)


def _list_leaf_cases() -> list[Path]:
    if not LEAF_KIT.is_dir():
        return []
    return sorted(
        [
            p
            for p in LEAF_KIT.iterdir()
            if p.is_dir() and (p.name.startswith("case_LOW_") or p.name.startswith("case_HIGH_"))
        ]
    )


def _embedding_for(image_path: Path) -> list[float]:
    return predict_leaf_severity(image_path.read_bytes())["embedding"]


def seed(replace_demo: bool) -> dict:
    init_observation_db()
    cases = _list_leaf_cases()
    if len(cases) < 5:
        raise SystemExit(
            f"Need leaf demo kit under {LEAF_KIT}. "
            "Run: python scripts/build_observation_demo_kit.py --cases-per-class 20 --clean"
        )

    conn = sqlite3.connect(DB_PATH)
    removed = 0
    if replace_demo:
        removed = _delete_existing_demo(conn)
    conn.close()

    base_day = datetime(2026, 7, 1, 10, 0, 0, tzinfo=timezone.utc)
    day_offsets = [0, 3, 7]
    obs_files = ["obs_01.jpg", "obs_02.jpg", "obs_03.jpg"]

    created_cases = 0
    created_obs = 0
    template_i = 0

    for case_dir in cases:
        meta = json.loads((case_dir / "case_meta.json").read_text(encoding="utf-8"))
        severity_bucket = meta.get("severity_class", "LOW")
        template_name, pcts, diseases = TREND_TEMPLATES[template_i % len(TREND_TEMPLATES)]
        template_i += 1

        if template_i % 3 == 0:
            bank = LOW_BANK if severity_bucket == "LOW" else HIGH_BANK
            if severity_bucket == "LOW":
                pcts = [bank[0], bank[2], bank[4]]
            else:
                pcts = [bank[1], bank[3], bank[5]]
            template_name = f"bank_{severity_bucket.lower()}"

        for p in pcts:
            assert _class_for_pct(p) == ("HIGH" if p > 30 else "LOW")

        label = f"{DEMO_PREFIX}{case_dir.name}_{template_name}"
        case = create_case("LEAF", label=label)
        created_cases += 1
        prev_emb = None
        prev_score = None
        trends: list[str] = []

        for idx, (day_off, fname, pct, disease) in enumerate(
            zip(day_offsets, obs_files, pcts, diseases)
        ):
            img_path = case_dir / fname
            if not img_path.is_file():
                raise SystemExit(f"Missing {img_path}")
            emb = _embedding_for(img_path)
            score = _pct_to_score(pct)
            sev_class = _class_for_pct(pct)
            created_at = (base_day + timedelta(days=day_off, hours=idx)).isoformat()
            similarity = None
            if prev_emb is not None:
                similarity = round(cosine_similarity(emb, prev_emb), 4)
            consistency = (
                "BASELINE"
                if prev_emb is None
                else (
                    "MATCH"
                    if similarity is not None and similarity >= 0.85
                    else "POSSIBLE_MATCH"
                )
            )
            trend = compute_trend(score, prev_score)
            trends.append(trend)
            status = compute_overall_status(trends)
            observation_id = f"OBS-{uuid.uuid4().hex[:10].upper()}"
            stored = save_observation_image(case["case_id"], observation_id, img_path.read_bytes())
            recommendation = get_worsening_recommendation(
                disease=disease, trend=trend, weather_context=None
            )
            insert_observation(
                {
                    "observation_id": observation_id,
                    "case_id": case["case_id"],
                    "crop_part": "LEAF",
                    "created_at": created_at,
                    "disease": disease,
                    "severity_score": score,
                    "severity_class": sev_class,
                    "embedding": emb,
                    "similarity_score": similarity,
                    "consistency_status": consistency,
                    "weather_context": {
                        "demo": True,
                        "seeded": True,
                        "demo_kind": "LEAF_OBSERVATION_DEMO",
                        "planned_affected_area_percentage": pct,
                        "day_index": idx + 1,
                        "day_offset": day_off,
                        "template": template_name,
                        "note": "DEMO/SEEDED TEST DATA — not field ground truth",
                    },
                    "trend": trend,
                    "status": status,
                    "recommendation": recommendation,
                    "accepted": True,
                    "image_path": stored,
                }
            )
            prev_emb = emb
            prev_score = score
            created_obs += 1

    return {
        "db_path": DB_PATH,
        "observations_dir": OBSERVATIONS_DATA_DIR,
        "demo_cases_removed": removed,
        "cases_created": created_cases,
        "observations_created": created_obs,
        "crop_part": "LEAF",
        "severity_threshold": SEVERITY_AREA_THRESHOLD,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--replace-demo", action="store_true")
    args = parser.parse_args()
    summary = seed(replace_demo=args.replace_demo)
    print(json.dumps(summary, indent=2))
    return 0 if summary["observations_created"] >= 100 else 2


if __name__ == "__main__":
    raise SystemExit(main())
