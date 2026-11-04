import unreal, re

def L(m):
    unreal.log_warning("[MI] " + str(m))

ROOT = r"E:/steam/steamapps/common/PBZ/workbuddy"
TGA = ROOT + "/ueproj/assets/tga"
TEXDIR = "/Game/Mods/PBZWardrobe/Textures"
MIDIR = "/Game/Mods/PBZWardrobe/MaterialInstances"
MESH = "/Game/Mods/PBZWardrobe/Meshes/SK_GoldenTigerBody"
HEAD = "/Game/Mods/PBZWardrobe/Meshes/SK_GoldenTigerHead"
MASTER = "/AkashaEffects/MaterialLibrary/Template/Character/MAI_Equipment_Mask"

FLAT = {
    "T_BY_FlatNormal": TGA + "/T_BY_FlatNormal.tga",
    "T_BY_ORM": TGA + "/T_BY_ORM.tga",
    "T_BY_white": TGA + "/T_BY_white.tga",
    "T_BY_insoles": TGA + "/T_BY_insoles.tga",
    "T_BY_soles": TGA + "/T_BY_soles.tga",
    "T_BY_metal": TGA + "/T_BY_metal.tga",
    "T_BY_black": TGA + "/T_BY_black.tga",
    "T_BY_darkbrown": TGA + "/T_BY_darkbrown.tga",
    "T_BY_teeth": TGA + "/T_BY_teeth.tga",
    "T_BY_tongue": TGA + "/T_BY_tongue.tga",
    "T_BY_ornament": TGA + "/T_BY_ornament.tga",
}

tasks = []
for name, src in FLAT.items():
    if unreal.EditorAssetLibrary.does_asset_exist(TEXDIR + "/" + name):
        continue
    t = unreal.AssetImportTask()
    t.filename = src
    t.destination_path = TEXDIR
    t.destination_name = name
    t.automated = True
    t.save = True
    t.replace_existing = True
    t.factory = unreal.TextureFactory()
    tasks.append(t)
if tasks:
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks(tasks)
L("flat textures imported %d" % len(tasks))

BODY = {
    # 键 = 材质槽名前缀，值 = (Albedo, Normal, Mix)
    # 全部按明末原版材质的真实分配来（wcdump MAT 读出来的 Albedo / Normal tex / Reflection）：
    #   M_HWC_Qunzi    -> BWC_QZ_D / BWC_QZ_N / BWC_QZ_R
    #   M_HWC_XiongGu  -> BWC_XG_D / BWC_XG_N / BWC_XG_R
    #   M_HWC_YaoDai01 -> BWC_YD_D / BWC_YD_N / BWC_YD_R
    #   M_HWC_LianPI01 -> BWC_LP_D / BWC_LP_N / BWC_LPJS_R   ← 注意用的是 LPJS_R
    #   M_HWC_shoubi   -> BWC_SB_D / BWC_SB_N / BWC_SB_R
    #   M_HWC_TouGu    -> BWC_TG_D / BWC_TG_N / BWC_TG_R
    "M_HWC_Qunzi":    ("T_BWC_QZ_D", "T_BWC_QZ_N", "T_BWC_QZ_R"),
    "M_HWC_XiongGu":  ("T_BWC_XG_D", "T_BWC_XG_N", "T_BWC_XG_R"),
    "M_HWC_YaoDai01": ("T_BWC_YD_D", "T_BWC_YD_N", "T_BWC_YD_R"),
    "M_HWC_LianPI01": ("T_BWC_LP_D", "T_BWC_LP_N", "T_BWC_LPJS_R"),
    "M_HWC_shoubi":   ("T_BWC_SB_D", "T_BWC_SB_N", "T_BWC_SB_R"),
    "M_HWC_TouGu":    ("T_BWC_TG_D", "T_BWC_TG_N", "T_BWC_TG_R"),
    # 皮肤 / 鞋子 / 外套：原版皮肤另有专用贴图，这里沿用已导出的肤色与通用图
    "MI_Head":        ("T_Skin_Head_D", "T_BY_FlatNormal", "T_BY_ORM"),
    "MI_Body":        ("T_Skin_Body_D", "T_BY_FlatNormal", "T_BY_ORM"),
    "white":          ("T_BY_white", "T_BY_FlatNormal", "T_BY_ORM"),
    "ih_insoles":     ("T_BY_insoles", "T_BY_FlatNormal", "T_BY_ORM"),
    "ih_soles":       ("T_BY_soles", "T_BY_FlatNormal", "T_BY_ORM"),
    "ih_metal":       ("T_BY_metal", "T_BY_FlatNormal", "T_BY_ORM"),
    "M_WCNJ_Jacket":  ("T_NVJ_COAT_D", "T_BY_FlatNormal", "T_BY_ORM"),
}

