"""Build observation demo sequences from existing LOW/HIGH severity images.

Purpose
-------
The public severity dataset does not contain multi-day same-plant captures.
For Observation Monitoring demos and pipeline tests, this utility creates
short observation sequences (obs_01 / obs_02 / obs_03) from a *single*
source leaf image using only conservative crop / framing differences.

    obs_01 = original image (copied unchanged when the source is JPEG)
    obs_02 = same leaf, slightly tighter / shifted crop
    obs_03 = same leaf, another slight crop / framing

No lighting, brightness, contrast, color, rotation, perspective, blur, or
noise changes. Disease appearance is not redrawn.

What this is
------------
- Curated monitoring-case sequences for UI / API demonstration
- Visual-consistency friendly (same leaf content → typically MATCH)

What this is NOT
----------------
- Biological proof of the same physical plant
- Expert disease progression over time
- Model training or label fabrication
- Modification of Tomato_Severity_Dataset source files

Run from the Disease_Monitoring project root:

  python scripts/build_observation_demo_kit.py
  python scripts/build_observation_demo_kit.py --cases-per-class 2 --clean

Requires: Pillow
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
DEFAULT_SOURCE_ROOT = (
    PROJECT_ROOT
    / "Tomato_Severity_Dataset"
    / "data"
    / "processed"
    / "cnn_severity_dataset"
    / "test"
)
DEFAULT_OUTPUT_ROOT = PROJECT_ROOT / "demo_data" / "observation_sequences"

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
SEVERITY_CLASSES = ("LOW", "HIGH")

# Crop / framing only. Ranges stay conservative so EfficientNet embedding
# cosine similarity typically remains >= MATCH_THRESHOLD (0.85).
VARIANT_SPECS: list[dict] = [
    {
        "filename": "obs_01.jpg",
        "role": "baseline",
        "scale": 1.0,
        "offset_x_frac": 0.0,
        "offset_y_frac": 0.0,
    },
    {
        "filename": "obs_02.jpg",
        "role": "follow_up_a",
        # Slightly tighter crop, nudged up-right
        "scale": 0.98,
        "offset_x_frac": 0.010,
        "offset_y_frac": -0.008,
    },
    {
        "filename": "obs_03.jpg",
        "role": "follow_up_b",
        # Another framing: a bit tighter, nudged down-left
        "scale": 0.97,
        "offset_x_frac": -0.008,
        "offset_y_frac": 0.010,
    },
]


def list_images(folder: Path) -> list[Path]:
    if not folder.is_dir():
        return []
    files = [
        path
        for path in folder.iterdir()
        if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS
    ]
    return sorted(files, key=lambda path: path.name.lower())


def clamp(value: int, low: int, high: int) -> int:
    return max(low, min(high, value))


def make_crop_variant(
    image: Image.Image,
    *,
    scale: float,
    offset_x_frac: float = 0.0,
    offset_y_frac: float = 0.0,
) -> Image.Image:
    """Same leaf, different framing only. No photometric or geometric warps."""
    if abs(scale - 1.0) < 1e-6 and abs(offset_x_frac) < 1e-9 and abs(offset_y_frac) < 1e-9:
        return image.copy()

    width, height = image.size
    crop_w = clamp(int(round(width * scale)), 8, width)
    crop_h = clamp(int(round(height * scale)), 8, height)
    dx = int(round(width * offset_x_frac))
    dy = int(round(height * offset_y_frac))

    left = clamp((width - crop_w) // 2 + dx, 0, width - crop_w)
    top = clamp((height - crop_h) // 2 + dy, 0, height - crop_h)
    box = (left, top, left + crop_w, top + crop_h)

    # Resize crop back to original size so framing differs without changing
    # output resolution used by the monitoring upload flow.
    return image.crop(box).resize((width, height), Image.Resampling.BICUBIC)


def relative_to_project(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(PROJECT_ROOT)).replace("\\", "/")
    except ValueError:
        return str(path)


def write_case_readme(case_dir: Path, meta: dict) -> None:
    text = f"""# Observation demo case: `{meta["case_id"]}`

