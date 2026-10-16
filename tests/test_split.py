"""The leak-free split must never put copies of one source photo in two splits."""
import csv
from collections import defaultdict
from pathlib import Path

MANIFEST = Path(__file__).resolve().parent.parent / "data_splits" / "source_split.csv"


def load():
    with open(MANIFEST, newline="") as fh:
        return list(csv.DictReader(fh))


def test_manifest_covers_whole_dataset():
    rows = load()
    assert len(rows) == 1268
    assert {r["new_split"] for r in rows} == {"train", "val", "test"}


def test_no_source_or_group_in_two_splits():
    rows = load()
    for key in ("source", "group"):
        splits = defaultdict(set)
        for r in rows:
            splits[r[key]].add(r["new_split"])
        leaked = {k: v for k, v in splits.items() if len(v) > 1}
        assert not leaked, f"{key}s in more than one split: {leaked}"


def test_every_class_in_every_split():
    rows = load()
    for split in ("train", "val", "test"):
        assert {r["label"] for r in rows if r["new_split"] == split} == {
            "alternaria_alternata", "cercospora_nicotianae", "healthy"}
