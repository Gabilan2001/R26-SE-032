"""Build FRUIT observation demo sequences (crop/framing only).

Mirrors the leaf demo kit:
  obs_01 = original tomato-fruit JPEG copy
  obs_02 / obs_03 = same fruit, slight crop / framing only

Only source images that currently pass the FRUIT OpenCV gate are used.
No lighting / rotation / blur edits. Source dataset is never modified.

  python scripts/build_fruit_observation_demo_kit.py --cases-per-class 40 --clean
"""
from __future__ import annotations

import argparse
import csv
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

try:
    from PIL import Image
except ImportError as exc:  # pragma: no cover
    raise SystemExit("Pillow is required. Install with: pip install Pillow") from exc

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
sys.path.insert(0, str(PROJECT_ROOT / "backend"))

from build_observation_demo_kit import (  # noqa: E402
    VARIANT_SPECS,
    clamp,
    list_images,
    make_crop_variant,
    pick_sources,
    relative_to_project,
)

DEFAULT_SOURCE_ROOT = (
    PROJECT_ROOT
    / "Tomato_Severity_Dataset"
    / "data"
    / "processed"
    / "fruit_cnn_severity_dataset"
    / "test"
)
DEFAULT_OUTPUT_ROOT = PROJECT_ROOT / "demo_data" / "observation_sequences_fruit"
SEVERITY_CLASSES = ("LOW", "HIGH")


def _passes_fruit_gate(path: Path) -> bool:
    from ml.predict.cv_pregate import validate_crop_image

    try:
        return bool(validate_crop_image(path.read_bytes(), "FRUIT").accepted)
    except Exception:
        return False


def write_case_readme(case_dir: Path, meta: dict) -> None:
    text = f"""# Fruit observation demo case: `{meta["case_id"]}`

## Important

These three images are **crop/framing variants of one source tomato-fruit
photograph** (`{meta["severity_class"]}`).

Demo / monitoring pipeline only — not biological same-plant field proof.

## Upload order

1. `obs_01.jpg` — original
2. `obs_02.jpg` — same fruit, slight crop
3. `obs_03.jpg` — same fruit, another slight crop

## Source

- `{meta["source_relative"]}`
- Generated (UTC): `{meta["generated_at_utc"]}`
"""
    (case_dir / "README.md").write_text(text, encoding="utf-8")


def write_kit_readme(output_root: Path, summary: dict) -> None:
    text = f"""# Fruit observation sequence demo kit

Generated: `{summary["generated_at_utc"]}` (UTC)

## Method

Crop/framing only from `fruit_cnn_severity_dataset/test/{{LOW|HIGH}}`.
Sources are filtered to images that pass the current FRUIT OpenCV gate.

No lighting/rotation/blur. No model training. Source files untouched.

## Use

1. Create a **FRUIT** monitoring case in the app.
2. Upload `obs_01.jpg` → `obs_02.jpg` → `obs_03.jpg` from one `case_*` folder.
3. For MISMATCH demos use `mismatch/other_fruit.jpg` or a leaf image.

## Summary

- Cases: {summary["cases_generated"]}
- Mismatch: {summary.get("mismatch_filename") or "none"}
"""
    (output_root / "README.md").write_text(text, encoding="utf-8")


def build_case(source: Path, case_dir: Path, *, case_id: str, severity_class: str) -> dict:
    case_dir.mkdir(parents=True, exist_ok=True)
    image = Image.open(source).convert("RGB")
    rows: list[dict] = []
    for spec in VARIANT_SPECS:
        out = case_dir / spec["filename"]
        scale = float(spec["scale"])
        ox = float(spec.get("offset_x_frac", 0.0))
        oy = float(spec.get("offset_y_frac", 0.0))
        if spec["role"] == "baseline":
            if source.suffix.lower() in {".jpg", ".jpeg"}:
                shutil.copy2(source, out)
            else:
                image.save(out, format="JPEG", quality=95, optimize=True)
            method = "original_copy"
        else:
            make_crop_variant(image, scale=scale, offset_x_frac=ox, offset_y_frac=oy).save(
                out, format="JPEG", quality=95, optimize=True
            )
            method = "crop_framing"
        rows.append(
            {
                "filename": spec["filename"],
                "role": spec["role"],
                "scale": scale,
                "offset_x_frac": ox,
                "offset_y_frac": oy,
                "method": method,
            }
        )
    meta = {
        "case_id": case_id,
        "crop_part": "FRUIT",
        "severity_class": severity_class,
        "source_filename": source.name,
        "source_relative": relative_to_project(source),
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "claim": "demo_fruit_crop_variants;not_biological_same_plant",
        "observations": rows,
    }
    (case_dir / "case_meta.json").write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
    write_case_readme(case_dir, meta)
    return meta


