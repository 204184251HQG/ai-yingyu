"""按词性抽样查看 100 个例句，肉眼校验。"""
import json
import random
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FILES = [
    ROOT / "data/wordbank/primary.json",
    ROOT / "data/wordbank/middle.json",
    ROOT / "data/wordbank/high.json",
]

by_pos = defaultdict(list)
for f in FILES:
    for w in json.loads(f.read_text(encoding="utf-8")):
        by_pos[w.get("pos", "?")].append(w)

random.seed(42)
for pos, words in sorted(by_pos.items()):
    sample = random.sample(words, min(8, len(words)))
    print(f"\n== 词性 {pos!r}（{len(words)} 词）==")
    for w in sample:
        print(f"  [{w['word']:<14s}] {w.get('example','')}")
        print(f"  {'':<16s} {w.get('example_zh','')}")
