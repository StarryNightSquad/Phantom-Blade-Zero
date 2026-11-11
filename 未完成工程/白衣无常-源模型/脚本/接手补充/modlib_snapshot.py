# -*- coding: utf-8 -*-
"""Snapshot / diff a UEModManager mod library folder (pak/ucas/utoc triplets).

Usage:
  python modlib_snapshot.py snap <dir> <out.json>
  python modlib_snapshot.py diff <old.json> <new.json>

Designed for comparing two releases of the author's 23-outfit collection.
"""
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

EXTS = (".pak", ".ucas", ".utoc")


def snapshot(root):
    packages = defaultdict(dict)
    for p in Path(root).rglob("*"):
        if not p.is_file() or p.suffix.lower() not in EXTS:
            continue
        m = re.match(r"^(.*)_P\.(pak|ucas|utoc)$", p.name, re.I)
        if not m:
            continue
        packages[m.group(1)][m.group(2).lower()] = p.stat().st_size
    return {
        "root": str(root),
        "package_count": len(packages),
        "packages": {k: v for k, v in sorted(packages.items())},
    }


def diff(old, new):
    a, b = old["packages"], new["packages"]
    ka, kb = set(a), set(b)
    changed = []
    for k in sorted(ka & kb):
        ch = {
            ext: {"old": a[k].get(ext), "new": b[k].get(ext)}
            for ext in set(a[k]) | set(b[k])
            if a[k].get(ext) != b[k].get(ext)
        }
        if ch:
            changed.append({"package": k, "files": ch})
    return {
        "old_root": old.get("root"),
        "new_root": new.get("root"),
        "added": sorted(kb - ka),
        "removed": sorted(ka - kb),
        "changed": changed,
    }


def main():
    mode = sys.argv[1]
    if mode == "snap":
        s = snapshot(sys.argv[2])
        out = Path(sys.argv[3])
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(s, ensure_ascii=False, indent=2), encoding="utf-8")
        print("packages:", s["package_count"], "->", out)
    elif mode == "diff":
        old = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))
        new = json.loads(Path(sys.argv[3]).read_text(encoding="utf-8"))
        d = diff(old, new)
        print(json.dumps(d, ensure_ascii=False, indent=2))
        print(
            "SUMMARY added=%d removed=%d changed=%d"
            % (len(d["added"]), len(d["removed"]), len(d["changed"]))
        )
    else:
        raise SystemExit("mode must be snap or diff")


if __name__ == "__main__":
    main()