HEADM = {
    "MI_BlackBraid":         ("T_BY_black", "T_BY_FlatNormal", "T_BY_ORM"),
    "MI_FOX_BraidOrnament":  ("T_BY_ornament", "T_BY_FlatNormal", "T_BY_ORM"),
    "MI_Wuchang_Eyelash":    ("T_HeadLash", "T_BY_FlatNormal", "T_BY_ORM"),
    "MI_Wuchang_Brows":      ("T_HeadBrow", "T_BY_FlatNormal", "T_BY_ORM"),
    "MI_Wuchang_Eye":        ("T_HeadEye", "T_BY_FlatNormal", "T_BY_ORM"),
    "MI_Wuchang_Head":       ("T_HeadSkin", "T_BY_FlatNormal", "T_BY_ORM"),
    "MI_teeth":              ("T_BY_teeth", "T_BY_FlatNormal", "T_BY_ORM"),
    "MI_tongue":             ("T_BY_tongue", "T_BY_FlatNormal", "T_BY_ORM"),
    "MI_Wuchang_Tear":       ("T_BY_white", "T_BY_FlatNormal", "T_BY_ORM"),
}

# 需要额外的两张头部贴图（T_HeadBrow / T_HeadLash 已在 head_mats.py 里导入过）

master = unreal.load_asset(MASTER)
if master is None:
    L("!! master missing " + MASTER)
flatn = unreal.EditorAssetLibrary.load_asset(TEXDIR + "/T_BY_FlatNormal")
orm = unreal.EditorAssetLibrary.load_asset(TEXDIR + "/T_BY_ORM")

tools = unreal.AssetToolsHelpers.get_asset_tools()
mel = unreal.MaterialEditingLibrary
made = {}


