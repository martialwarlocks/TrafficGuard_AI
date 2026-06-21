#!/usr/bin/env python3
"""Prepare and convert datasets for YOLO training."""

import argparse
import json
import random
import shutil
from pathlib import Path


CLASS_MAPPING = {
    "person": 0, "bicycle": 1, "car": 2, "motorcycle": 3,
    "bus": 4, "truck": 5, "helmet": 6, "no_helmet": 7,
    "seatbelt": 8, "no_seatbelt": 9, "license_plate": 10,
}


def create_yolo_structure(output_dir: Path):
    for split in ("train", "val", "test"):
        (output_dir / "images" / split).mkdir(parents=True, exist_ok=True)
        (output_dir / "labels" / split).mkdir(parents=True, exist_ok=True)


def generate_data_yaml(output_dir: Path):
    yaml_content = f"""path: {output_dir.absolute()}
train: images/train
val: images/val
test: images/test

nc: {len(CLASS_MAPPING)}
names: {list(CLASS_MAPPING.keys())}
"""
    (output_dir / "data.yaml").write_text(yaml_content)


def split_dataset(raw_dir: Path, output_dir: Path, val_ratio: float = 0.15, test_ratio: float = 0.10):
    images = list(raw_dir.rglob("*.jpg")) + list(raw_dir.rglob("*.png"))
    random.shuffle(images)

    n = len(images)
    n_test = int(n * test_ratio)
    n_val = int(n * val_ratio)

    splits = {
        "test": images[:n_test],
        "val": images[n_test:n_test + n_val],
        "train": images[n_test + n_val:],
    }

    for split, files in splits.items():
        for img_path in files:
            dest = output_dir / "images" / split / img_path.name
            shutil.copy2(img_path, dest)
            label_path = img_path.with_suffix(".txt")
            if label_path.exists():
                shutil.copy2(label_path, output_dir / "labels" / split / label_path.name)

    stats = {s: len(f) for s, f in splits.items()}
    (output_dir / "split_stats.json").write_text(json.dumps(stats, indent=2))
    print(f"Split complete: {stats}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw", default="datasets/raw")
    parser.add_argument("--output", default="datasets/processed")
    args = parser.parse_args()

    raw_dir = Path(args.raw)
    output_dir = Path(args.output)

    create_yolo_structure(output_dir)
    generate_data_yaml(output_dir)

    if raw_dir.exists():
        split_dataset(raw_dir, output_dir)
    else:
        print(f"Raw directory not found: {raw_dir}. Created empty YOLO structure.")

    print(f"Prepared dataset at {output_dir}")


if __name__ == "__main__":
    main()
