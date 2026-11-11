"""P2.1 - rebuild the BASE-GAME appearance table from CUE4Parse's row dump.

Why this exists
---------------
`pbzprobe dt` (UE5.7 settings + PBZ AES key + PBZ usmap) can now read the
encrypted base-game DT_PBZAppearanceTable: 54 rows (12 outfits + their
Body/Hat/Hair/Neck/MeshBand/BrowLashCard sub-rows). Earlier attempts used
GAME_UE5_1 (the Wuchang preset) and failed with "Read size is bigger than
remaining archive length".

With the original rows we can:
  * keep every vanilla outfit in the wardrobe (no more "原版服装全没了"), and
  * replace exactly ONE existing outfit slot with our Baiyi meshes - the
    user's "borrow an existing slot" proposal. Its ItemId stays untouched,
    so unlock status is inherited and no runtime grant framework is needed.

The produced JSON is consumed by `mipatch fromjson`, then `retoc to-zen`.
NOT installed by this script.
"""
import copy
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "github_wip"
DUMP = ROOT / "s7_orig_table_dump.txt"
TEMPLATE = ROOT / "s1_slot_table.json"       # 3 rows x 35 fields (field skeleton)
OUT = ROOT / "p2_jsons"
OUT.mkdir(parents=True, exist_ok=True)

# The outfit slot we take over. Change this single name to target another one.
TARGET_OUTFIT = "Hun_OutFit_Climax"
OUR_BODY_MESH = "/Game/Mods/PBZBaiyi/Meshes/SK_BaiyiBody"
OUR_HEAD_MESH = "/Game/Mods/PBZBaiyi/Meshes/SK_BaiyiHead"
OUR_ICON = "/Game/PBZContent/UI/UINew/items/T_Icon_Appearance_ChuanCheng"
OUR_NAME_KEY = "Baiyi_Outfit_Name"
OUR_DESC_KEY = "Baiyi_Outfit_Desc"

SOFT = {"AppearanceTexture", "HighPrecisionTexture", "BodyMeshAsset",
        "ClothMeshAsset", "HatAsset", "HeadAsset", "GroomPhysicsAsset",
        "NeckAsset", "MeshBandAsset", "BrowLashCardAsset"}
STR = {"OutfitBodyItem", "OutfitHatItem", "OutfitBeardItem",
       "OutfitHairStyleItem", "OutfitSequenceHairStyleItem",
       "OutfitNeckItem", "OutfitMeshBandItem", "OutfitBrowLashCardItem",
       "ItemId"}
BOOL = {"bHatUseSkinComponent", "bDefaultHatHidden", "bObtainableInGame"}
ARRAYS = {"BodyClothDataArray", "GroomDataArray", "HeadClothDataArray",
          "HeadClothDataArrayHatHidden", "UsedInSequences"}
TEXT = {"AppearanceName", "AppearanceDesc", "UnlockConditionDesc",
        "LockedTipText"}
TAGS = {"PBZItemTypeTag", "AddTagWhenHas", "AddTagWhenUse"}


def soft(path: str):
    """'/Pkg/Path/Asset.Asset' -> UAssetAPI FSoftObjectPath JSON value."""
    if not path or path in ("None", "?"):
        pkg, asset = "None", "None"
    elif "." in path.rsplit("/", 1)[-1]:
        pkg, asset = path.rsplit(".", 1)
    else:
        pkg, asset = path, path.rsplit("/", 1)[-1]
    return {"$type": "UAssetAPI.PropertyTypes.Objects.FSoftObjectPath, UAssetAPI",
            "AssetPath": {
                "$type": "UAssetAPI.PropertyTypes.Objects.FTopLevelAssetPath, UAssetAPI",
                "PackageName": pkg, "AssetName": asset},
            "SubPathString": None}


def parse_dump(path: Path):
    # .NET Console writes Chinese FNames in GBK on this machine.
    text = path.read_bytes().decode("gbk", errors="replace")
    parts = re.split(r"^  ROW\[(\d+)\] key=(.+)$", text, flags=re.M)
    rows = []
    for i in range(1, len(parts), 3):
        rows.append((int(parts[i]), parts[i + 1].strip(), parts[i + 2]))
    return rows


