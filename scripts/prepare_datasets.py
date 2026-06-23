#!/usr/bin/env python3
"""Prepare and merge datasets for YOLO training with unified class mapping."""

import argparse
import json
import random
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Unified TrafficGuard class IDs
CLASS_MAPPING = {
    "person": 0,
    "bicycle": 1,
    "car": 2,
    "motorcycle": 3,
    "bus": 4,
    "truck": 5,
    "helmet": 6,
    "no_helmet": 7,
    "seatbelt": 8,
    "no_seatbelt": 9,
    "license_plate": 10,
    "traffic_light_red": 11,
    "traffic_light_green": 12,
    "traffic_light_yellow": 13,
}

# Map external dataset class names -> our classes
ALIAS_MAP = {
    # Helmet datasets
    "with helmet": "helmet",
    "with_helmet": "helmet",
    "helmet": "helmet",
    "helmet_on": "helmet",
    "wearing helmet": "helmet",
    "without helmet": "no_helmet",
    "without_helmet": "no_helmet",
    "no_helmet": "no_helmet",
    "no helmet": "no_helmet",
    "no-helmet": "no_helmet",
    "nohelmet": "no_helmet",
    "head": "no_helmet",
    "human head": "no_helmet",
    "human_head": "no_helmet",
    "vehicle registration plate": "license_plate",
    # Traffic lights
    "red": "traffic_light_red",
    "red-light": "traffic_light_red",
    "red_light": "traffic_light_red",
    "traffic light red": "traffic_light_red",
    "traffic-light-red": "traffic_light_red",
    "green": "traffic_light_green",
    "green-light": "traffic_light_green",
    "green_light": "traffic_light_green",
    "traffic light green": "traffic_light_green",
    "yellow": "traffic_light_yellow",
    "yellow-light": "traffic_light_yellow",
    "traffic light": "traffic_light_yellow",
    "traffic_light": "traffic_light_yellow",
    # Vehicles
    "motorbike": "motorcycle",
    "bike": "bicycle",
    "van": "car",
    "coach": "bus",
    "tricycle": "motorcycle",
    "jeep": "car",
    "numberplate": "license_plate",
    "number_plate": "license_plate",
    "license plate": "license_plate",
    "plate": "license_plate",
    # COCO passthrough
    "person": "person",
    "bicycle": "bicycle",
    "car": "car",
    "motorcycle": "motorcycle",
    "bus": "bus",
    "truck": "truck",
}


def create_yolo_structure(output_dir: Path):
    for split in ("train", "val", "test"):
        (output_dir / "images" / split).mkdir(parents=True, exist_ok=True)
        (output_dir / "labels" / split).mkdir(parents=True, exist_ok=True)


def generate_data_yaml(output_dir: Path):
    names = [None] * len(CLASS_MAPPING)
    for name, idx in CLASS_MAPPING.items():
        names[idx] = name
    yaml_content = f"""path: {output_dir.absolute()}
train: images/train
val: images/val
test: images/test

nc: {len(CLASS_MAPPING)}
names: {names}
"""
    (output_dir / "data.yaml").write_text(yaml_content)


def normalize_class(name: str) -> str | None:
    key = name.strip().lower().replace("-", "_")
    key = key.replace(" ", "_")
    if key in CLASS_MAPPING:
        return key
    if key in ALIAS_MAP:
        return ALIAS_MAP[key]
    low = name.strip().lower()
    if "truck" in low or "trailer" in low or "tractor" in low or "firetruck" in low:
        return "truck"
    if "bus" in low:
        return "bus"
    if low in ("car", "auto", "minivan", "van", "lcv", "jeep", "handcart", "hcm_eme", "ambulance"):
        return "truck" if low == "ambulance" else "car"
    if "motorcycle" in low or "motorbike" in low or "tricycle" in low:
        return "motorcycle"
    if "bicycle" in low or low == "bike":
        return "bicycle"
    if low == "green":
        return "traffic_light_green"
    if low == "red":
        return "traffic_light_red"
    if low == "yellow":
        return "traffic_light_yellow"
    for alias, mapped in ALIAS_MAP.items():
        if alias.replace("_", " ") in low or low in alias.replace("_", " "):
            return mapped
    return None


def remap_label_file(label_path: Path, class_names: dict[int, str] | None) -> list[str]:
    lines = []
    for line in label_path.read_text().strip().splitlines():
        parts = line.split()
        if len(parts) < 5:
            continue
        cls_id = int(parts[0])
        if class_names and cls_id in class_names:
            raw_name = class_names[cls_id]
        else:
            raw_name = str(cls_id)
        mapped = normalize_class(raw_name) if not str(raw_name).isdigit() else None
        if mapped is None and class_names is None:
            continue
        if mapped is None:
            mapped = normalize_class(str(raw_name))
        if mapped is None:
            continue
        new_id = CLASS_MAPPING[mapped]
        lines.append(f"{new_id} {' '.join(parts[1:])}")
    return lines


