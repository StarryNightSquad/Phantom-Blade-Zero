# -*- coding: utf-8 -*-
"""Inspect FBX files against the porting checklist in 技术说明.md / 修复方案.md.

Run with:
  blender.exe -b --factory-startup --python inspect_fbx.py -- <a.fbx> [b.fbx ...]

Writes <output_dir>/fbx_inspect.json and prints the same JSON to stdout.
"""
import json
import sys
from pathlib import Path

import bpy
from mathutils import Vector

try:
    bpy.ops.preferences.addon_enable(module="io_scene_fbx")
except Exception:
    pass

OUT = Path("E:/steam/steamapps/common/PBZ/workbuddy/github_wip")
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []


def clean():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def mesh_info(obj):
    me = obj.data
    maxinf = 0
    zero = 0
    sum_bad = 0
    for v in me.vertices:
        gs = [g for g in v.groups if g.weight > 1e-6]
        if not gs:
            zero += 1
        else:
            maxinf = max(maxinf, len(gs))
            s = sum(g.weight for g in gs)
            if abs(s - 1.0) > 0.02:
                sum_bad += 1
    corners = [obj.matrix_world @ Vector(c) for c in obj.bound_box]
    lo = [round(min(c[i] for c in corners), 3) for i in range(3)]
    hi = [round(max(c[i] for c in corners), 3) for i in range(3)]
    return {
        "name": obj.name,
        "vertices": len(me.vertices),
        "polygons": len(me.polygons),
        "materials": [m.name if m else None for m in me.materials],
        "vertex_groups": len(obj.vertex_groups),
        "max_influences": maxinf,
        "zero_weight_vertices": zero,
        "non_normalized_vertices": sum_bad,
        "bbox_min": lo,
        "bbox_max": hi,
        "modifiers": [(m.name, m.type, getattr(getattr(m, "object", None), "name", None)) for m in obj.modifiers],
    }


def inspect(path):
    clean()
    bpy.ops.import_scene.fbx(filepath=str(path), use_custom_normals=True, ignore_leaf_bones=False)
    arms = []
    for o in bpy.data.objects:
        if o.type == "ARMATURE":
            names = [b.name for b in o.data.bones]
            arms.append({
                "name": o.name,
                "bone_count": len(names),
                "first12": names[:12],
                "has_root_at_0": bool(names) and names[0] == "root",
                "pelvis_index": names.index("pelvis") if "pelvis" in names else -1,
                "ik_weapon_root_index": names.index("ik_weapon_root") if "ik_weapon_root" in names else -1,
            })
    meshes = [mesh_info(o) for o in bpy.data.objects if o.type == "MESH"]
    return {
        "file": path.name,
        "size_bytes": path.stat().st_size,
        "objects": [(o.name, o.type) for o in bpy.data.objects],
        "armatures": arms,
        "meshes": meshes,
    }


def main():
    reports = []
    for p in argv:
        path = Path(p)
        print("INSPECTING " + str(path), flush=True)
        try:
            reports.append(inspect(path))
        except Exception as exc:  # noqa: BLE001
            reports.append({"file": path.name, "error": repr(exc)})
    result = {"fbx": reports}
    (OUT / "fbx_inspect.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print("RESULT_JSON " + json.dumps(result, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