def parse_row(block: str):
    """Return {field: scalar | {'n','k'} | [paths]} for one ROW block."""
    lines = block.splitlines()
    out, cur, top_indent = {}, None, 8
    for line in lines:
        s = line.strip()
        if not s or s.startswith("STRUCTTYPE="):
            continue
        ind = len(line) - len(line.lstrip())
        if ind == top_indent:
            cur = None
            if " = " in s:
                n, v = s.split(" = ", 1)
                out[n.strip()] = v.strip()
            elif s.endswith(" = "):
                out[s[:-3].strip()] = ""
            elif " [" in s and s.endswith("]"):
                n = s.rsplit(" [", 1)[0].strip()
                cur = n
                out[n] = [] if "UScriptArray" in s else {}
        elif cur is not None and ind > top_indent:
            if " = " in s:
                n, v = s.split(" = ", 1)
                n, v = n.strip(), v.strip()
                if isinstance(out[cur], list):
                    if v.startswith("/"):
                        out[cur].append(v)
                elif isinstance(out[cur], dict):
                    out[cur][n.lower()] = v
            elif s == "":
                pass
    return out


def fill(prop, f):
    """Fill one template PropertyData from a parsed field value."""
    name = prop["Name"]
    v = f.get(name, None)
    if name in SOFT:
        prop["Value"] = soft(v if isinstance(v, str) else "")
    elif name in STR:
        # These are NamePropertyData (FName), NOT FString. Writing JSON null
        # makes UAssetAPI emit FName index 0, which reads back as NameMap[0]
        # (a ChangHong hair path) and corrupts the row. Use the FName "None".
        prop["Value"] = "None" if (v is None or v in ("None", "")) else v
    elif name in BOOL:
        prop["Value"] = (v == "True")
    elif name == "AppearanceType":
        prop["Value"] = (v or "").split("::")[-1]
    elif name in TEXT:
        d = v if isinstance(v, dict) else {}
        for part in prop["Value"]:
            if part["Name"] == "Namespace":
                part["Value"] = d.get("namespace", "Default")
            elif part["Name"] == "Key":
                part["Value"] = d.get("key", "")
            elif part["Name"] == "ValueCache":
                part["HistoryType"] = "None"
                part["CultureInvariantString"] = None
                part["Value"] = None
    elif name in TAGS:
        for part in prop["Value"]:
            if part["Name"] == "TagName":
                part["Value"] = None   # template uses null + IsZero=true
    elif name in ARRAYS:
        # CONSERVATIVE first pass: leave every array empty.
        # The array elements are unversioned structs whose StructType CUE4Parse
        # could not resolve (STRUCTTYPE=?). Guessing a StructType risks shifting
        # the whole row's property indices and breaking the ENTIRE table.
        # Phase 1 verifies "54 rows load + target slot replaced"; phase 2 adds
        # cloth/groom arrays once their exact schema is confirmed.
        prop["Value"] = []
    return prop