## Important

These three images are **crop/framing variants of one source leaf photograph**
from the severity CNN test split (`{meta["severity_class"]}`).

They support Observation Monitoring demos (upload Obs 1 → 2 → 3, visual
consistency, trend UI). They do **not** prove biological same-plant identity
or multi-day field progression.

## Suggested upload order

1. `obs_01.jpg` — original / reference
2. `obs_02.jpg` — same leaf, slightly different crop
3. `obs_03.jpg` — same leaf, another slight crop / framing

## Source

- Severity class: `{meta["severity_class"]}`
- Source file: `{meta["source_filename"]}`
- Source relative path: `{meta["source_relative"]}`
- Generated (UTC): `{meta["generated_at_utc"]}`
"""
    (case_dir / "README.md").write_text(text, encoding="utf-8")


def write_kit_readme(output_root: Path, summary: dict) -> None:
    text = f"""# Observation sequence demo kit

Generated: `{summary["generated_at_utc"]}` (UTC)

## Purpose

Build short **monitoring-case image sequences** for the Observation-Based
Disease Severity and Recovery Monitoring component when a true same-plant
time series is not available in the public severity dataset.

## Method

For each selected source image under
`Tomato_Severity_Dataset/data/processed/cnn_severity_dataset/test/{{LOW|HIGH}}`:

- `obs_01.jpg` = original image (copied when source is JPEG)
- `obs_02.jpg` = same leaf, slightly different crop / framing
- `obs_03.jpg` = same leaf, another slight crop / framing

No lighting, brightness, contrast, color, rotation, perspective, blur, or
noise changes. Disease pattern is not redrawn. Crops stay conservative so
embedding cosine similarity typically remains ≥ 0.85 (MATCH).

Source dataset files are **never modified**. No model is trained.

## Honesty statement (reports / viva)

> Demo observation sequences were produced as crop/framing variants of a
> single severity-dataset image per monitoring case. This validates the
> observation pipeline and visual-consistency behaviour. It is not a claim of
> multi-day same-plant field capture.

## Layout

```text
observation_sequences/
  README.md
  kit_manifest.csv
  kit_summary.json
  case_LOW_01/
    obs_01.jpg  obs_02.jpg  obs_03.jpg
    README.md
    case_meta.json
  case_HIGH_01/
    ...
  mismatch/
    other_leaf.jpg
```

## How to use in the app

1. Start backend + frontend as usual.
2. Create a **LEAF** monitoring case.
3. Upload `obs_01.jpg`, then `obs_02.jpg`, then `obs_03.jpg` from one `case_*` folder.
4. For mismatch demos, use `mismatch/other_leaf.jpg` (different source leaf).

## Regenerate

From `Disease_Monitoring`:

```text
python scripts/build_observation_demo_kit.py
python scripts/build_observation_demo_kit.py --cases-per-class 2 --clean
```

## Summary

