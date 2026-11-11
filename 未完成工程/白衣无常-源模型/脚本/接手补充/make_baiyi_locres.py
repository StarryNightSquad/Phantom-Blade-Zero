"""Generate a minimal UE5.7 Compact-format .locres for our own outfit name.

Why this exists
---------------
The outfit row's AppearanceName is a FlowLocText {Namespace, Key, ValueCache}.
The game resolves it at runtime via FTextLocalizationManager, NOT via the
ValueCache field. The author's working DT_CorsairAppearance template has
HistoryType=None / Value=null and relies on a .locres shipped in the pak.
Our v1-v4 rows wrote HistoryType=Base + CultureInvariantString, which the game
ignored -> the wardrobe showed an empty name.

Format evidence (Epic UE 5.7 source, authoritative):
  Engine/Source/Runtime/Core/Private/Internationalization/TextLocalizationResource.cpp
    FGuid LocResMagic                      (16 bytes)
    uint8 VersionNumber                    (Compact = 1)
    int64 LocalizedStringArrayOffset
    uint32 NamespaceCount
      FTextKey Namespace  (SerializeAsString for Compact -> plain FString)
      uint32 KeyCount
        FTextKey Key      (plain FString)
        uint32 SourceStringHash   <- only used for conflict detection
        int32  LocalizedStringIndex
    @LocalizedStringArrayOffset: TArray<FString>  (uint32 count + FStrings)
  Engine/Source/Runtime/Core/Public/Internationalization/TextLocalizationResource.h
    HashString() == FCrc::StrCrc32  (SourceStringHash); lookup is by FTextId.
  => SourceStringHash does not affect lookups; 0 is safe.

The reference mod's AdditiveWardrobe_9950 pak ships exactly this kind of file
at Content/Localization/Game/Platforms/Windows/<culture>/Game.locres and it
works in-game, so we copy that verified path layout (Game target only; we do
not write into the author's PBZCollectionWardrobe plugin namespace).
"""
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "github_wip"
OUT = ROOT / "s5_locres_stage"
MAGIC = bytes.fromhex("0e147475674a03fc4a15909dc3377f1b")
VERSION_COMPACT = 1

# Keys must match build_baiyi_tables.py's NAME_KEY / DESC_KEY (+ _1 / _2).
ENTRIES = [
    ("Baiyi_Outfit_Name",   "白衣无常"),
    ("Baiyi_Outfit_Desc",   "白衣无常 · 独立外观槽位"),
    ("Baiyi_Outfit_Name_1", "白衣无常 · 身体"),
    ("Baiyi_Outfit_Desc_1", "白衣无常 · 身体部件"),
    ("Baiyi_Outfit_Name_2", "白衣无常 · 发型"),
    ("Baiyi_Outfit_Desc_2", "白衣无常 · 发型部件"),
]

CULTURES = ("en", "en-US", "zh", "zh-Hans", "zh-Hant")
REL = "ProjectPBZ/Content/Localization/Game/Platforms/Windows/{}/Game.locres"


def fstring(s: str) -> bytes:
    """UE FArchive << FString: positive len = ANSI incl NUL, negative = UTF-16."""
    if all(ord(c) < 128 for c in s):
        b = s.encode("ascii") + b"\x00"
        return struct.pack("<i", len(b)) + b
    b = s.encode("utf-16-le") + b"\x00\x00"
    return struct.pack("<i", -(len(s) + 1)) + b


def build() -> bytes:
    body = struct.pack("<I", 1)          # namespace count
    body += fstring("Default")           # namespace
    body += struct.pack("<I", len(ENTRIES))
    for i, (key, _value) in enumerate(ENTRIES):
        body += fstring(key)
        body += struct.pack("<I", 0)     # SourceStringHash (lookup-independent)
        body += struct.pack("<i", i)     # localized string index
    strings = struct.pack("<I", len(ENTRIES))
    strings += b"".join(fstring(v) for _k, v in ENTRIES)
    off = 16 + 1 + 8 + len(body)
    return MAGIC + bytes([VERSION_COMPACT]) + struct.pack("<q", off) + body + strings


def verify(blob: bytes):
    """Parse back with the namespace->key model and assert exact agreement."""
    assert blob[:16] == MAGIC and blob[16] == VERSION_COMPACT
    off = struct.unpack_from("<q", blob, 17)[0]
    p = 25
    nsc = struct.unpack_from("<I", blob, p)[0]; p += 4
    assert nsc == 1

    def fs(pos):
        n = struct.unpack_from("<i", blob, pos)[0]; pos += 4
        if n == 0:
            return "", pos
        if n < 0:
            ln = -n * 2
            return blob[pos:pos + ln].decode("utf-16-le").rstrip("\x00"), pos + ln
        return blob[pos:pos + n].decode("latin1").rstrip("\x00"), pos + n

    ns, p = fs(p)
    assert ns == "Default"
    kc = struct.unpack_from("<I", blob, p)[0]; p += 4
    keys = []
    for _ in range(kc):
        k, p = fs(p)
        _hash = struct.unpack_from("<I", blob, p)[0]; p += 4
        idx = struct.unpack_from("<i", blob, p)[0]; p += 4
        keys.append((k, idx))
    assert p == off, (p, off)
    sc = struct.unpack_from("<I", blob, off)[0]; sp = off + 4
    vals = []
    for _ in range(sc):
        v, sp = fs(sp)
        vals.append(v)
    assert sp == len(blob), (sp, len(blob))
    assert keys == [(k, i) for i, (k, _v) in enumerate(ENTRIES)]
    assert vals == [v for _k, v in ENTRIES]
    return off


def main():
    blob = build()
    off = verify(blob)
    OUT.mkdir(parents=True, exist_ok=True)
    for c in CULTURES:
        dst = OUT / REL.format(c)
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_bytes(blob)
        print("  %6d B  %s" % (len(blob), dst.relative_to(OUT).as_posix()))
    print("OK: %d cultures, %d entries, string-array offset %d" % (len(CULTURES), len(ENTRIES), off))


if __name__ == "__main__":
    main()
