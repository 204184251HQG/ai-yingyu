"""列出词库里所有"封闭类"（介/代/连/冠/助/情态/感叹/数）单词与释义，作为 OVERRIDE 编写依据。"""
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FILES = [
    ROOT / "data/wordbank/primary.json.bak",
    ROOT / "data/wordbank/middle.json.bak",
    ROOT / "data/wordbank/high.json.bak",
]

CLOSED = {"prep", "pron", "conj", "art", "aux", "modal", "int", "num"}

bag = defaultdict(dict)
for f in FILES:
    for w in json.loads(f.read_text(encoding="utf-8")):
        if w.get("pos") in CLOSED:
            bag[w["pos"]][w["word"].lower()] = w.get("meaning", "")

for pos, dct in sorted(bag.items()):
    print(f"\n== {pos}（{len(dct)} 个）==")
    items = sorted(dct.items())
    for word, meaning in items:
        print(f'  "{word}": "{meaning}",')
