"""SQLite persistence for monitoring cases and append-only observations."""

import json
import os
import sqlite3
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from config.observation_config import DB_PATH, OBSERVATIONS_DATA_DIR
from utils.location_service import public_location_fields


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_observation_db() -> None:
    os.makedirs(OBSERVATIONS_DATA_DIR, exist_ok=True)
    conn = _connect()
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS monitoring_cases (
            case_id TEXT PRIMARY KEY,
            crop_part TEXT NOT NULL,
            label TEXT,
            created_at TEXT NOT NULL
        )
        """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS observations (
            observation_id TEXT PRIMARY KEY,
            case_id TEXT NOT NULL,
            crop_part TEXT NOT NULL,
            created_at TEXT NOT NULL,
            disease TEXT NOT NULL,
            severity_score REAL NOT NULL,
            severity_class TEXT NOT NULL,
            embedding_json TEXT NOT NULL,
            similarity_score REAL,
            consistency_status TEXT NOT NULL,
            weather_context TEXT,
            trend TEXT,
            status TEXT,
            recommendation TEXT,
            accepted INTEGER NOT NULL DEFAULT 1,
            image_path TEXT,
            FOREIGN KEY (case_id) REFERENCES monitoring_cases(case_id)
        )
        """
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_observations_case ON observations(case_id, created_at)"
    )
    _migrate_observation_columns(cursor)
    conn.commit()
    conn.close()


def _migrate_observation_columns(cursor: sqlite3.Cursor) -> None:
    """Add location columns to existing databases without dropping data."""
    existing = {row[1] for row in cursor.execute("PRAGMA table_info(observations)")}
    additions = [
        ("latitude", "REAL"),
        ("longitude", "REAL"),
        ("area", "TEXT"),
        ("district", "TEXT"),
        ("province", "TEXT"),
        ("location_source", "TEXT"),
        ("severity_evidence_json", "TEXT"),
    ]
    for name, col_type in additions:
        if name not in existing:
            cursor.execute(f"ALTER TABLE observations ADD COLUMN {name} {col_type}")


def create_case(crop_part: str, label: Optional[str] = None) -> Dict[str, Any]:
    case_id = f"CASE-{uuid.uuid4().hex[:8].upper()}"
    created_at = _utc_now_iso()
    conn = _connect()
    conn.execute(
        "INSERT INTO monitoring_cases (case_id, crop_part, label, created_at) VALUES (?, ?, ?, ?)",
        (case_id, crop_part, label, created_at),
    )
    conn.commit()
    conn.close()
    return {"case_id": case_id, "crop_part": crop_part, "label": label, "created_at": created_at}


