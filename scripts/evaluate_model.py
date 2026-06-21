#!/usr/bin/env python3
"""Evaluate trained YOLO model."""

import argparse
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="ml/models/yolov8s_traffic.pt")
    parser.add_argument("--data", default="datasets/processed/data.yaml")
    parser.add_argument("--output", default="ml/models/evaluation.json")
    args = parser.parse_args()

    from ultralytics import YOLO

    model_path = args.model if Path(args.model).exists() else "yolov8s.pt"
    model = YOLO(model_path)

    metrics = model.val(data=args.data, split="test")

    results = {
        "precision": float(metrics.box.mp),
        "recall": float(metrics.box.mr),
        "map50": float(metrics.box.map50),
        "map50_95": float(metrics.box.map),
        "f1": float(2 * metrics.box.mp * metrics.box.mr / max(metrics.box.mp + metrics.box.mr, 1e-6)),
    }

    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output).write_text(json.dumps(results, indent=2))
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
