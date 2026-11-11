# -*- coding: utf-8 -*-
"""List assets inside unencrypted IoStore .utoc containers via UnrealPak -List.

Usage:
  python utoc_index.py snap <utoc-or-dir> <out.json>
  python utoc_index.py diff <a.json> <b.json>

Works for the author's PBZ outfit mods (no AES key needed for the container TOC).
"""
import json
import re
import subprocess
import sys
from pathlib import Path

UNREALPAK = r"D:/Epic Games/UE_5.7/Engine/Binaries/Win64/UnrealPak.exe"
LINE = re.compile(r'LogIoStore: Display: "([^"]+)" offset:')


def list_utoc(path):
    proc = subprocess.run(
        [UNREALPAK, str(path), "-List"],
        capture_output=True,
        text=True,
        errors="ignore",
        timeout=120,
    )
    out = (proc.stdout or "") + (proc.stderr or "")
    return sorted(set(LINE.findall(out)))


def snap(target):
    t = Path(target)
    files = sorted(t.rglob("*.utoc")) if t.is_dir() else [t]
    data = {}
    for f in files:
        try:
            data[f.name] = list_utoc(f)
        except Exception as exc:  # noqa: BLE001
            data[f.name] = {"error": repr(exc)}
    return {"root": str(t), "containers": data}


def clean(path):
    """Strip mount prefix and project/Mods/<namespace> so names are comparable."""
    s = path.replace("../../../", "").replace("\\", "/")
    parts = s.split("/")
    # drop everything through Content/Mods/<Namespace>/
    try:
        i = parts.index("Mods")
        s = "/".join(parts[i + 2 :])
    except ValueError:
        pass
    return s


def diff(a, b):
    def names(d):
        return {clean(p) for pack in d["containers"].values() if isinstance(pack, list) for p in pack}

    na, nb = names(a), names(b)
    return {
        "a_only": sorted(na - nb),
        "b_only": sorted(nb - na),
        "common": len(na & nb),
        "a_total": len(na),
        "b_total": len(nb),
    }


def main():
    mode = sys.argv[1]
    if mode == "snap":
        s = snap(sys.argv[2])
        out = Path(sys.argv[3])
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(s, ensure_ascii=False, indent=2), encoding="utf-8")
        for k, v in s["containers"].items():
            print(k, len(v) if isinstance(v, list) else v)
        print("->", out)
    elif mode == "diff":
        a = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))
        b = json.loads(Path(sys.argv[3]).read_text(encoding="utf-8"))
        print(json.dumps(diff(a, b), ensure_ascii=False, indent=2))
    else:
        raise SystemExit("mode must be snap or diff")


if __name__ == "__main__":
    main()
