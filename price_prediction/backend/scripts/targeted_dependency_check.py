"""
Targeted READ-ONLY Dependency Check Script for Tomato Price Advisor project.
Performs byte-level hashing (SHA256), repository-wide string searches,
function/class reference tracking, and dependency chain validation.
"""

import hashlib
import os
from pathlib import Path
import pandas as pd
import re

BASE_DIR = Path(__file__).resolve().parent.parent

def compute_sha256(file_path: Path) -> str:
    if not file_path.exists() or file_path.is_dir():
        return "N/A"
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()

def search_text_in_repo(query: str) -> list[str]:
    matches = []
    # Search all text files in repo excluding venv / node_modules / .git
    for p in BASE_DIR.glob("**/*"):
        if p.is_file() and not any(part.startswith(".") or part in ["node_modules", "__pycache__", "brain"] for part in p.parts):
            if p.suffix in [".py", ".html", ".js", ".css", ".md", ".json", ".yml", ".txt"]:
                try:
                    text = p.read_text(encoding="utf-8", errors="ignore")
                    if query in text:
                        rel = str(p.relative_to(BASE_DIR)).replace("\\", "/")
                        matches.append(rel)
                except Exception:
                    pass
    return matches

def section_1_check_old_models():
    print("==================================================================================")
    print(" 1. CHECK OLD MODEL ARTIFACTS")
    print("==================================================================================\n")

    targets = ["lstm_price_predictor.h5", "scaler.pkl"]
    for t in targets:
        p = BASE_DIR / "ml_models" / t
        print(f"Target: {t}")
        print(f"Path: {p}")
        print(f"Exists: {p.exists()}")
        if p.exists():
            print(f"SHA-256: {compute_sha256(p)}")
        
        # References search
        refs = search_text_in_repo(t)
        # Exclude self reference in audit scripts if needed or list all
        print(f"Exact filename references ({len(refs)}):")
        for r in refs:
            print(f"  - {r}")
        
        # Partial search
        stem = Path(t).stem
        partial_refs = search_text_in_repo(stem)
        print(f"Stem '{stem}' references ({len(partial_refs)}):")
        for pr in partial_refs:
            print(f"  - {pr}")
        print("-" * 60 + "\n")

def section_2_check_legacy_services():
    print("==================================================================================")
    print(" 2. CHECK LEGACY PYTHON SERVICES")
    print("==================================================================================\n")

    legacy_files = [
        "app/models/lstm_model.py",
        "app/services/lstm_service.py",
        "app/services/dataset_price_service.py",
        "app/services/preprocessing_service.py",
        "app/services/recommendation_engine.py",
        "app/services/recommendation_service.py",
        "app/services/explanation_service.py",
        "test_prediction.py"
    ]

    for lf in legacy_files:
        p = BASE_DIR / lf
        print(f"--- Legacy File: {lf} ---")
        print(f"Exists: {p.exists()}")
        
        # Search filename
        fn_refs = search_text_in_repo(p.name)
        stem_refs = search_text_in_repo(p.stem)
        
        print(f"Filename '{p.name}' references in repo:")
        for r in fn_refs:
            print(f"  - {r}")
            
        print(f"Module stem '{p.stem}' references in repo:")
        for r in stem_refs:
            print(f"  - {r}")
            
        # Parse functions/classes defined inside file
        if p.exists():
            text = p.read_text(encoding="utf-8", errors="ignore")
            symbols = re.findall(r'def\s+([a-zA-Z0-9_]+)\s*\(|class\s+([a-zA-Z0-9_]+)\s*[\(:]', text)
            symbol_names = [s[0] or s[1] for s in symbols if (s[0] or s[1]) not in ["__init__", "main"]]
            print(f"Symbols defined in {p.name}: {symbol_names}")
            
            for sym in symbol_names:
                sym_refs = search_text_in_repo(sym)
                # Filter out definition file itself
                external_refs = [r for r in sym_refs if r != lf]
                print(f"  Symbol '{sym}' external references ({len(external_refs)}): {external_refs}")
        print("\n")

def section_3_check_old_datasets():
    print("==================================================================================")
    print(" 3. CHECK OLD DATASETS")
    print("==================================================================================\n")

    datasets = [
        "sri_lanka_crop_prices.csv",
        "food_prices_cleaned-selected-columns.csv",
        "Dollar-Carrot.csv",
        "final Datset.xlsx",
        "Vegetables_fruit_prices_with_climate_130000_2020_to_2025.csv"
    ]

    for d in datasets:
        p = BASE_DIR / "datasets" / d
        print(f"Dataset: {d}")
        print(f"Exists: {p.exists()}")
        refs = search_text_in_repo(d)
        print(f"References in repo ({len(refs)}):")
        for r in refs:
            print(f"  - {r}")
        print("-" * 60 + "\n")

def section_4_check_experimental():
    print("==================================================================================")
    print(" 4. CHECK ml_models/experimental/ HASH COMPARISON")
    print("==================================================================================\n")

    exp_dir = BASE_DIR / "ml_models" / "experimental"
    if not exp_dir.exists():
        print("Experimental directory does not exist.")
        return

    exp_files = sorted(list(exp_dir.glob("*")))
    rows = []

    for ef in exp_files:
        if ef.is_dir():
            continue
        prod_counterpart = BASE_DIR / "ml_models" / ef.name
        exp_hash = compute_sha256(ef)
        prod_hash = compute_sha256(prod_counterpart)
        is_identical = (exp_hash == prod_hash) and (exp_hash != "N/A")

        refs = search_text_in_repo(str(ef.relative_to(BASE_DIR)).replace("\\", "/"))
        refs_name = search_text_in_repo(ef.name)

        rows.append({
            "Experimental File": ef.name,
            "Production Counterpart": prod_counterpart.name if prod_counterpart.exists() else "None",
            "Identical (SHA256)?": is_identical,
            "Exp Hash": exp_hash[:12] + "...",
            "Prod Hash": prod_hash[:12] + "..." if prod_hash != "N/A" else "N/A"
        })

    df_exp = pd.DataFrame(rows)
    print(df_exp.to_string(index=False))
    print("\n")

if __name__ == "__main__":
    section_1_check_old_models()
    section_2_check_legacy_services()
    section_3_check_old_datasets()
    section_4_check_experimental()
