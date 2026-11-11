# -*- coding: utf-8 -*-
"""Look up a localized string in a UE .locres (version >= 2, optimized layout).

Usage:
  python locres_lookup.py <file.locres> <keyword> [--max N]

Prints (namespace, key, hash, string-index, value) for every matching entry.
"""
import struct
import sys
from pathlib import Path


def read_fstring(d, pos):
    n = struct.unpack_from("<i", d, pos)[0]
    pos += 4
    if n == 0:
        return "", pos
    if n < 0:
        ln = -n * 2
        s = d[pos : pos + ln].decode("utf-16-le", errors="replace").rstrip("\x00")
    else:
        ln = n
        s = d[pos : pos + ln].decode("latin1", errors="replace").rstrip("\x00")
    return s, pos + ln


def parse(path):
    d = Path(path).read_bytes()
    if struct.unpack_from("<I", d, 0)[0] != 0x7574140E:
        raise ValueError("not a locres file")
    version = d[16]
    pos = 17
    strarr_off = struct.unpack_from("<q", d, pos)[0]
    pos += 8
    count = struct.unpack_from("<I", d, pos)[0]
    pos += 4
    entries = []
    for _ in range(count):
        ns, pos = read_fstring(d, pos)
        key, pos = read_fstring(d, pos)
        h = struct.unpack_from("<I", d, pos)[0]
        pos += 4
        idx = struct.unpack_from("<I", d, pos)[0]
        pos += 4
        entries.append((ns, key, h, idx))
    sp = strarr_off
    scount = struct.unpack_from("<I", d, sp)[0]
    sp += 4
    strings = []
    for _ in range(scount):
        s, sp = read_fstring(d, sp)
        strings.append(s)
    return {"version": version, "entries": entries, "strings": strings}


def main():
    path, kw = sys.argv[1], sys.argv[2]
    maxn = int(sys.argv[sys.argv.index("--max") + 1]) if "--max" in sys.argv else 20
    r = parse(path)
    print(
        "locres version=%d entries=%d strings=%d"
        % (r["version"], len(r["entries"]), len(r["strings"]))
    )
    hits = [i for i, s in enumerate(r["strings"]) if kw in s]
    print("string matches:", len(hits))
    for i in hits[:maxn]:
        val = r["strings"][i]
        owners = [e for e in r["entries"] if e[3] == i]
        for ns, key, h, _ in owners[:5]:
            print("  ns=%s key=%s hash=%08X idx=%d value=%s" % (ns, key, h, i, val))
        if not owners:
            print("  idx=%d value=%s (no owner entry)" % (i, val))
    if "--keys" in sys.argv:
        target = sys.argv[sys.argv.index("--keys") + 1]
        for ns, key, h, idx in r["entries"]:
            if target in key:
                val = r["strings"][idx] if idx < len(r["strings"]) else "?"
                print("  KEY ns=%s key=%s idx=%d value=%s" % (ns, key, idx, val))


if __name__ == "__main__":
    main()
