#!/usr/bin/env python3
"""
Download curated traffic-violation datasets for YOLO training.

Sources (best public datasets):
  - Roboflow: Vietnam Traffic Light (2666 imgs), Helmet Detection (4169 imgs)
  - GitHub: Helmet/No-Helmet YOLO annotations (~2000 imgs)

Set ROBOFLOW_API_KEY in .env (free at https://app.roboflow.com/settings/api).

Usage:
  python scripts/download_training_data.py
  python scripts/download_training_data.py --skip-roboflow
"""

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "datasets" / "raw"

ROBOFLOW_DATASETS = [
    {
        "name": "vehicles_car_bike",
        "workspace": "tansam-uunrl",
        "project": "vehicle-detection-3",
        "version": 1,
        "description": "Vehicle Detection 3 — Car, Bicycle, Motorcycle",
    },
    {
        "name": "vehicles_karyn",
        "workspace": "karyn",
        "project": "vehicle-detection-fw6w1",
        "version": 1,
        "description": "Vehicle Detection — Car, Truck, Motorcycle (1.8k imgs)",
    },
    {
        "name": "vehicles_detect",
        "workspace": "yolov8-rbuqm",
        "project": "detect-vehicles-utnre",
        "version": 1,
        "description": "Detect Vehicles — 3.6k images, car/truck/van",
    },
    {
        "name": "traffic_lights",
        "workspace": "mxhuy0606",
        "project": "vietnam-traffic-light",
        "version": 4,
        "description": "Vietnam Traffic Light — 2666 images, red/green/yellow",
    },
    {
        "name": "helmet",
        "workspace": "learning-evidence",
        "project": "helmet-detection_yolov8",
        "version": 3,
        "description": "Helmet Detection — 4169 images, with/without helmet",
    },
    {
        "name": "bike_helmet",
        "workspace": "yolo-eimze",
        "project": "bike-helmet-detection-2vdjo-9n2oh",
        "version": 1,
        "description": "Bike Helmet Detection — 1371 images",
    },
]

GITHUB_DATASETS = [
    {
        "name": "helmet_yolo_github",
        "url": "https://github.com/TheSiddheshFulawade/YOLO-dataset-with-annotations-for-Helmet-No-Helmet-Motorcycles-and-Numberplates.git",
        "description": "Helmet + motorcycle + numberplate YOLO labels",
    },
]


def run(cmd: list[str], cwd: Path | None = None):
    print(f"  $ {' '.join(cmd)}")
    subprocess.run(cmd, check=True, cwd=cwd or ROOT)


def load_env_key() -> str | None:
    key = os.environ.get("ROBOFLOW_API_KEY")
    if key:
        return key
    env_file = ROOT / ".env"
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            if line.startswith("ROBOFLOW_API_KEY="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    return None


def download_roboflow(api_key: str):
    try:
        from roboflow import Roboflow
    except ImportError:
        print("Installing roboflow...")
        subprocess.run([sys.executable, "-m", "pip", "install", "roboflow", "-q"], check=True)
        from roboflow import Roboflow

    rf = Roboflow(api_key=api_key)
    dest_root = RAW / "roboflow"
    dest_root.mkdir(parents=True, exist_ok=True)

    for ds in ROBOFLOW_DATASETS:
        out = dest_root / ds["name"]
        if (out / "data.yaml").exists() or (out / "train").exists():
            print(f"  Skip {ds['name']} — already downloaded")
            continue
        print(f"\nDownloading Roboflow: {ds['description']}")
        try:
            project = rf.workspace(ds["workspace"]).project(ds["project"])
            dataset = project.version(ds["version"]).download("yolov8", location=str(out))
            print(f"  Saved to {dataset.location}")
        except Exception as e:
            print(f"  WARN: Failed {ds['name']}: {e}")


def download_github():
    gh_root = RAW / "github"
    gh_root.mkdir(parents=True, exist_ok=True)
    for ds in GITHUB_DATASETS:
        dest = gh_root / ds["name"]
        if dest.exists():
            print(f"  Skip {ds['name']} — already cloned")
            continue
        print(f"\nCloning: {ds['description']}")
        run(["git", "clone", "--depth", "1", ds["url"], str(dest)])


def download_coco_sample():
    """Download a small COCO traffic subset via ultralytics (auto-cached)."""
    print("\nPrefetching YOLOv8n COCO weights for traffic-light pretrain...")
    try:
        from ultralytics import YOLO
        YOLO("yolov8n.pt")
        print("  yolov8n.pt ready")
    except Exception as e:
        print(f"  WARN: {e}")


def main():
    parser = argparse.ArgumentParser(description="Download TrafficGuard training datasets")
    parser.add_argument("--skip-roboflow", action="store_true")
    parser.add_argument("--skip-github", action="store_true")
    args = parser.parse_args()

    RAW.mkdir(parents=True, exist_ok=True)
    print("=" * 60)
    print("TrafficGuard AI — Dataset Download")
    print("=" * 60)

    if not args.skip_github:
        download_github()

    api_key = load_env_key()
    if not args.skip_roboflow:
        if api_key and api_key not in ("", "your_roboflow_api_key"):
            download_roboflow(api_key)
        else:
            print("\n⚠ ROBOFLOW_API_KEY not set — skipping Roboflow datasets.")
            print("  Get free key: https://app.roboflow.com/settings/api")
            print("  Add to .env: ROBOFLOW_API_KEY=your_key_here")
            print("  Then re-run this script for 6800+ labeled images.")

    download_coco_sample()

    print("\n" + "=" * 60)
    print("Next: python scripts/prepare_datasets.py --merge")
    print("Then: python scripts/train_all_violations.py --epochs 50")
    print("=" * 60)


if __name__ == "__main__":
    main()
