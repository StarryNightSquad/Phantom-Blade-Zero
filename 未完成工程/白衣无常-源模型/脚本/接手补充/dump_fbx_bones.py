# -*- coding: utf-8 -*-
"""Dump the ordered bone name list of an FBX for skeleton compatibility checks.

Run with:
  blender.exe -b --factory-startup --python dump_fbx_bones.py -- <a.fbx> <out.txt>

Blender's FBX importer must keep leaf bones (use 1134, not 1080).
"""
import sys
from pathlib import Path

import bpy

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
if len(argv) < 2:
    raise SystemExit("usage: dump_fbx_bones.py -- <file.fbx> <out.txt>")

fbx, out = argv[0], Path(argv[1])
bpy.ops.wm.read_factory_settings(use_empty=True)
try:
    bpy.ops.preferences.addon_enable(module="io_scene_fbx")
except Exception:
    pass
bpy.ops.import_scene.fbx(filepath=fbx, use_anim=False, ignore_leaf_bones=False)

armatures = [o for o in bpy.data.objects if o.type == "ARMATURE"]
if not armatures:
    raise SystemExit("NO_ARMATURE")
arm = armatures[0]
names = [b.name for b in arm.data.bones]
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text("\n".join(names), encoding="utf-8")
print("BONES %d ARM %s FIRST %s -> %s" % (len(names), arm.name, names[:3], out))
