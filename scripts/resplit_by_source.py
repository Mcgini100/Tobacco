"""
Leak-free re-split of the Roboflow "Tobacco leaf disease detection" dataset.

Why: the Roboflow export contains several copies of each source photo
(file names share the prefix before ".rf."). The original export placed
copies of the same photo in train, valid AND test, so the original test
accuracy measured memorisation, not generalisation.

What this script does:
1. Reads the three _classes.csv files and maps every image to
   (source photo, class).
2. Optionally merges different source names whose images are perceptual-hash
   near-duplicates into one group (so a re-uploaded photo cannot leak either).
3. Splits *groups* (not images) into train/val/test, stratified by class,
   so no source photo appears in more than one split.
4. Writes a manifest CSV (committed) and builds a YOLOv8-cls folder tree
   (not committed) with symlinks to the original images.

Usage:
    python scripts/resplit_by_source.py --out dataset_clean
"""
from __future__ import annotations

import argparse
import csv
import os
import random
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "Tobacco leaf disease detection.v1i.multiclass"
CLASS_MAP = {
    "alternaria alternata": "alternaria_alternata",
    "cercospora nicotianae": "cercospora_nicotianae",
    "no cercospora nicotianae or alternaria alternata present": "healthy",
}
SPLITS = ("train", "valid", "test")


def source_of(filename: str) -> str:
    """Roboflow names copies '<source>.rf.<hash>.jpg'; the source is the prefix."""
    return filename.split(".rf.")[0]


def load_records() -> list[dict]:
    records = []
    for split in SPLITS:
        with open(RAW / split / "_classes.csv", newline="") as fh:
            rows = list(csv.reader(fh))
        header = [h.strip() for h in rows[0]]
        for row in rows[1:]:
            fn = row[0].strip()
            onehot = [int(x) for x in row[1:]]
            if sum(onehot) != 1:
                raise ValueError(f"{fn}: expected exactly one label, got {onehot}")
            label = CLASS_MAP[header[1 + onehot.index(1)]]
            records.append(
                {
                    "path": str((RAW / split / fn).relative_to(ROOT)),
                    "filename": fn,
                    "original_split": split,
                    "source": source_of(fn),
                    "label": label,
                }
            )
    return records


def merge_near_duplicates(records: list[dict], max_distance: int) -> dict[str, str]:
    """Union-find over sources: two sources join if any of their images have
    perceptual-hash distance <= max_distance. Returns source -> group id."""
    import imagehash
    from PIL import Image

    parent: dict[str, str] = {}

    def find(x: str) -> str:
        parent.setdefault(x, x)
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a: str, b: str) -> None:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[max(ra, rb)] = min(ra, rb)

    hashes = []
    for r in records:
        find(r["source"])
        with Image.open(ROOT / r["path"]) as im:
            hashes.append((r["source"], imagehash.phash(im)))
    merged_pairs = set()
    for i in range(len(hashes)):
        si, hi = hashes[i]
        for j in range(i + 1, len(hashes)):
            sj, hj = hashes[j]
            if si != sj and (hi - hj) <= max_distance:
                union(si, sj)
                merged_pairs.add(tuple(sorted((si, sj))))
    for a, b in sorted(merged_pairs):
        print(f"  near-duplicate sources merged: {a}  <->  {b}")
    return {s: find(s) for s in parent}


def split_groups(group_label: dict[str, str], ratios=(0.6, 0.2, 0.2), seed=42) -> dict[str, str]:
    by_class: dict[str, list[str]] = defaultdict(list)
    for g, lab in sorted(group_label.items()):
        by_class[lab].append(g)
    rng = random.Random(seed)
    assignment = {}
    for lab, groups in sorted(by_class.items()):
        rng.shuffle(groups)
        n = len(groups)
        n_test = max(1, round(n * ratios[2]))
        n_val = max(1, round(n * ratios[1]))
        for k, g in enumerate(groups):
            assignment[g] = "test" if k < n_test else "val" if k < n_test + n_val else "train"
    return assignment


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="dataset_clean", help="YOLO folder tree to build (git-ignored)")
    ap.add_argument("--manifest", default="data_splits/source_split.csv")
    ap.add_argument("--phash-distance", type=int, default=6,
                    help="merge sources whose images are this close (0 disables merge)")
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    records = load_records()
    sources = sorted({r["source"] for r in records})
    print(f"{len(records)} images from {len(sources)} distinct source photos")

    if args.phash_distance > 0:
        group_of = merge_near_duplicates(records, args.phash_distance)
    else:
        group_of = {s: s for s in sources}

    group_label: dict[str, str] = {}
    for r in records:
        g = group_of[r["source"]]
        if group_label.setdefault(g, r["label"]) != r["label"]:
            raise ValueError(f"group {g} mixes labels {group_label[g]} and {r['label']}")

    assignment = split_groups(group_label, seed=args.seed)

    manifest = ROOT / args.manifest
    manifest.parent.mkdir(parents=True, exist_ok=True)
    with open(manifest, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["path", "source", "group", "label", "original_split", "new_split"])
        w.writeheader()
        for r in sorted(records, key=lambda r: r["path"]):
            g = group_of[r["source"]]
            w.writerow({"path": r["path"], "source": r["source"], "group": g, "label": r["label"],
                        "original_split": r["original_split"], "new_split": assignment[g]})
    print(f"manifest written: {manifest.relative_to(ROOT)}")

    out = ROOT / args.out
    if out.exists():
        for p in sorted(out.rglob("*"), reverse=True):
            p.unlink() if p.is_file() or p.is_symlink() else p.rmdir()
    for split in ("train", "val", "test"):
        for lab in CLASS_MAP.values():
            (out / split / lab).mkdir(parents=True, exist_ok=True)
    for r in records:
        split = assignment[group_of[r["source"]]]
        dst = out / split / r["label"] / r["filename"]
        os.symlink(ROOT / r["path"], dst)

    # Summary + leak check
    summary = defaultdict(lambda: defaultdict(lambda: [0, set()]))
    for r in records:
        split = assignment[group_of[r["source"]]]
        summary[split][r["label"]][0] += 1
        summary[split][r["label"]][1].add(group_of[r["source"]])
    print(f"\n{'split':6s} {'class':24s} {'images':>7s} {'groups':>7s}")
    for split in ("train", "val", "test"):
        for lab in CLASS_MAP.values():
            n, gs = summary[split][lab]
            print(f"{split:6s} {lab:24s} {n:7d} {len(gs):7d}")
    split_groups_sets = {s: set().union(*(v[1] for v in summary[s].values())) for s in summary}
    for a in ("train", "val", "test"):
        for b in ("train", "val", "test"):
            if a < b:
                assert not (split_groups_sets[a] & split_groups_sets[b]), f"leak between {a} and {b}"
    print("\nleak check passed: no source group appears in more than one split")


if __name__ == "__main__":
    main()
