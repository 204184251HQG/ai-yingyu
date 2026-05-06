"""统计词库 example 字段的模板化分布。"""
import json
import re
import collections
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FILES = [
    ROOT / "data/wordbank/primary.json",
    ROOT / "data/wordbank/middle.json",
    ROOT / "data/wordbank/high.json",
]

total = 0
patterns = collections.Counter()
samples = collections.defaultdict(list)

for f in FILES:
    data = json.loads(f.read_text(encoding="utf-8"))
    print(f"== {f.name}: {len(data)} 词 ==")
    for w in data:
        ex = (w.get("example") or "").strip()
        total += 1
        if not ex:
            patterns["(empty)"] += 1
            continue
        m = re.match(r"^(\w+\s+\w+\s+\w+)", ex)
        prefix = m.group(1) if m else ex[:20]
        patterns[prefix] += 1
        if len(samples[prefix]) < 3:
            samples[prefix].append(f"{w['word']}: {ex}")

print(f"\n== TOTAL {total} 词 · 不同前 3 词模式 {len(patterns)} 种 ==\n")
for p, c in patterns.most_common(20):
    print(f"  {c:5d}  {p}")
    for s in samples[p][:2]:
        print(f"           {s}")
