"""Offline: is a generated plan identical to another, byte for byte? For the rule that Lvl_BackAlleys_Arena's plan must
come out identical after any generator change (the 2026-11-08 split into kit/, passes/ and levels/).

    python Tools/LevelGen/analysis/plan_identical.py <dir A> <dir B> [prefix]      prefix: plan3_ by default

Compares every <prefix>*.json in both folders. If any differ, lists the first pieces that changed, by label."""
import json
import os
import sys

a_dir, b_dir = sys.argv[1], sys.argv[2]
prefix = sys.argv[3] if len(sys.argv) > 3 else "plan3_"
names = sorted({f for d in (a_dir, b_dir) for f in os.listdir(d) if f.startswith(prefix) and f.endswith(".json")})
diff = []
for f in names:
    pa, pb = os.path.join(a_dir, f), os.path.join(b_dir, f)
    if not (os.path.exists(pa) and os.path.exists(pb)) or open(pa, "rb").read() != open(pb, "rb").read():
        diff.append(f)
print("%d files compared, %d differ" % (len(names), len(diff)))
if diff:
    def load(d):
        out = []
        for f in sorted(os.listdir(d)):
            if f.startswith(prefix) and f[len(prefix):-5].isdigit():
                out.append((int(f[len(prefix):-5]), json.load(open(os.path.join(d, f)))))
        return [p for _, c in sorted(out) for p in c]
    ia, ib = load(a_dir), load(b_dir)
    print("items: %d vs %d" % (len(ia), len(ib)))
    for k, (p, q) in enumerate(zip(ia, ib)):
        if p != q:
            print("first difference at item %d:\n  A %s\n  B %s" % (k, json.dumps(p)[:300], json.dumps(q)[:300]))
            break
    la, lb = {p["label"] for p in ia}, {p["label"] for p in ib}
    print("only in A:", sorted(la - lb)[:20], "\nonly in B:", sorted(lb - la)[:20])
    sys.exit(1)