def main():
    rows = parse_dump(DUMP)
    tmpl = json.loads(TEMPLATE.read_text(encoding="utf-8-sig"))
    field_skeleton = tmpl["Exports"][0]["Table"]["Data"][0]["Value"]

    table = json.loads(json.dumps(tmpl))          # deep copy
    exp = table["Exports"][0]
    exp["ObjectName"] = "DT_PBZAppearanceTable"
    table["Info"] = "Rebuilt base-game appearance table: 54 vanilla rows, one slot replaced"
    new_rows = []
    parsed = {}
    for n, key, block in rows:
        f = parse_row(block)
        parsed[key] = f
        val = copy.deepcopy(field_skeleton)
        for prop in val:
            fill(prop, f)
        new_rows.append({"Name": key, "StructType": "PBZAppearanceStruct",
                         "$type": tmpl["Exports"][0]["Table"]["Data"][0]["$type"],
                         **{k: v for k, v in tmpl["Exports"][0]["Table"]["Data"][0].items()
                            if k not in ("Name", "StructType", "$type", "Value")},
                         "Value": val})

    # ---- take over one existing outfit slot ---------------------------------
    # Its Outfit row keeps name/ItemId (unlock inherited). We repoint the
    # Body/Hair sub-rows it references and drop vanilla cloth/hair overlays.
    target = parsed[TARGET_OUTFIT]
    body_row = target.get("OutfitBodyItem", "")
    hair_row = target.get("OutfitHairStyleItem", "")

    def item_id(row):
        return next((x["Value"] for x in row["Value"] if x["Name"] == "ItemId"), None)

    changed = []
    for r in new_rows:
        p = {x["Name"]: x for x in r["Value"]}
        if r["Name"] == TARGET_OUTFIT:
            p["AppearanceTexture"]["Value"] = soft(OUR_ICON)
            p["HighPrecisionTexture"]["Value"] = soft(OUR_ICON)
            for part in p["AppearanceName"]["Value"]:
                if part["Name"] == "Key":
                    part["Value"] = OUR_NAME_KEY
            for part in p["AppearanceDesc"]["Value"]:
                if part["Name"] == "Key":
                    part["Value"] = OUR_DESC_KEY
            # Drop vanilla hat / neck / band / brow overlays for THIS slot only;
            # their rows are shared with other outfits, so we must not edit them.
            for fld in ("OutfitHatItem", "OutfitNeckItem", "OutfitMeshBandItem",
                        "OutfitBrowLashCardItem", "OutfitSequenceHairStyleItem"):
                p[fld]["Value"] = "None"   # FName, see fill() note
            changed.append(r["Name"])
        elif item_id(r) == body_row:
            p["BodyMeshAsset"]["Value"] = soft(OUR_BODY_MESH)
            p["BodyClothDataArray"]["Value"] = []
            changed.append(r["Name"] + " (ItemId=" + body_row + ")")
        elif item_id(r) == hair_row:
            p["HeadAsset"]["Value"] = soft(OUR_HEAD_MESH)
            p["HeadClothDataArray"]["Value"] = []
            changed.append(r["Name"] + " (ItemId=" + hair_row + ")")

    exp["Table"]["Data"] = new_rows
    # UAssetAPI serializes FNames through NameMap; make sure every new string exists.
    nm = table["NameMap"]
    def add(s):
        if s and s not in ("None", "?") and s not in nm:
            nm.append(s)
    add("DT_PBZAppearanceTable")
    for r in new_rows:
        add(r["Name"])
        for prop in r["Value"]:
            fname, v = prop["Name"], prop["Value"]
            if fname in SOFT and isinstance(v, dict) and "AssetPath" in v:
                add(v["AssetPath"]["PackageName"])
                add(v["AssetPath"]["AssetName"])
            elif isinstance(v, str):
                add(v)
            elif isinstance(v, list):
                if fname in ARRAYS:
                    for e in v:
                        for sp in e.get("Value", []):
                            ap = sp.get("Value", {}).get("AssetPath", {})
                            add(ap.get("PackageName"))
                            add(ap.get("AssetName"))
                else:  # FlowLocText / GameplayTag structs
                    for part in v:
                        if isinstance(part, dict):
                            add(part.get("Value"))
    dst = OUT / "DT_PBZAppearanceTable_Full.json"
    dst.write_text(json.dumps(table, ensure_ascii=False, indent=2), encoding="utf-8")

    report = {
        "source_dump": str(DUMP), "rows": len(new_rows),
        "target_outfit": TARGET_OUTFIT,
        "target_subrows": {"body": body_row, "hair": hair_row},
        "rows_changed": changed,
        "array_element_totals": {
            a: sum(len(x["Value"]) for r in new_rows for x in r["Value"]
                   if x["Name"] == a and isinstance(x["Value"], list))
            for a in sorted(ARRAYS)},
        "our_meshes": {"body": OUR_BODY_MESH, "head": OUR_HEAD_MESH},
        "output": str(dst), "name_map_entries": len(nm),
        "note": "Array element StructType='AppearanceClothData' is inferred from the PBZ usmap name table; verify via mipatch fromjson round-trip.",
    }
    (OUT / "build_full_table_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
