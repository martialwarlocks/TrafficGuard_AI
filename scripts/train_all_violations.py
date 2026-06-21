#!/usr/bin/env python3
"""
Train YOLOv8 for all TrafficGuard violation categories.

Classes (11 detection + violation context):
  person, bicycle, car, motorcycle, bus, truck,
  helmet, no_helmet, seatbelt, no_seatbelt, license_plate

Violation modules (7 enforcement categories):
  red_light, stop_line, helmet, seatbelt, triple_riding, wrong_side, parking

Usage:
  python scripts/prepare_datasets.py
  python scripts/train_all_violations.py --epochs 100
"""

import argparse
from pathlib import Path

VIOLATION_CLASSES = [
    "person", "bicycle", "car", "motorcycle", "bus", "truck",
    "helmet", "no_helmet", "seatbelt", "no_seatbelt", "license_plate",
]

RECOMMENDED_DATASETS = {
    "red_light": ["BDD100K (traffic scenes)", "UA-DETRAC", "Roboflow traffic signal datasets"],
    "stop_line": ["BDD100K", "Open Images V7 (crosswalk)"],
    "helmet": ["Roboflow helmet detection", "Kaggle helmet datasets"],
    "seatbelt": ["Roboflow seatbelt detection", "Custom dashcam footage"],
    "triple_riding": ["Custom motorcycle annotation", "UA-DETRAC"],
    "wrong_side": ["BDD100K wrong-way detection", "Custom lane annotations"],
    "parking": ["PKLot", "Open Images parking meter"],
    "license_plate": ["CCPD", "UFPR-ALPR", "Open Images license plate"],
}


def write_data_yaml(output_dir: Path):
    yaml = f"""# TrafficGuard AI — Full Violation Detection Dataset
path: {output_dir.absolute()}
train: images/train
val: images/val
test: images/test

nc: {len(VIOLATION_CLASSES)}
names: {VIOLATION_CLASSES}

# Violation enforcement categories (post-processing modules):
# red_light, stop_line, helmet, seatbelt, triple_riding, wrong_side, parking
"""
    (output_dir / "data.yaml").write_text(yaml)
    print(f"Wrote {output_dir / 'data.yaml'}")


def main():
    parser = argparse.ArgumentParser(description="Train TrafficGuard YOLO on all violation classes")
    parser.add_argument("--data", default="datasets/processed/data.yaml")
    parser.add_argument("--epochs", type=int, default=100)
    parser.add_argument("--batch", type=int, default=16)
    parser.add_argument("--imgsz", type=int, default=640)
    parser.add_argument("--model", default="yolov8s.pt")
    parser.add_argument("--output", default="ml/models")
    parser.add_argument("--init-only", action="store_true", help="Only create dataset structure")
    args = parser.parse_args()

    processed = Path("datasets/processed")
    processed.mkdir(parents=True, exist_ok=True)
    write_data_yaml(processed)

    if args.init_only:
        print("\nRecommended datasets per violation category:")
        for vtype, datasets in RECOMMENDED_DATASETS.items():
            print(f"  {vtype}: {', '.join(datasets)}")
        print("\nRun: python scripts/download_datasets.py")
        print("Then: python scripts/prepare_datasets.py")
        return

    data_path = Path(args.data)
    if not data_path.exists():
        print(f"Dataset not found at {data_path}. Run prepare_datasets.py first.")
        print("Creating empty structure — add labeled images to datasets/processed/images/train/")
        write_data_yaml(processed)
        return

    from ultralytics import YOLO

    print(f"Training on {VIOLATION_CLASSES}")
    print(f"Violation categories: {list(RECOMMENDED_DATASETS.keys())}")

    model = YOLO(args.model)
    model.train(
        data=str(data_path),
        epochs=args.epochs,
        batch=args.batch,
        imgsz=args.imgsz,
        project=args.output,
        name="trafficguard_v8_all_violations",
        patience=25,
        save=True,
        augment=True,
        mosaic=1.0,
        mixup=0.15,
        degrees=5.0,
        translate=0.1,
        scale=0.5,
        fliplr=0.5,
        hsv_h=0.015,
        hsv_s=0.7,
        hsv_v=0.4,
    )

    best = Path(args.output) / "trafficguard_v8_all_violations" / "weights" / "best.pt"
    dest = Path(args.output) / "yolov8s_traffic.pt"
    if best.exists():
        import shutil
        shutil.copy2(best, dest)
        print(f"\nModel saved to {dest}")
        print("Update YOLO_MODEL_PATH=ml/models/yolov8s_traffic.pt in .env")


if __name__ == "__main__":
    main()
