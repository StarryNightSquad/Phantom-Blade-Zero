import unreal

def L(m):
    unreal.log_warning("[AK2] " + str(m))

DIR = "/AkashaEffects/MaterialLibrary/Template/Character"
PATH = DIR + "/MAI_Equipment_Mask"

# 依据：作者新包 PBZ_WanRuoYouLong_3800 里 MI_YL_Shangsheng 的完整参数表（izprobe PARAM 读出）
#   Scalar(18): ReplaceAlpha, Normal Strength, AO Min, AO Exponent, Roughness Min/Max/Exponent,
#               Metallic Min/Max, Specular, Mask Sharpness, Mask Bias, Mask Final Multiply,
#               Tile, Tile_U, Tile_V, Tile ApplyObjectScale, Use UV2 (For Scene Materials)
#   Vector(5):  AO Channel=0000FF, Roughness Channel=00FF00, Metallic Channel=FF0000,
#               Albedo Controls=FFFFFF, Albedo Overlay=BCBCBC
#   Texture(3): Albedo / Normal / Mix
# 说明：官方 MI 的子集只反映「官方自己设了几个」，真正母材质里的参数远不止那些。
# 我们这个占位母材质只要把**全部参数名和类型**声明出来，MI 才能把值写进去。

SCALARS = [
    ("ReplaceAlpha", 0.0),
    ("Normal Strength", 1.0),
    ("AO Min", 0.0),
    ("AO Exponent", 1.0),
    ("Roughness Min", 0.0),
    ("Roughness Max", 1.0),
    ("Roughness Exponent", 1.0),
    ("Metallic Min", 0.0),
    ("Metallic Max", 1.0),
    ("Specular", 0.5),
    ("Mask Sharpness", 0.0),
    ("Mask Bias", 0.0),
    ("Mask Final Multiply", 1.0),
    ("Tile", 1.0),
    ("Tile_U", 1.0),
    ("Tile_V", 1.0),
    ("Tile ApplyObjectScale", 0.0),
    ("Use UV2 (For Scene Materials)", 0.0),
    ("OpacityThreshold", 0.3333),
]

VECTORS = [
    ("AO Channel", (0.0, 0.0, 1.0, 1.0)),
    ("Roughness Channel", (0.0, 1.0, 0.0, 1.0)),
    ("Metallic Channel", (1.0, 0.0, 0.0, 1.0)),
    ("Albedo Controls", (1.0, 1.0, 1.0, 1.0)),
    ("Albedo Overlay", (0.5, 0.5, 0.5, 1.0)),
]

if unreal.EditorAssetLibrary.does_asset_exist(PATH):
    unreal.EditorAssetLibrary.delete_asset(PATH)
    L("deleted old " + PATH)

tools = unreal.AssetToolsHelpers.get_asset_tools()
mat = tools.create_asset("MAI_Equipment_Mask", DIR, unreal.Material, unreal.MaterialFactoryNew())
mel = unreal.MaterialEditingLibrary

alb = mel.create_material_expression(mat, unreal.MaterialExpressionTextureSampleParameter2D, -700, -200)
alb.set_editor_property("parameter_name", "Albedo")
mel.connect_material_property(alb, "RGB", unreal.MaterialProperty.MP_BASE_COLOR)

nrm = mel.create_material_expression(mat, unreal.MaterialExpressionTextureSampleParameter2D, -700, 40)
nrm.set_editor_property("parameter_name", "Normal")
mel.connect_material_property(nrm, "RGB", unreal.MaterialProperty.MP_NORMAL)

mix = mel.create_material_expression(mat, unreal.MaterialExpressionTextureSampleParameter2D, -700, 260)
mix.set_editor_property("parameter_name", "Mix")

y = 480
for nm, dv in SCALARS:
    sp = mel.create_material_expression(mat, unreal.MaterialExpressionScalarParameter, -400, y)
    sp.set_editor_property("parameter_name", nm)
    sp.set_editor_property("default_value", dv)
    y += 80

y = 480
for nm, c in VECTORS:
    vp = mel.create_material_expression(mat, unreal.MaterialExpressionVectorParameter, -100, y)
    vp.set_editor_property("parameter_name", nm)
    vp.set_editor_property("default_value", unreal.LinearColor(c[0], c[1], c[2], c[3]))
    y += 80

# ---------------------------------------------------------------------------
# 【关键】使用标记（Material Usage）
#
# 之前这里从来没设过，于是占位母材质的 bUsedWithSkeletalMesh = False。
# cook 时这个标记会被烘进每个 MIC 的 FMaterialCachedExpressionData.RuntimeMaterialUsage，
# 运行时组件一检查「这个材质支持骨骼网格吗」→ 否 → 直接退回 DefaultMaterial。
# 表现就是：不报错、无紫红格子、就是一片均匀灰白，且参数怎么改都不生效。
# 官方母材质 MAI_Equipment_Mask 是给骨骼网格角色用的，这些标记必然是开的。
# ---------------------------------------------------------------------------
for _flag in ("used_with_skeletal_mesh",
              "used_with_static_mesh",
              "used_with_instanced_static_meshes",
              "used_with_particle_sprites",
              "used_with_morph_targets"):
    try:
        mat.set_editor_property(_flag, True)
        L("usage %s = True" % _flag)
    except Exception as _e:
        L("!! usage %s 设置失败: %s" % (_flag, _e))

mat.set_editor_property("blend_mode", unreal.BlendMode.BLEND_MASKED)
mat.set_editor_property("opacity_mask_clip_value", 0.3333)
mel.recompile_material(mat)
unreal.EditorAssetLibrary.save_asset(PATH)
L("rebuilt %s  scalars=%d vectors=%d" % (PATH, len(SCALARS), len(VECTORS)))
L("DONE")