def clean_output_tree(output_root: Path) -> None:
    if not output_root.exists():
        return
    for child in output_root.iterdir():
        if child.is_dir() and (child.name.startswith("case_") or child.name == "mismatch"):
            shutil.rmtree(child)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build FRUIT crop-only observation demo kit")
    parser.add_argument("--source-root", type=Path, default=DEFAULT_SOURCE_ROOT)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--cases-per-class", type=int, default=20)
    parser.add_argument("--clean", action="store_true")
    args = parser.parse_args()

    if not args.source_root.is_dir():
        print(f"ERROR: missing source root {args.source_root}", file=sys.stderr)
        return 1
    if args.clean:
        clean_output_tree(args.output_root)
    args.output_root.mkdir(parents=True, exist_ok=True)

    manifest: list[dict] = []
    cases_meta: list[dict] = []
    used: set[Path] = set()

    for severity in SEVERITY_CLASSES:
        class_dir = args.source_root / severity
        candidates = [p for p in list_images(class_dir) if _passes_fruit_gate(p)]
        print(f"{severity}: gate-accepted sources {len(candidates)}/{len(list_images(class_dir))}")
        for index, source in enumerate(
            pick_sources(candidates, max(1, int(args.cases_per_class))), start=1
        ):
            case_id = f"case_FRUIT_{severity}_{index:02d}"
            meta = build_case(
                source,
                args.output_root / case_id,
                case_id=case_id,
                severity_class=severity,
            )
            cases_meta.append(meta)
            used.add(source.resolve())
            for obs in meta["observations"]:
                manifest.append(
                    {
                        "case_id": case_id,
                        "severity_class": severity,
                        "observation_file": obs["filename"],
                        "role": obs["role"],
                        "source_filename": source.name,
                        "output_path": relative_to_project(
                            args.output_root / case_id / obs["filename"]
                        ),
                    }
                )
            print(f"OK  {case_id}  <-  {severity}/{source.name}")

    mismatch_dir = args.output_root / "mismatch"
    mismatch_dir.mkdir(parents=True, exist_ok=True)
    mismatch_name = ""
    # Prefer a different accepted fruit, else any unused fruit file
    mismatch_src = None
    for severity in SEVERITY_CLASSES:
        for candidate in list_images(args.source_root / severity):
            if candidate.resolve() not in used:
                mismatch_src = candidate
                break
        if mismatch_src:
            break
    if mismatch_src:
        mismatch_name = "other_fruit.jpg"
        shutil.copy2(mismatch_src, mismatch_dir / mismatch_name)
        (mismatch_dir / "README.md").write_text(
            f"# Mismatch sample\n\nDifferent source fruit (`{mismatch_src.name}`).\n",
            encoding="utf-8",
        )
        print(f"OK  mismatch/{mismatch_name}")

    summary = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "crop_part": "FRUIT",
        "source_root": str(args.source_root),
        "output_root": str(args.output_root),
        "cases_generated": len(cases_meta),
        "mismatch_filename": mismatch_name or None,
        "transform_ranges": {
            "method": "crop_framing_only",
            "obs_01": "original_copy",
            "obs_02": "scale=0.98 offset≈(+1.0%,-0.8%)",
            "obs_03": "scale=0.97 offset≈(-0.8%,+1.0%)",
        },
        "disclaimer": "DEMO crop variants; not biological same-plant time series.",
        "cases": [
            {
                "case_id": c["case_id"],
                "severity_class": c["severity_class"],
                "source_filename": c["source_filename"],
            }
            for c in cases_meta
        ],
    }
    with (args.output_root / "kit_manifest.csv").open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=[
                "case_id",
                "severity_class",
                "observation_file",
                "role",
                "source_filename",
                "output_path",
            ],
        )
        writer.writeheader()
        writer.writerows(manifest)
    (args.output_root / "kit_summary.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )
    write_kit_readme(args.output_root, summary)
    gitignore = args.output_root / ".gitignore"
    if not gitignore.exists():
        gitignore.write_text(
            "case_*/\nmismatch/\nkit_manifest.csv\nkit_summary.json\n",
            encoding="utf-8",
        )
    print(f"\nWrote fruit kit -> {args.output_root} | cases={len(cases_meta)}")
    return 0 if cases_meta else 2


if __name__ == "__main__":
    # silence unused import lint for clamp
    _ = clamp
    raise SystemExit(main())