def load_yaml_names(yaml_path: Path) -> dict[int, str]:
    names: dict[int, str] = {}
    if not yaml_path.exists():
        return names
    text = yaml_path.read_text()
    import re
    m = re.search(r"names:\s*\[(.*?)\]", text, re.DOTALL)
    if m:
        import ast
        try:
            lst = ast.literal_eval("[" + m.group(1) + "]")
            for i, n in enumerate(lst):
                names[i] = str(n).strip("'\"")
            return names
        except Exception:
            pass
    in_names = False
    idx = 0
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("names:"):
            val = stripped.split(":", 1)[1].strip()
            if val.startswith("["):
                continue
            in_names = True
            continue
        if in_names and stripped.startswith("- "):
            names[idx] = stripped[2:].strip()
            idx += 1
        elif in_names and stripped and not stripped.startswith("#") and ":" in stripped:
            in_names = False
    return names


def ingest_roboflow_folder(src: Path, output_dir: Path, split_map: dict[str, str]):
    yaml_path = src / "data.yaml"
    if not yaml_path.exists():
        for sub in src.iterdir():
            if (sub / "data.yaml").exists():
                src = sub
                yaml_path = sub / "data.yaml"
                break

    class_names = load_yaml_names(yaml_path)
    # Roboflow also embeds names in train folder structure
    for rob_split, our_split in split_map.items():
        img_dir = src / rob_split / "images" if (src / rob_split / "images").exists() else src / rob_split
        lbl_dir = src / rob_split / "labels" if (src / rob_split / "labels").exists() else src / rob_split
        if not img_dir.exists():
            continue
        for img in list(img_dir.glob("*.jpg")) + list(img_dir.glob("*.png")):
            lbl = lbl_dir / (img.stem + ".txt")
            if not lbl.exists():
                lbl = img.with_suffix(".txt")
            if not lbl.exists():
                continue
            new_lines = remap_label_file(lbl, class_names)
            if not new_lines:
                continue
            dest_img = output_dir / "images" / our_split / f"{src.name}_{img.name}"
            dest_lbl = output_dir / "labels" / our_split / f"{src.name}_{img.stem}.txt"
            shutil.copy2(img, dest_img)
            dest_lbl.write_text("\n".join(new_lines) + "\n")
        count = len(list((output_dir / "images" / our_split).glob(f"{src.name}_*")))
        if count:
            print(f"    {src.name}/{our_split}: {count} images")


def ingest_github_helmet(src: Path, output_dir: Path):
    """Ingest GitHub YOLO helmet repo (images/ + labels/ layout)."""
    classes_file = src / "labels" / "classes.txt"
    if not classes_file.exists():
        classes_file = src / "classes.txt"
    class_list = []
    if classes_file.exists():
        class_list = [c.strip() for c in classes_file.read_text().splitlines() if c.strip()]
    cn = {i: class_list[i] for i in range(len(class_list))}

    img_dir = src / "images" if (src / "images").exists() else src
    lbl_dir = src / "labels" if (src / "labels").exists() else src

    pairs = []
    for lbl in lbl_dir.glob("*.txt"):
        if lbl.name == "classes.txt":
            continue
        img = img_dir / (lbl.stem + ".jpg")
        if not img.exists():
            img = img_dir / (lbl.stem + ".png")
        if img.exists():
            pairs.append((img, lbl))

    random.shuffle(pairs)
    n = len(pairs)
    n_test = max(1, int(n * 0.08))
    n_val = max(1, int(n * 0.12))
    splits = {
        "test": pairs[:n_test],
        "val": pairs[n_test:n_test + n_val],
        "train": pairs[n_test + n_val:],
    }
    for split, items in splits.items():
        for img, lbl in items:
            new_lines = remap_label_file(lbl, cn if cn else None)
            if not new_lines:
                continue
            dest_img = output_dir / "images" / split / f"gh_{img.name}"
            dest_lbl = output_dir / "labels" / split / f"gh_{lbl.stem}.txt"
            shutil.copy2(img, dest_img)
            dest_lbl.write_text("\n".join(new_lines) + "\n")
    print(f"  GitHub helmet: {n} image-label pairs")


def merge_all(raw_dir: Path, output_dir: Path):
    create_yolo_structure(output_dir)
    split_map = {"train": "train", "valid": "val", "val": "val", "test": "test"}

    roboflow_dir = raw_dir / "roboflow"
    if roboflow_dir.exists():
        for sub in roboflow_dir.iterdir():
            if sub.is_dir():
                print(f"  Merging Roboflow: {sub.name}")
                ingest_roboflow_folder(sub, output_dir, split_map)

    gh = raw_dir / "github" / "helmet_yolo_github"
    if gh.exists():
        print("  Merging GitHub helmet dataset")
        ingest_github_helmet(gh, output_dir)

    stats = {}
    for split in ("train", "val", "test"):
        stats[split] = len(list((output_dir / "images" / split).glob("*")))
    (output_dir / "split_stats.json").write_text(json.dumps(stats, indent=2))
    print(f"  Merged dataset stats: {stats}")
    return stats


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
    parser.add_argument("--merge", action="store_true", help="Merge Roboflow + GitHub into unified dataset")
    args = parser.parse_args()

    raw_dir = Path(args.raw)
    output_dir = Path(args.output)

    if args.merge:
        if output_dir.exists():
            shutil.rmtree(output_dir)
        merge_all(raw_dir, output_dir)
        generate_data_yaml(output_dir)
    else:
        create_yolo_structure(output_dir)
        generate_data_yaml(output_dir)
        if raw_dir.exists():
            split_dataset(raw_dir, output_dir)

    print(f"Prepared dataset at {output_dir}")
    stats_path = output_dir / "split_stats.json"
    if stats_path.exists():
        print(stats_path.read_text())


if __name__ == "__main__":
    main()