def make_mi(key, texname, nrmname="T_BY_FlatNormal", mixname="T_BY_ORM", skin=False):
    name = "MI_BY_" + re.sub(r"[^A-Za-z0-9_]", "_", key)
    path = MIDIR + "/" + name
    if path in made:
        return made[path]
    if unreal.EditorAssetLibrary.does_asset_exist(path):
        unreal.EditorAssetLibrary.delete_asset(path)
    mi = tools.create_asset(name, MIDIR, unreal.MaterialInstanceConstant,
                            unreal.MaterialInstanceConstantFactoryNew())
    mi.set_editor_property("parent", master)
    tex = unreal.EditorAssetLibrary.load_asset(TEXDIR + "/" + texname)
    if tex is None:
        L("!! tex missing " + texname)
    else:
        mel.set_material_instance_texture_parameter_value(mi, "Albedo", tex)
    nrm = unreal.EditorAssetLibrary.load_asset(TEXDIR + "/" + nrmname)
    if nrm is None:
        L("!! normal missing " + nrmname); nrm = flatn
    if nrm is not None:
        mel.set_material_instance_texture_parameter_value(mi, "Normal", nrm)
    mixtex = unreal.EditorAssetLibrary.load_asset(TEXDIR + "/" + mixname)
    if mixtex is None:
        L("!! mix missing " + mixname); mixtex = orm
    if mixtex is not None:
        mel.set_material_instance_texture_parameter_value(mi, "Mix", mixtex)
    # 参数值照抄作者新包 PBZ_WanRuoYouLong_3800 的 MI_YL_Shangsheng（同一套明末衣服、游戏里跑得起来）
    # 关键：三个通道向量**必须显式给**，否则用母材质默认值 —— 默认与我们的贴图打包方式不一致时，
    # Metallic 会读到 AO 通道（=1）→ 全身金属反光/暗处发灰。这就是之前"灰"和"铬"的真正来源。
    # 我们把 T_BY_ORM 重新打包成 MRA：R=Metallic(0) G=Roughness(179) B=AO(255)。
    scal = {"ReplaceAlpha": 0.0,
            "Normal Strength": 0.0 if skin else 1.0,
            "AO Min": 1.0 if skin else 0.0,
            "AO Exponent": 1.0,
            "Roughness Min": 0.5 if skin else 0.0,
            "Roughness Max": 0.5 if skin else 1.0,
            "Roughness Exponent": 1.0,
            "Metallic Min": 0.0,
            "Metallic Max": 0.0 if skin else 1.0,
            "Specular": 0.35 if skin else 0.5,
            "Mask Sharpness": 0.0,
            "Mask Bias": 0.0,
            "Mask Final Multiply": 1.0,
            "Tile": 1.0,
            "Tile_U": 1.0,
            "Tile_V": 1.0,
            "Tile ApplyObjectScale": 0.0,
            "Use UV2 (For Scene Materials)": 0.0,
            "OpacityThreshold": 0.3333}
    for k, v in scal.items():
        mel.set_material_instance_scalar_parameter_value(mi, k, v)
    mel.set_material_instance_vector_parameter_value(mi, "AO Channel", unreal.LinearColor(0.0, 0.0, 1.0, 1.0))
    mel.set_material_instance_vector_parameter_value(mi, "Roughness Channel", unreal.LinearColor(0.0, 1.0, 0.0, 1.0))
    mel.set_material_instance_vector_parameter_value(mi, "Metallic Channel", unreal.LinearColor(1.0, 0.0, 0.0, 1.0))
    mel.set_material_instance_vector_parameter_value(mi, "Albedo Controls", unreal.LinearColor(1.0, 1.0, 1.0, 1.0))
    mel.set_material_instance_vector_parameter_value(mi, "Albedo Overlay", unreal.LinearColor(0.5, 0.5, 0.5, 1.0))
    unreal.EditorAssetLibrary.save_asset(path)
    made[path] = mi
    return mi


def apply(meshpath, table):
    m = unreal.EditorAssetLibrary.load_asset(meshpath)
    if m is None:
        L("!! mesh missing " + meshpath)
        return
    cur = m.get_editor_property("materials")
    out = []
    for i, sm in enumerate(cur):
        slot_name = str(sm.get_editor_property("material_slot_name") or "")
        base = re.sub(r"_\d{3}$", "", slot_name.split(".")[0])
        entry = table.get(base)
        if entry is None:
            # 前缀匹配「最长优先」：MI_Wuchang_Eye 是 MI_Wuchang_Eyelash 的前缀，短名会抢先命中
            for k in sorted(table.keys(), key=len, reverse=True):
                if slot_name.startswith(k):
                    entry = table[k]
                    base = k
                    break
        if entry is None:
            L("  slot %d '%s' -> no rule, use white" % (i, slot_name))
            entry = ("T_BY_white", "T_BY_FlatNormal", "T_BY_ORM")
            base = "fallback"
        tex, nrmn, mixn = entry
        mi = make_mi(base + ("_%d" % i if base in ("MI_Body", "MI_ZhiJia_base") else ""),
                      tex, nrmn, mixn,
                      skin=tex.startswith("T_Skin") or tex in ("T_HeadSkin", "T_HeadEye", "T_HeadLash"))
        nm = unreal.SkeletalMaterial()
        nm.set_editor_property("material_slot_name", slot_name if slot_name else ("slot%d" % i))
        nm.set_editor_property("material_interface", mi)
        out.append(nm)
        L("  slot %2d %-22s -> %s (%s / %s / %s)" % (i, slot_name, mi.get_name(), tex, nrmn, mixn))
    m.set_editor_property("materials", out)
    unreal.EditorAssetLibrary.save_asset(meshpath)
    L("applied %d slots to %s" % (len(out), meshpath.split("/")[-1]))


apply(MESH, BODY)
apply(HEAD, HEADM)
L("DONE")
