#!/usr/bin/env python3
"""Download traffic violation detection datasets."""

import argparse
import os
import subprocess
import sys
from pathlib import Path

DATASETS = {
    "bdd100k": {
        "url": "https://bdd-data.berkeley.edu/bdd100k_images.zip",
        "description": "Berkeley DeepDrive 100K - driving scenes",
    },
    "ua_detrac": {
        "url": "http://detrac-db.rit.albany.edu/download/DETRAC-Train-Images-Part1.zip",
        "description": "UA-DETRAC vehicle tracking dataset",
    },
    "openimages": {
        "url": "https://storage.googleapis.com/openimages/web/index.html",
        "description": "Open Images V7 - use OID toolkit for download",
        "manual": True,
    },
    "ccpd": {
        "url": "https://github.com/detectRecog/CCPD",
        "description": "Chinese City Parking Dataset - license plates",
        "git": True,
    },
    "ufpr_alpr": {
        "url": "http://web.inf.ufpr.br/vri/databases/vehicle-license-plate-recognition/",
        "description": "UFPR-ALPR license plate dataset",
        "manual": True,
    },
    "helmet": {
        "url": "https://universe.roboflow.com/search?q=helmet+detection",
        "description": "Roboflow helmet detection datasets",
        "manual": True,
    },
}


def download_file(url: str, dest: Path):
    dest.parent.mkdir(parents=True, exist_ok=True)
    print(f"Downloading {url} -> {dest}")
    subprocess.run(["curl", "-L", "-o", str(dest), url], check=True)


def clone_repo(url: str, dest: Path):
    if dest.exists():
        print(f"Already exists: {dest}")
        return
    subprocess.run(["git", "clone", "--depth", "1", url, str(dest)], check=True)


def main():
    parser = argparse.ArgumentParser(description="Download TrafficGuard AI datasets")
    parser.add_argument("--dataset", choices=list(DATASETS.keys()) + ["all"], default="all")
    parser.add_argument("--output", default="datasets/raw")
    args = parser.parse_args()

    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)

    targets = DATASETS.keys() if args.dataset == "all" else [args.dataset]

    for name in targets:
        info = DATASETS[name]
        print(f"\n{'='*60}\nDataset: {name}\n{info['description']}\n{'='*60}")

        if info.get("manual"):
            print(f"  Manual download required: {info['url']}")
            continue

        dest = output / name
        dest.mkdir(exist_ok=True)

        if info.get("git"):
            clone_repo(info["url"], dest)
        else:
            filename = info["url"].split("/")[-1]
            download_file(info["url"], dest / filename)

    print("\nDownload complete. Run prepare_datasets.py next.")


if __name__ == "__main__":
    main()
