# -*- coding: utf-8 -*-
"""P2.2 - merge the Baiyi FBX into the 1 body + 1 head shape the game's
appearance table requires, while preserving all 28 material slots and the
1134-bone PBZ skeleton.

Why: DT_*Appearance rows only expose BodyMeshAsset + HeadAsset (P0.3). The
downloaded source is 4 separate meshes (Jacket / Hands / Pants / Head), same
layout as Wuchang's original. Epic's "Working with Modular Characters" says
Leader Pose needs exact skeletal subsets and runtime Merge destroys
MorphTargets, so we merge OFFLINE in Blender and keep every material slot.

Run:
  blender.exe -b --factory-startup --python merge_baiyi_fbx.py

Outputs:
  github_wip/p2_fbx/SK_BaiyiBody.fbx   (18 slots)
  github_wip/p2_fbx/SK_BaiyiHead.fbx   (10 slots)
  github_wip/p2_fbx/merge_report.json
"""
import json
import sys
from pathlib import Path

import bpy

ROOT = Path("E:/steam/steamapps/common/PBZ/workbuddy/github_wip")
SRC = ROOT / "baiyi"
OUT = ROOT / "p2_fbx"
OUT.mkdir(parents=True, exist_ok=True)

BODY_IN = SRC / "Baiyi_Body_ShortHair.fbx"
HEAD_IN = SRC / "HaiKou_ShortHair_Head.fbx"
BODY_OUT = OUT / "SK_BaiyiBody.fbx"
HEAD_OUT = OUT / "SK_BaiyiHead.fbx"

# Import MUST keep leaf bones: ignoring them drops 54 bones (1134 -> 1080).
IMPORT = dict(use_custom_normals=True, ignore_leaf_bones=False)

EXPORT = dict(
    use_selection=True,
    object_types={"ARMATURE", "MESH"},
    add_leaf_bones=False,
    bake_anim=False,
    global_scale=1.0,
    apply_unit_scale=False,      # do not introduce an extra x100
    apply_scale_options="FBX_SCALE_NONE",
    axis_forward="Y",
    axis_up="Z",
    use_mesh_modifiers=False,    # keep the Armature modifier / skin as-is
    mesh_smooth_type="FACE",
    use_custom_props=False,
    path_mode="AUTO",
)


def clean():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def load(path):
    clean()
    bpy.ops.import_scene.fbx(filepath=str(path), **IMPORT)
    meshes = sorted((o for o in bpy.data.objects if o.type == "MESH"),
                    key=lambda o: o.name)
    arms = [o for o in bpy.data.objects if o.type == "ARMATURE"]
    assert len(arms) == 1, "expected exactly one armature, got %d" % len(arms)
    return meshes, arms[0]


def snapshot(meshes, arm):
    bones = [b.name for b in arm.data.bones]
    info = {
        "armature_object": arm.name,
        "bone_count": len(bones),
        "first3": bones[:3],
        "ik_weapon_root_index": bones.index("ik_weapon_root")
        if "ik_weapon_root" in bones else -1,
        "meshes": [],
    }
    for o in meshes:
        me = o.data
        maxinf = zero = bad = 0
        for v in me.vertices:
            gs = [g for g in v.groups if g.weight > 1e-6]
            if not gs:
                zero += 1
            else:
                maxinf = max(maxinf, len(gs))
                if abs(sum(g.weight for g in gs) - 1.0) > 0.02:
                    bad += 1
        info["meshes"].append({
            "name": o.name,
            "vertices": len(me.vertices),
            "polygons": len(me.polygons),
            "materials": [m.name if m else None for m in me.materials],
            "vertex_groups": len(o.vertex_groups),
            "max_influences": maxinf,
            "zero_weight_vertices": zero,
            "non_normalized_vertices": bad,
            "bbox_min": [round(min((o.matrix_world @ __import__("mathutils").Vector(c))[i]
                                   for c in o.bound_box), 3) for i in range(3)],
            "bbox_max": [round(max((o.matrix_world @ __import__("mathutils").Vector(c))[i]
                                   for c in o.bound_box), 3) for i in range(3)],
        })
    return info


def write(path, meshes, arm):
    bpy.ops.object.select_all(action="DESELECT")
    for o in meshes + [arm]:
        o.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    bpy.ops.export_scene.fbx(filepath=str(path), **EXPORT)
    print("EXPORTED %s (%d B)" % (path.name, path.stat().st_size), flush=True)


def main():
    report = {}

    # ---- body: 3 meshes -> 1 -------------------------------------------------
    meshes, arm = load(BODY_IN)
    report["body_input"] = snapshot(meshes, arm)
    assert len(meshes) == 3, "expected 3 body meshes, got %d" % len(meshes)

    # Deterministic slot order: alphabetical mesh order, then each mesh's
    # original material order (all 18 names are unique, so join keeps all).
    bpy.ops.object.select_all(action="DESELECT")
    for o in meshes:
        o.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    bpy.ops.object.join()
    merged = next(o for o in bpy.data.objects if o.type == "MESH")
    merged.name = "SK_BaiyiBody"
    arm.name = "Armature"           # project rule: UE skips this container node
    arm.data.name = "Armature"
    report["body_merged"] = snapshot([merged], arm)
    assert len(merged.data.materials) == 18, \
        "material slots lost: %d" % len(merged.data.materials)
    assert report["body_merged"]["bone_count"] == 1134
    write(BODY_OUT, [merged], arm)

    # ---- head: single mesh, just rename --------------------------------------
    meshes, arm = load(HEAD_IN)
    report["head_input"] = snapshot(meshes, arm)
    assert len(meshes) == 1
    meshes[0].name = "SK_BaiyiHead"
    arm.name = "Armature"
    arm.data.name = "Armature"
    report["head_merged"] = snapshot(meshes, arm)
    assert len(meshes[0].data.materials) == 10
    assert report["head_merged"]["bone_count"] == 1134
    write(HEAD_OUT, meshes, arm)

    # ---- verify by re-importing the exported files --------------------------
    m2, a2 = load(BODY_OUT)
    report["body_export_verify"] = snapshot(m2, a2)
    m3, a3 = load(HEAD_OUT)
    report["head_export_verify"] = snapshot(m3, a3)

    ok = (
        report["body_export_verify"]["bone_count"] == 1134
        and report["head_export_verify"]["bone_count"] == 1134
        and len(report["body_export_verify"]["meshes"][0]["materials"]) == 18
        and len(report["head_export_verify"]["meshes"][0]["materials"]) == 10
        and report["body_export_verify"]["meshes"][0]["zero_weight_vertices"] == 0
        and report["head_export_verify"]["meshes"][0]["zero_weight_vertices"] == 0
    )
    report["VERIFIED"] = ok
    (OUT / "merge_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print("RESULT " + json.dumps({"VERIFIED": ok,
                                  "body_slots": len(report["body_export_verify"]["meshes"][0]["materials"]),
                                  "head_slots": len(report["head_export_verify"]["meshes"][0]["materials"]),
                                  "body_bones": report["body_export_verify"]["bone_count"],
                                  "head_bones": report["head_export_verify"]["bone_count"]}), flush=True)


if __name__ == "__main__":
    main()
