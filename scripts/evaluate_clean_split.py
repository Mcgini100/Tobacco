"""
Evaluate one or more YOLOv8-cls weights on the leak-free test split.

Reports, per model:
  * image-level accuracy, per-class precision/recall/F1, macro-F1, confusion matrix
  * group-level accuracy (probabilities averaged over all copies of a source photo),
    which counts each distinct photo once
  * the same metrics on the "unseen-by-original-model" subset: test groups whose
    images never appeared in the ORIGINAL Roboflow train split. Only this subset
    is a fair test for the old models/best.pt, which was trained on that split.

    python scripts/evaluate_clean_split.py --weights models/best.pt runs/.../best.pt
"""
from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path

import numpy as np
from sklearn.metrics import accuracy_score, confusion_matrix, precision_recall_fscore_support
from ultralytics import YOLO

ROOT = Path(__file__).resolve().parent.parent
CLASSES = ["alternaria_alternata", "cercospora_nicotianae", "healthy"]


def load_manifest(path: Path, split: str) -> list[dict]:
    with open(path, newline="") as fh:
        rows = list(csv.DictReader(fh))
    groups_in_original_train = {r["group"] for r in rows if r["original_split"] == "train"}
    out = [r for r in rows if r["new_split"] == split]
    for r in out:
        r["group_seen_in_original_train"] = r["group"] in groups_in_original_train
    return out


def metrics(y_true: list[int], y_pred: list[int]) -> dict:
    p, r, f, s = precision_recall_fscore_support(y_true, y_pred, labels=[0, 1, 2], zero_division=0)
    return {
        "n": len(y_true),
        "accuracy": round(float(accuracy_score(y_true, y_pred)), 4),
        "macro_f1": round(float(np.mean(f)), 4),
        "per_class": {
            c: {"precision": round(float(p[i]), 4), "recall": round(float(r[i]), 4),
                "f1": round(float(f[i]), 4), "support": int(s[i])}
            for i, c in enumerate(CLASSES)
        },
        "confusion_matrix": confusion_matrix(y_true, y_pred, labels=[0, 1, 2]).tolist(),
    }


def evaluate(weights: Path, rows: list[dict], batch: int = 32) -> dict:
    model = YOLO(str(weights))
    names = model.names  # {idx: class_name}
    order = [list(names.values()).index(c) for c in CLASSES]  # model idx for each CLASSES entry
    probs = []
    paths = [str(ROOT / r["path"]) for r in rows]
    for i in range(0, len(paths), batch):
        for res in model.predict(paths[i:i + batch], imgsz=224, verbose=False, device="cpu"):
            probs.append(res.probs.data.cpu().numpy()[order])
    probs = np.stack(probs)
    y_true = np.array([CLASSES.index(r["label"]) for r in rows])
    y_pred = probs.argmax(1)

    def group_level(mask: np.ndarray) -> dict:
        acc = defaultdict(list)
        for i in np.where(mask)[0]:
            acc[rows[i]["group"]].append(i)
        gt = [int(y_true[idx[0]]) for idx in acc.values()]
        gp = [int(probs[idx].mean(0).argmax()) for idx in acc.values()]
        return metrics(gt, gp)

    all_mask = np.ones(len(rows), bool)
    unseen = np.array([not r["group_seen_in_original_train"] for r in rows])
    return {
        "weights": str(weights),
        "image_level": metrics(y_true.tolist(), y_pred.tolist()),
        "group_level": group_level(all_mask),
        "unseen_subset_image_level": metrics(y_true[unseen].tolist(), y_pred[unseen].tolist()) if unseen.any() else None,
        "unseen_subset_group_level": group_level(unseen) if unseen.any() else None,
        "misclassified": [
            {"path": rows[i]["path"], "true": CLASSES[y_true[i]], "pred": CLASSES[y_pred[i]]}
            for i in np.where(y_true != y_pred)[0]
        ],
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--weights", nargs="+", required=True)
    ap.add_argument("--manifest", default="data_splits/source_split.csv")
    ap.add_argument("--split", default="test", choices=["train", "val", "test"])
    ap.add_argument("--out", default="data_splits/clean_split_results.json")
    args = ap.parse_args()

    rows = load_manifest(ROOT / args.manifest, args.split)
    results = [evaluate(Path(w), rows) for w in args.weights]
    for res in results:
        il, gl = res["image_level"], res["group_level"]
        print(f"\n== {res['weights']}  ({args.split} split)")
        print(f"image-level: acc {il['accuracy']}  macro-F1 {il['macro_f1']}  n={il['n']}")
        print(f"group-level: acc {gl['accuracy']}  macro-F1 {gl['macro_f1']}  n={gl['n']} source photos")
        for c, m in il["per_class"].items():
            print(f"  {c:24s} P {m['precision']:.3f}  R {m['recall']:.3f}  F1 {m['f1']:.3f}  n={m['support']}")
        print("  confusion (rows=true, cols=pred, order=" + ", ".join(CLASSES) + "):")
        for row in il["confusion_matrix"]:
            print("   ", row)
        if res["unseen_subset_image_level"]:
            u, ug = res["unseen_subset_image_level"], res["unseen_subset_group_level"]
            print(f"unseen-by-original-train subset: image acc {u['accuracy']} (n={u['n']}), "
                  f"group acc {ug['accuracy']} (n={ug['n']})")
    out = ROOT / args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"split": args.split, "results": results}, indent=2))
    print(f"\nwritten: {out}")


if __name__ == "__main__":
    main()
