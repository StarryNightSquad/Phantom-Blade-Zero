import unreal, os, glob

def L(m):
    unreal.log_warning("[RT] " + str(m))

TGA = r"E:/steam/steamapps/common/PBZ/workbuddy/ueproj/assets/tga"
TEXDIR = "/Game/Mods/PBZWardrobe/Textures"

# 只重导 albedo 这一类（T_ 开头且不是 FlatNormal/ORM 这种辅助图也无所谓，统一重导即可）
files = sorted(glob.glob(TGA + "/*.tga"))
L("found %d tga" % len(files))

tasks = []
for f in files:
    name = os.path.splitext(os.path.basename(f))[0]
    t = unreal.AssetImportTask()
    t.filename = f.replace("\\", "/")
    t.destination_path = TEXDIR
    t.destination_name = name
    t.automated = True
    t.save = True
    t.replace_existing = True
    t.factory = unreal.TextureFactory()
    tasks.append(t)

unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks(tasks)
L("re-imported %d" % len(tasks))

# 检查 alpha 是否已是 255（用原始数据块判定不可靠，这里只打印尺寸/格式供核对）
for k in ("T_BWC_QZ_D", "T_Skin_Body_D", "T_HeadSkin"):
    p = TEXDIR + "/" + k
    t = unreal.EditorAssetLibrary.load_asset(p)
    if t:
        L("%s size=%sx%s fmt=%s srgb=%s" % (k, t.blueprint_get_size_x(), t.blueprint_get_size_y(),
                                            t.get_editor_property("compression_settings"),
                                            t.get_editor_property("srgb")))
L("DONE")
