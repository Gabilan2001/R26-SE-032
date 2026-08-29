import pickle
import pandas as pd
from pathlib import Path

base_dir = Path("ml_models")
exp_dir = base_dir / "experimental"

series_list = ["dambulla_retail", "dambulla_wholesale", "pettah_retail", "pettah_wholesale"]

df = pd.read_csv("datasets/tomato_prices_vegetablesSriLanka.csv")
df.columns = [c.strip() for c in df.columns]
df["Date"] = pd.to_datetime(df["Date"])

print("=== SCALER COMPARISON (OLD vs NEW FIT ON EXPANDED DATASET) ===\n")
header = f"{'Series':<22} | {'Old Scaler Min/Max':<22} | {'New Scaler Min/Max':<22} | {'Aug 2026 Price Range':<22} | {'In Range?'}"
print(header)
print("-" * len(header))

for s in series_list:
    old_p = base_dir / f"scaler_{s}.pkl"
    new_p = exp_dir / f"scaler_{s}.pkl"
    
    with open(old_p, "rb") as f:
        s_old = pickle.load(f)
    with open(new_p, "rb") as f:
        s_new = pickle.load(f)
        
    parts = s.split("_")
    m_cap = parts[0].capitalize()
    t_cap = parts[1].capitalize()
    
    sub = df[(df["Market"] == m_cap) & (df["Type"] == t_cap)].copy()
    sub_aug = sub[sub["Date"] >= "2026-08-01"]
    aug_min, aug_max = sub_aug["Price"].min(), sub_aug["Price"].max()
    
    old_min, old_max = s_old.data_min_[0], s_old.data_max_[0]
    new_min, new_max = s_new.data_min_[0], s_new.data_max_[0]
    
    in_range = (aug_min >= new_min) and (aug_max <= new_max)
    
    old_str = f"[{old_min:.2f}, {old_max:.2f}]"
    new_str = f"[{new_min:.2f}, {new_max:.2f}]"
    aug_str = f"[{aug_min:.2f}, {aug_max:.2f}]"
    
    print(f"{s:<22} | {old_str:<22} | {new_str:<22} | {aug_str:<22} | {str(in_range):<10}")
