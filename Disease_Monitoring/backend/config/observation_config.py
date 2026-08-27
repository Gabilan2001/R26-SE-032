"""Configuration for observation-based disease recovery monitoring."""

import os

# Crop parts
CROP_PART_LEAF = "LEAF"
CROP_PART_FRUIT = "FRUIT"
CROP_PARTS = {CROP_PART_LEAF, CROP_PART_FRUIT}

# Supported diseases by crop part (external YOLO contract)
LEAF_DISEASES = {"early_blight", "late_blight", "leaf_miner"}
FRUIT_DISEASES = {"anthracnose", "blossom_end_rot", "spotted_wilt_virus"}

DISEASES_BY_CROP = {
    CROP_PART_LEAF: LEAF_DISEASES,
    CROP_PART_FRUIT: FRUIT_DISEASES,
}

# Visual consistency thresholds (cosine similarity on L2-normalized embeddings)
MATCH_THRESHOLD = float(os.getenv("CONSISTENCY_MATCH_THRESHOLD", "0.85"))
POSSIBLE_MATCH_THRESHOLD = float(os.getenv("CONSISTENCY_POSSIBLE_THRESHOLD", "0.65"))

# Trend analysis
STABLE_EPSILON = float(os.getenv("TREND_STABLE_EPSILON", "0.05"))
RECOVERED_SCORE_MAX = float(os.getenv("TREND_RECOVERED_SCORE_MAX", "0.25"))

# Visual affected-area severity (OpenCV estimate): 0–30% LOW, >30% HIGH
SEVERITY_AREA_THRESHOLD = float(os.getenv("SEVERITY_AREA_THRESHOLD", "0.30"))

# Paths
BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
LEAF_SEVERITY_MODEL_PATH = os.getenv(
    "LEAF_SEVERITY_MODEL_PATH",
    os.path.join(BACKEND_DIR, "datasets", "best_cnn_severity_model.pth"),
)
FRUIT_SEVERITY_MODEL_PATH = os.getenv(
    "FRUIT_SEVERITY_MODEL_PATH",
    os.path.join(BACKEND_DIR, "datasets", "fruit_severity_cnn.pth"),
)
OBSERVATIONS_DATA_DIR = os.getenv(
    "OBSERVATIONS_DATA_DIR",
    os.path.join(BACKEND_DIR, "data", "observations"),
)
DB_PATH = os.getenv("OBSERVATION_DB_PATH", os.path.join(BACKEND_DIR, "leaf_monitoring.db"))

# Optional external disease API (future)
YOLO_DISEASE_API_URL = os.getenv("YOLO_DISEASE_API_URL", "")
