"""
Inventory Python source files and trace imports/references.
"""

from pathlib import Path
import os
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent

def audit_python_files():
    print("==================================================================================")
    print(" 4. INVENTORY PYTHON SOURCE CODE")
    print("==================================================================================\n")

    py_files = sorted(list(BASE_DIR.glob("**/*.py")))

    rows = []
    for p in py_files:
        if any(part.startswith(".") for part in p.parts):
            continue
        rel_path = str(p.relative_to(BASE_DIR)).replace("\\", "/")
        st = os.stat(p)
        size_kb = st.st_size / 1024.0
        
        # Read content to check imports/references
        content = p.read_text(encoding="utf-8", errors="ignore")
        line_count = len(content.splitlines())

        rows.append({
            "Path": rel_path,
            "Lines": line_count,
            "Size (KB)": f"{size_kb:.1f}"
        })

    df_py = pd.DataFrame(rows)
    print(df_py.to_string(index=False))

if __name__ == "__main__":
    audit_python_files()
