"""
Retrain yolov8n-cls on the leak-free split built by scripts/resplit_by_source.py.

Hyperparameters are the same as notebooks/train_tobacco_model.py (imgsz=224,
50 epochs, patience 10, AdamW, lr0=0.001, same augmentation, seed 42) so the
only change is the split. Runs on CPU or GPU.

    python scripts/resplit_by_source.py --out dataset_clean
    python scripts/train_clean_split.py --data dataset_clean
"""
import argparse

import torch
from ultralytics import YOLO


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="dataset_clean")
    ap.add_argument("--epochs", type=int, default=50)
    ap.add_argument("--batch", type=int, default=32)
    ap.add_argument("--device", default="0" if torch.cuda.is_available() else "cpu")
    ap.add_argument("--workers", type=int, default=2)
    ap.add_argument("--name", default="tobacco_cls_clean_split")
    args = ap.parse_args()

    model = YOLO("yolov8n-cls.pt")
    model.train(
        data=args.data,
        epochs=args.epochs,
        imgsz=224,
        batch=args.batch,
        patience=10,
        optimizer="AdamW",
        lr0=0.001,
        lrf=0.01,
        weight_decay=0.0005,
        warmup_epochs=3,
        augment=True,
        hsv_h=0.015,
        hsv_s=0.7,
        hsv_v=0.4,
        degrees=15.0,
        translate=0.1,
        scale=0.5,
        flipud=0.1,
        fliplr=0.5,
        mosaic=0.0,
        project="runs/classify",
        name=args.name,
        exist_ok=True,
        seed=42,
        deterministic=True,
        device=args.device,
        workers=args.workers,
        plots=False,
    )


if __name__ == "__main__":
    main()
