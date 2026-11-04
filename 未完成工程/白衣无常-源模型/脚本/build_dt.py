"""用导出的 dt_rows.json 重建外观表（走 DataTable.fill_from_json_string），并追加我们的一行。

前提：C++ 模块 ProjectPBZ 已编译（提供 /Script/ProjectPBZ.PBZAppearanceStruct）。
用法：UnrealEditor-Cmd <uproject> -run=pythonscript -script=ueproj/build_dt.py -unattended
"""
import unreal, json

SRC = r"E:/steam/steamapps/common/PBZ/workbuddy/skel/dt_rows.json"
DT_PATH = "/Game/PBZContent/DataTable/UI/DT_PBZAppearanceTable"
DT_DIR = "/Game/PBZContent/DataTable/UI"
DT_NAME = "DT_PBZAppearanceTable"

OUR_ROW = "Hun_OutFit_CodexBaiyi"
OUR_NAME = "白衣无常"
OUR_DESC = "明末·白衣无常（移植）"
OUR_BODY = "/Game/Mods/PBZWardrobe/Meshes/SK_GoldenTigerBody.SK_GoldenTigerBody"
OUR_HEAD = "/Game/Mods/PBZWardrobe/Meshes/SK_GoldenTigerHead.SK_GoldenTigerHead"
OUR_ICON = "/Game/Mods/PBZWardrobe/Textures/T_UI_GoldenTiger.T_UI_GoldenTiger"
OUR_ITEM_BODY = "CodexBaiyi_Body"
OUR_ITEM_HEAD = "CodexBaiyi_Head"

BOOL_FIELDS = {"bHatUseSkinComponent", "bDefaultHatHidden", "bObtainableInGame",
               "bDisableSimulationWhenHatVisible", "bOverrideSettings"}


def L(m):
    unreal.log_warning("[DT] " + str(m))


import re
VEC_RE = re.compile(r"^\s*([XYZWRP])=(-?[\d.]+)\s+([XYZWRP])=(-?[\d.]+)\s+([XYZWRP])=(-?[\d.]+)\s*$")
VEC4_RE = re.compile(r"^\s*X=(-?[\d.]+)\s+Y=(-?[\d.]+)\s+Z=(-?[\d.]+)\s+W=(-?[\d.]+)\s*$")


def conv(k, v):
    if isinstance(v, dict):
        return {kk: conv(kk, vv) for kk, vv in v.items()}
    if isinstance(v, list):
        return [conv(k, x) for x in v]
    if isinstance(v, str):
        if k in BOOL_FIELDS:
            return v.lower() == "true"
        if v.startswith("EAppearanceType::"):
            return v.split("::")[-1]
        m = VEC4_RE.match(v)
        if m:
            return {"X": float(m.group(1)), "Y": float(m.group(2)), "Z": float(m.group(3)), "W": float(m.group(4))}
        m = VEC_RE.match(v)
        if m:
            return {m.group(1): float(m.group(2)), m.group(3): float(m.group(4)), m.group(5): float(m.group(6))}
        return v
    return v


def main():
    data = json.load(open(SRC, encoding="utf-8"))
    L("json rows = %d" % len(data))

    rows = []
    for name, row in data.items():
        r = {"Name": name}
        for k, v in row.items():
            r[k] = conv(k, v)
        rows.append(r)

    # 把 5 个官方 Codex 槽位全部指向我们的网格：
    # 已解锁的那几个会直接变成可穿的「白衣无常」，锁着的仍显示灰模。
    # 这样就能一眼看出哪几个槽位是已解锁的。
    CODEX = ["CodexFY", "CodexFoxRain", "CodexSilkCorsair",
             "CodexGoldenTiger", "CodexMuXiaoKui"]
    body_rows = {c + "_Body" for c in CODEX}
    head_rows = {c + "_Head" for c in CODEX}
    touched = 0
    for r in rows:
        n = r.get("Name")
        if n in body_rows:
            r["BodyMeshAsset"] = OUR_BODY
            r["AppearanceTexture"] = OUR_ICON
            r["HighPrecisionTexture"] = OUR_ICON
            touched += 1
        elif n in head_rows:
            r["HeadAsset"] = OUR_HEAD
            r["AppearanceTexture"] = OUR_ICON
            r["HighPrecisionTexture"] = OUR_ICON
            touched += 1
    L("codex slots redirected: %d rows" % touched)

    payload = json.dumps(rows, ensure_ascii=False)
    L("payload %d bytes, rows=%d" % (len(payload), len(rows)))

    if unreal.EditorAssetLibrary.does_asset_exist(DT_PATH):
        unreal.EditorAssetLibrary.delete_asset(DT_PATH)
        L("deleted old table")

    factory = unreal.DataTableFactory()
    factory.set_editor_property("struct", unreal.PBZAppearanceStruct.static_struct())
    tools = unreal.AssetToolsHelpers.get_asset_tools()
    dt = tools.create_asset(DT_NAME, DT_DIR, unreal.DataTable, factory)
    if dt is None:
        L("!! create failed")
        return
    L("created %s" % dt.get_path_name())

    try:
        dt.fill_from_json_string(payload)
    except Exception as e:
        L("!! fill raised " + str(e))
        return

    names = dt.get_row_names()
    L("rows now = %d" % len(names))
    for probe in ("Hun_OutFit_Default", OUR_ROW):
        L("  has %-28s %s" % (probe, probe in [str(n) for n in names]))

    unreal.EditorAssetLibrary.save_loaded_asset(dt, only_if_is_dirty=False)
    L("saved")

    L("DONE")


main()