- Cases generated: {summary["cases_generated"]}
- Mismatch sample: {summary.get("mismatch_filename") or "none"}
"""
    (output_root / "README.md").write_text(text, encoding="utf-8")


def build_case(
    source: Path,
    case_dir: Path,
    *,
    case_id: str,
    severity_class: str,
) -> dict:
    case_dir.mkdir(parents=True, exist_ok=True)
    image = Image.open(source).convert("RGB")

    observation_rows: list[dict] = []
    for spec in VARIANT_SPECS:
        out_path = case_dir / spec["filename"]
        scale = float(spec["scale"])
        ox = float(spec.get("offset_x_frac", 0.0))
        oy = float(spec.get("offset_y_frac", 0.0))

        if spec["role"] == "baseline":
            # Keep the original bytes when the source is already JPEG.
            if source.suffix.lower() in {".jpg", ".jpeg"}:
                shutil.copy2(source, out_path)
            else:
                image.save(out_path, format="JPEG", quality=95, optimize=True)
        else:
            variant = make_crop_variant(
                image,
                scale=scale,
                offset_x_frac=ox,
                offset_y_frac=oy,
            )
            variant.save(out_path, format="JPEG", quality=95, optimize=True)

        observation_rows.append(
            {
                "filename": spec["filename"],
                "role": spec["role"],
                "scale": scale,
                "offset_x_frac": ox,
                "offset_y_frac": oy,
                "method": "original_copy" if spec["role"] == "baseline" else "crop_framing",
            }
        )

    meta = {
        "case_id": case_id,
        "severity_class": severity_class,
        "source_filename": source.name,
        "source_relative": relative_to_project(source),
        "source_absolute": str(source.resolve()),
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "claim": (
            "monitoring_case_crop_variants_from_single_source_image;"
            "not_biological_same_plant_identity"
        ),
        "observations": observation_rows,
    }
    (case_dir / "case_meta.json").write_text(
        json.dumps(meta, indent=2) + "\n", encoding="utf-8"
    )
    write_case_readme(case_dir, meta)
    return meta


def pick_sources(images: list[Path], count: int) -> list[Path]:
    if not images:
        return []
    if count >= len(images):
        return images[:count]
    if count == 1:
        return [images[0]]

    step = (len(images) - 1) / (count - 1)
    indices = [int(round(i * step)) for i in range(count)]
    picked: list[Path] = []
    seen: set[int] = set()
    for idx in indices:
        if idx not in seen:
            seen.add(idx)
            picked.append(images[idx])
    for image in images:
        if len(picked) >= count:
            break
        if image not in picked:
            picked.append(image)
    return picked[:count]


def clean_output_tree(output_root: Path) -> None:
    if not output_root.exists():
        return
    for child in output_root.iterdir():
        if child.is_dir() and (
            child.name.startswith("case_") or child.name == "mismatch"
        ):
            shutil.rmtree(child)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build observation demo sequences (obs_01..obs_03) from "
            "cnn_severity_dataset test LOW/HIGH images using crop/framing "
            "only. Does not train models or modify the source dataset."
        )
    )
    parser.add_argument(
        "--source-root",
        type=Path,
        default=DEFAULT_SOURCE_ROOT,
        help="Folder containing LOW/ and HIGH/ (default: cnn_severity_dataset/test)",
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=DEFAULT_OUTPUT_ROOT,
        help="Output directory for demo sequences",
    )
    parser.add_argument(
        "--cases-per-class",
        type=int,
        default=1,
        help="Number of monitoring cases per severity class (default: 1)",
    )
    parser.add_argument(
        "--classes",
        nargs="+",
        choices=list(SEVERITY_CLASSES),
        default=list(SEVERITY_CLASSES),
        help="Severity classes to include (default: LOW HIGH)",
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Remove existing case_* and mismatch folders under output-root",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    source_root: Path = args.source_root
    output_root: Path = args.output_root
    cases_per_class = max(1, int(args.cases_per_class))

    if not source_root.is_dir():
        print(f"ERROR: source root not found: {source_root}", file=sys.stderr)
        print(
            "Ensure Tomato_Severity_Dataset/.../cnn_severity_dataset/test exists.",
            file=sys.stderr,
        )
        return 1

    if args.clean:
        clean_output_tree(output_root)

    output_root.mkdir(parents=True, exist_ok=True)

    manifest_rows: list[dict] = []
    cases_meta: list[dict] = []
    used_sources: set[Path] = set()

    for severity in args.classes:
        class_dir = source_root / severity
        images = list_images(class_dir)
        if not images:
            print(f"WARNING: no images in {class_dir}", file=sys.stderr)
            continue

        for index, source in enumerate(pick_sources(images, cases_per_class), start=1):
            case_id = f"case_{severity}_{index:02d}"
            case_dir = output_root / case_id
            meta = build_case(
                source,
                case_dir,
                case_id=case_id,
                severity_class=severity,
            )
            cases_meta.append(meta)
            used_sources.add(source.resolve())
            for obs in meta["observations"]:
                manifest_rows.append(
                    {
                        "case_id": case_id,
                        "severity_class": severity,
                        "observation_file": obs["filename"],
                        "role": obs["role"],
                        "source_filename": source.name,
                        "output_path": relative_to_project(case_dir / obs["filename"]),
                    }
                )
            print(f"OK  {case_id}  <-  {severity}/{source.name}")

    mismatch_dir = output_root / "mismatch"
    mismatch_dir.mkdir(parents=True, exist_ok=True)
    mismatch_source: Path | None = None
    for severity in SEVERITY_CLASSES:
        for candidate in list_images(source_root / severity):
            if candidate.resolve() not in used_sources:
                mismatch_source = candidate
                break
        if mismatch_source is not None:
            break
    if mismatch_source is None:
        for severity in SEVERITY_CLASSES:
            imgs = list_images(source_root / severity)
            if imgs:
                mismatch_source = imgs[-1]
                break

    mismatch_name = ""
    if mismatch_source is not None:
        mismatch_name = "other_leaf.jpg"
        if mismatch_source.suffix.lower() in {".jpg", ".jpeg"}:
            shutil.copy2(mismatch_source, mismatch_dir / mismatch_name)
        else:
            Image.open(mismatch_source).convert("RGB").save(
                mismatch_dir / mismatch_name,
                format="JPEG",
                quality=95,
                optimize=True,
            )
        (mismatch_dir / "README.md").write_text(
            f"""# Mismatch sample

