#!/usr/bin/env python3
"""Benchmark model inference latency and throughput."""

import argparse
import json
import time
from pathlib import Path

import cv2
import numpy as np


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="ml/models/yolov8s.pt")
    parser.add_argument("--image", default=None)
    parser.add_argument("--runs", type=int, default=100)
    parser.add_argument("--output", default="ml/models/benchmark.json")
    args = parser.parse_args()

    from ultralytics import YOLO

    model_path = args.model if Path(args.model).exists() else "yolov8s.pt"
    model = YOLO(model_path)

    if args.image and Path(args.image).exists():
        image = cv2.imread(args.image)
    else:
        image = np.random.randint(0, 255, (640, 640, 3), dtype=np.uint8)

    latencies = []
    for _ in range(args.runs):
        start = time.perf_counter()
        model(image, verbose=False)
        latencies.append((time.perf_counter() - start) * 1000)

    avg_latency = sum(latencies) / len(latencies)
    p95 = sorted(latencies)[int(len(latencies) * 0.95)]
    fps = 1000 / avg_latency

    results = {
        "avg_latency_ms": round(avg_latency, 2),
        "p95_latency_ms": round(p95, 2),
        "fps": round(fps, 2),
        "runs": args.runs,
        "model": model_path,
    }

    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output).write_text(json.dumps(results, indent=2))
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
