"""Generate two brand-new PBZ appearance tables from the field-layout templates.

Inputs (read-only templates, never shipped):
  github_wip/s1_slot_table.json       - DT_CorsairAppearance  (3 rows x 35 fields)
  github_wip/s1_aggregate_table.json - DT_PBZAppearanceTable (CompositeDataTable, ParentTables)

Outputs (JSON, then converted to .uasset/.uexp by `mipatch fromjson`):
  github_wip/s2_jsons/DT_BaiyiAppearance.json
  github_wip/s2_jsons/DT_PBZAppearanceTable.json

The templates are used ONLY to learn the game's field layout. The produced package
contains no asset from any other mod: new table name, new ItemIds, our own display
text, and mesh/icon references pointing at the *base game* assets.

Caveat (needs in-game verification): ParentTables hard references were degraded to
UnknownExport by the Zen->legacy conversion. Whether the game resolves them after
the to-zen round trip is unknown; the first playtest decides. If it fails, the
fallback is a JS runtime registration (PBZModLoader 2.1.0 is installed).
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "github_wip"
OUT = ROOT / "s2_jsons"
OUT.mkdir(parents=True, exist_ok=True)

TABLE = "DT_BaiyiAppearance"
PKG = "/Game/Mods/PBZOutfitSlots/DT_BaiyiAppearance"
OUTFIT = "Hun_OutFit_BaiyiWuchang"
BODY = "BaiyiAppearance_Body"
HEAD = "BaiyiAppearance_Head"
NAME_KEY = "Baiyi_Outfit_Name"
DESC_KEY = "Baiyi_Outfit_Desc"

BODY_MESH = "/HuaShira/Characters/Hero/Hero_Hun/SkinParts/Hun_Body_Simple"
HEAD_MESH = "/HuaShira/Characters/Hero/Hero_Hun/SkinParts/Hun_Head_New"
ICON = "/Game/PBZContent/UI/UINew/items/T_Icon_Appearance_ChuanCheng"
ICON_NAME = "T_Icon_Appearance_ChuanCheng"

# Exact string substitutions (FName / FString / FSoftObjectPath values).
RENAME = {
    "DT_CorsairAppearance": TABLE,
    "/Game/Mods/PBZOutfitSlots/DT_CorsairAppearance": PKG,
    "Hun_OutFit_CodexCorsair": OUTFIT,
    "CorsairAppearance_Body": BODY,
    "CorsairAppearance_Head": HEAD,
    "PBZCollection_Hun_OutFit_CodexCorsair_Name": NAME_KEY,
    "PBZCollection_Hun_OutFit_CodexCorsair_Desc": DESC_KEY,
    "/Game/Mods/PBZFourOutfits/Meshes/SK_CorsairBody": BODY_MESH,
    "SK_CorsairBody": "Hun_Body_Simple",
    "/Game/Mods/PBZFourOutfits/Meshes/SK_CorsairHead": HEAD_MESH,
    "SK_CorsairHead": "Hun_Head_New",
    "/Game/Mods/PBZFourOutfits/UI/T_Corsair_Icon": ICON,
    "T_Corsair_Icon": ICON_NAME,
}


def walk_replace(node):
    """Recursively replace exact string values anywhere in the JSON tree."""
    if isinstance(node, dict):
        return {k: walk_replace(v) for k, v in node.items()}
    if isinstance(node, list):
        return [walk_replace(v) for v in node]
    if isinstance(node, str):
        return RENAME.get(node, node)
    return node


def set_flow_text(row, field, key, text):
    """Fill a FlowLocText-like {Namespace, Key, ValueCache} struct."""
    prop = next((p for p in row["Value"] if p.get("Name") == field), None)
    if not prop:
        return
    for part in prop["Value"]:
        n = part.get("Name")
        if n == "Key":
            part["Value"] = key
            part["IsZero"] = False
        elif n == "ValueCache":
            # ValueCache is an FText (TextPropertyData), not a plain string.
            # HistoryType=Base uses CultureInvariantString as the literal text,
            # so the name shows up even without a .locres entry.
            part["HistoryType"] = "Base"
            part["CultureInvariantString"] = text
            part["IsZero"] = False
            part.pop("Value", None)


def set_soft_path(row, field, package, asset):
    prop = next((p for p in row["Value"] if p.get("Name") == field), None)
    if not prop:
        return
    ap = prop["Value"]["AssetPath"]
    ap["PackageName"] = package
    ap["AssetName"] = asset
    prop["Value"]["SubPathString"] = None


def set_scalar(row, field, value):
    prop = next((p for p in row["Value"] if p.get("Name") == field), None)
    if prop:
        prop["Value"] = value


# ---------------------------------------------------------------- slot table
slot = walk_replace(json.loads((ROOT / "s1_slot_table.json").read_text(encoding="utf-8-sig")))
slot["Info"] = "Generated for PBZ Baiyi Wuchang standalone outfit slot (UAssetAPI JSON)"
exp = slot["Exports"][0]
exp["ObjectName"] = TABLE
rows = exp["Table"]["Data"]
assert len(rows) == 3, "expected 3 rows"

names = [OUTFIT, BODY, HEAD]
for row, new_name in zip(rows, names):
    row["Name"] = new_name
    set_scalar(row, "ItemId", new_name)
    # MEASURED (playtest 08:49, v3): setting bObtainableInGame=False removes the
    # row from the wardrobe entirely. Keep the template's True value.
    set_scalar(row, "bObtainableInGame", True)

# v4 - "borrow an existing outfit slot" (user's proposal, 08:49).
# The game's own DT_PBZAppearanceTable contains these real row/ItemId names
# (read from the P0.8 base-game export): Hun_OutFit_Default, _Climax,
# _Climax_Hat, _FengXue, _GuYou, _JiGuanMoQu, _MoTian, _YaYu, _ZhuiMing.
# The 08:40 playtest showed the row is listed but "未解锁，无法装备"; UE4SS
# probing found DefaultOutfits / OwnedOutfits TSets on BP_AppearanceComp_C.
# INFERRED (not game-official): the unlock gate compares ItemId against those
# sets, so reusing a base-game ID that the player already owns passes the gate.
# Hun_OutFit_Default is chosen because a default outfit is necessarily owned.
# Row name stays ours so the wardrobe keeps a single, unambiguous entry.
BORROWED_ID = "Hun_OutFit_Default"
set_scalar(rows[0], "ItemId", BORROWED_ID)

# Outfit row: link to our body/head rows, custom display text.
set_scalar(rows[0], "OutfitBodyItem", BODY)
set_scalar(rows[0], "OutfitHairStyleItem", HEAD)
set_scalar(rows[0], "OutfitSequenceHairStyleItem", HEAD)
LABELS = (
    ("白衣无常", "白衣无常 · 独立外观测试槽位"),
    ("白衣无常 · 身体", "白衣无常 · 身体部件"),
    ("白衣无常 · 发型", "白衣无常 · 发型部件"),
)
for i, (name, desc) in enumerate(LABELS):
    set_flow_text(rows[i], "AppearanceName", NAME_KEY if i == 0 else NAME_KEY + "_" + str(i), name)
    set_flow_text(rows[i], "AppearanceDesc", DESC_KEY if i == 0 else DESC_KEY + "_" + str(i), desc)

# Base-game icon on every row, base-game meshes on the body/head rows.
for row in rows:
    set_soft_path(row, "AppearanceTexture", ICON, ICON_NAME)
    set_soft_path(row, "HighPrecisionTexture", ICON, ICON_NAME)
set_soft_path(rows[1], "BodyMeshAsset", BODY_MESH, "Hun_Body_Simple")
set_soft_path(rows[2], "HeadAsset", HEAD_MESH, "Hun_Head_New")

# Neutralise unused template name-map entries. Index positions are preserved
# (array length unchanged), so no FName index can shift. Only PKG stays.
def neutralise_unused_mods(doc, keep):
    n = 0
    for i, s in enumerate(doc["NameMap"]):
        if "/Game/Mods/" in s and s != keep:
            doc["NameMap"][i] = "Unused_%03d" % i
            n += 1
    return n


slot_cleaned = neutralise_unused_mods(slot, PKG)
(OUT / (TABLE + ".json")).write_text(
    json.dumps(slot, ensure_ascii=False, indent=2), encoding="utf-8")

# ----------------------------------------------------------- aggregate table
agg = json.loads((ROOT / "s1_aggregate_table.json").read_text(encoding="utf-8-sig"))
aexp = agg["Exports"][0]
parents = next(p for p in aexp["Data"] if p.get("Name") == "ParentTables")
before = len(parents["Value"])
parents["Value"] = [parents["Value"][0]]  # only our table
parents["Value"][0]["Name"] = "0"

# The Zen->legacy conversion degraded every parent-table hard reference to
# import "UnknownExport" with outer "/Engine/UnknownPackage", which the game
# cannot resolve. Repair the one remaining reference so it points at our real
# package/object; FPackageIndex -7 -> Imports[6], whose OuterIndex -6 -> Imports[5].
imps = agg["Imports"]
ref_idx = -parents["Value"][0]["Value"] - 1
outer_idx = -imps[ref_idx]["OuterIndex"] - 1
assert imps[ref_idx]["ObjectName"] == "UnknownExport", "unexpected import layout"
assert imps[outer_idx]["ObjectName"] == "/Engine/UnknownPackage", "unexpected package layout"
imps[outer_idx]["ObjectName"] = PKG
imps[ref_idx]["ObjectName"] = TABLE
imps[ref_idx]["ClassPackage"] = "/Script/Engine"
imps[ref_idx]["ClassName"] = "DataTable"

# NOTE: do NOT truncate the remaining unused import pairs. retoc's Zen
# conversion panics ("index out of bounds: the len is 0 but the index is 1")
# when the import table is shortened, even though no live reference targets
# those entries. They are inert metadata; leave them in place.
print("repaired ParentTables import[%d] -> %s / %s (unused imports kept)"
      % (ref_idx, PKG, TABLE))

# Point the first parent-table name entry at our own table. The other 28 entries
# stay as unused FName strings (no reference points at them any more).
nm = agg["NameMap"]
first = next(i for i, s in enumerate(nm) if "PBZOutfitSlots" in s)
nm[first] = PKG
# The short asset name next to it.
if first + 1 < len(nm) and nm[first + 1].startswith("DT_"):
    nm[first + 1] = TABLE

agg["Info"] = "Generated CompositeDataTable: parent = " + PKG
agg_cleaned = neutralise_unused_mods(agg, PKG)
(OUT / "DT_PBZAppearanceTable.json").write_text(
    json.dumps(agg, ensure_ascii=False, indent=2), encoding="utf-8")

print("slot table rows:", [r["Name"] for r in rows])
print("name-map entries neutralised: slot=%d aggregate=%d" % (slot_cleaned, agg_cleaned))
print("parent tables:", before, "->", len(parents["Value"]))
print("name map entry", first, "->", nm[first])
print("written:", OUT / (TABLE + ".json"), "|", OUT / "DT_PBZAppearanceTable.json")