def get_case(case_id: str) -> Optional[Dict[str, Any]]:
    conn = _connect()
    row = conn.execute(
        "SELECT * FROM monitoring_cases WHERE case_id = ?", (case_id,)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def save_observation_image(case_id: str, observation_id: str, image_bytes: bytes) -> str:
    case_dir = os.path.join(OBSERVATIONS_DATA_DIR, case_id)
    os.makedirs(case_dir, exist_ok=True)
    path = os.path.join(case_dir, f"{observation_id}.jpg")
    with open(path, "wb") as f:
        f.write(image_bytes)
    return path


def insert_observation(record: Dict[str, Any]) -> Dict[str, Any]:
    conn = _connect()
    conn.execute(
        """
        INSERT INTO observations (
            observation_id, case_id, crop_part, created_at, disease,
            severity_score, severity_class, embedding_json, similarity_score,
            consistency_status, weather_context, trend, status, recommendation,
            accepted, image_path,
            latitude, longitude, area, district, province, location_source,
            severity_evidence_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            record["observation_id"],
            record["case_id"],
            record["crop_part"],
            record["created_at"],
            record["disease"],
            record["severity_score"],
            record["severity_class"],
            json.dumps(record["embedding"]),
            record.get("similarity_score"),
            record["consistency_status"],
            json.dumps(record.get("weather_context")),
            record.get("trend"),
            record.get("status"),
            json.dumps(record.get("recommendation")),
            1 if record.get("accepted", True) else 0,
            record.get("image_path"),
            record.get("latitude"),
            record.get("longitude"),
            record.get("area"),
            record.get("district"),
            record.get("province"),
            record.get("location_source"),
            json.dumps(record["severity_evidence"])
            if record.get("severity_evidence") is not None
            else None,
        ),
    )
    conn.commit()
    conn.close()
    return record


def get_accepted_observations(case_id: str, crop_part: str) -> List[Dict[str, Any]]:
    conn = _connect()
    rows = conn.execute(
        """
        SELECT * FROM observations
        WHERE case_id = ? AND crop_part = ? AND accepted = 1
        ORDER BY created_at ASC
        """,
        (case_id, crop_part),
    ).fetchall()
    conn.close()
    return [_row_to_observation(row) for row in rows]


def get_all_observations(case_id: str) -> List[Dict[str, Any]]:
    conn = _connect()
    rows = conn.execute(
        "SELECT * FROM observations WHERE case_id = ? ORDER BY created_at ASC",
        (case_id,),
    ).fetchall()
    conn.close()
    return [_row_to_observation(row) for row in rows]


def get_last_accepted_observation(case_id: str, crop_part: str) -> Optional[Dict[str, Any]]:
    observations = get_accepted_observations(case_id, crop_part)
    return observations[-1] if observations else None


def _row_to_observation(row: sqlite3.Row) -> Dict[str, Any]:
    return {
        "observation_id": row["observation_id"],
        "case_id": row["case_id"],
        "crop_part": row["crop_part"],
        "created_at": row["created_at"],
        "disease": row["disease"],
        "severity_score": row["severity_score"],
        "severity_class": row["severity_class"],
        "embedding": json.loads(row["embedding_json"]),
        "similarity_score": row["similarity_score"],
        "consistency_status": row["consistency_status"],
        "weather_context": json.loads(row["weather_context"]) if row["weather_context"] else None,
        "trend": row["trend"],
        "status": row["status"],
        "recommendation": json.loads(row["recommendation"]) if row["recommendation"] else None,
        "accepted": bool(row["accepted"]),
        "image_path": row["image_path"],
        "latitude": row["latitude"] if "latitude" in row.keys() else None,
        "longitude": row["longitude"] if "longitude" in row.keys() else None,
        "area": row["area"] if "area" in row.keys() else None,
        "district": row["district"] if "district" in row.keys() else None,
        "province": row["province"] if "province" in row.keys() else None,
        "location_source": row["location_source"] if "location_source" in row.keys() else None,
        "severity_evidence": (
            json.loads(row["severity_evidence_json"])
            if "severity_evidence_json" in row.keys() and row["severity_evidence_json"]
            else None
        ),
    }


_FARMER_HIDDEN = {
    "embedding",
    "severity_evidence",
    "cnn_high_prob",
    "verification_status",
    "final_severity",
    "secondary_severity",
    "secondary_confidence",
    "secondary_estimated_area_percentage",
    "secondary_reasoning",
}


def public_observation(obs: Dict[str, Any]) -> Dict[str, Any]:
    """Strip embeddings and secondary-verify internals from farmer-facing API."""
    out = {k: v for k, v in obs.items() if k not in _FARMER_HIDDEN}
    score = out.get("severity_score")
    if isinstance(score, (int, float)):
        out["estimated_affected_area_percentage"] = round(float(score) * 100.0, 1)
    loc = public_location_fields(
        {
            "latitude": out.pop("latitude", None),
            "longitude": out.pop("longitude", None),
            "area": out.pop("area", None),
            "district": out.pop("district", None),
            "province": out.pop("province", None),
            "source": out.pop("location_source", None),
        }
    )
    if loc:
        out["location"] = loc
    return out


init_observation_db()
