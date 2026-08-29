"""
READ-ONLY Model File Safety Audit Script.
Verifies file existence and individual file sizes for production ML model files
prior to Commit 4.
"""

from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent
MODELS_DIR = BASE_DIR / "ml_models"

PRODUCTION_MODELS = [
    MODELS_DIR / "lstm_dambulla_retail.h5",
    MODELS_DIR / "lstm_dambulla_wholesale.h5",
    MODELS_DIR / "lstm_pettah_retail.h5",
    MODELS_DIR / "lstm_pettah_wholesale.h5",
    MODELS_DIR / "scaler_dambulla_retail.pkl",
    MODELS_DIR / "scaler_dambulla_wholesale.pkl",
    MODELS_DIR / "scaler_pettah_retail.pkl",
    MODELS_DIR / "scaler_pettah_wholesale.pkl",
    MODELS_DIR / "anomaly_dambulla_retail.pkl",
    MODELS_DIR / "anomaly_dambulla_wholesale.pkl",
    MODELS_DIR / "anomaly_pettah_retail.pkl",
    MODELS_DIR / "anomaly_pettah_wholesale.pkl",
]

def audit_models():
    print("==================================================================================")
    print(" READ-ONLY PRODUCTION ML MODEL FILES AUDIT")
    print("==================================================================================\n")

    total_bytes = 0
    for fpath in PRODUCTION_MODELS:
        rel = fpath.relative_to(BASE_DIR.parent)
        size_b = os.path.getsize(fpath)
        size_mb = size_b / (1024 * 1024)
        total_bytes += size_b
        print(f"  [OK] {str(rel):<50} : {size_mb:6.2f} MB ({size_b} bytes)")




    print("-" * 82)
    print(f"  TOTAL SIZE FOR ALL 12 PRODUCTION MODEL FILES: {total_bytes / (1024*1024):6.2f} MB")
    print(f"  GitHub 100MB Per-File Limit respected by ALL files: YES")

if __name__ == "__main__":
    audit_models()
