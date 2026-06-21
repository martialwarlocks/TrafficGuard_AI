#!/usr/bin/env python3
"""Train YOLOv8s on prepared traffic violation dataset."""

import argparse
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", default="datasets/processed/data.yaml")
    parser.add_argument("--epochs", type=int, default=100)
    parser.add_argument("--batch", type=int, default=16)
    parser.add_argument("--imgsz", type=int, default=640)
    parser.add_argument("--model", default="yolov8s.pt")
    parser.add_argument("--output", default="ml/models")
    args = parser.parse_args()

    from ultralytics import YOLO

    model = YOLO(args.model)
    results = model.train(
        data=args.data,
        epochs=args.epochs,
        batch=args.batch,
        imgsz=args.imgsz,
        project=args.output,
        name="trafficguard_yolov8s",
        patience=20,
        save=True,
        device=0,
        augment=True,
        mosaic=1.0,
        mixup=0.1,
    )

    best_model = Path(args.output) / "trafficguard_yolov8s" / "weights" / "best.pt"
    dest = Path(args.output) / "yolov8s_traffic.pt"
    if best_model.exists():
        import shutil
        shutil.copy2(best_model, dest)
        print(f"Best model saved to {dest}")

    print(f"Training complete. Results: {results}")


if __name__ == "__main__":
    main()