Copy of a **different** source leaf (`{mismatch_source.name}`) for
MISMATCH / confirm-flow demos.

Do not mix this file into a `case_*` sequence if you want a MATCH demo.
""",
            encoding="utf-8",
        )
        print(f"OK  mismatch/{mismatch_name}  <-  {mismatch_source.name}")

    generated_at = datetime.now(timezone.utc).isoformat()
    summary = {
        "generated_at_utc": generated_at,
        "source_root": str(source_root),
        "output_root": str(output_root),
        "cases_generated": len(cases_meta),
        "mismatch_filename": mismatch_name or None,
        "disclaimer": (
            "Sequences are single-image crop/framing variants for monitoring "
            "demos; not biological same-plant time series."
        ),
        "transform_ranges": {
            "method": "crop_framing_only",
            "obs_01": "original_copy",
            "obs_02": "scale=0.98, offset≈(+1.0%, -0.8%)",
            "obs_03": "scale=0.97, offset≈(-0.8%, +1.0%)",
            "disabled": "lighting, brightness, contrast, color, rotation, perspective, blur, noise",
        },
        "cases": [
            {
                "case_id": item["case_id"],
                "severity_class": item["severity_class"],
                "source_filename": item["source_filename"],
            }
            for item in cases_meta
        ],
    }

    manifest_path = output_root / "kit_manifest.csv"
    with manifest_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
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
        writer.writerows(manifest_rows)

    (output_root / "kit_summary.json").write_text(
        json.dumps(summary, indent=2) + "\n",
        encoding="utf-8",
    )
    write_kit_readme(output_root, summary)

    gitignore = output_root / ".gitignore"
    if not gitignore.exists():
        gitignore.write_text(
            "# Generated demo images — regenerate with scripts/build_observation_demo_kit.py\n"
            "case_*/\n"
            "mismatch/\n"
            "kit_manifest.csv\n"
            "kit_summary.json\n",
            encoding="utf-8",
        )

    print()
    print(f"Wrote kit -> {output_root}")
    print(f"Cases: {len(cases_meta)} | Manifest: {manifest_path.name}")
    return 0 if cases_meta else 2


if __name__ == "__main__":
    raise SystemExit(main())
