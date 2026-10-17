"""Bir .glb dosyasındaki animasyonları listeler ve önemli kemiklerin konumlarını ölçer.

Kullanım:
  blender --background --factory-startup --python tools/check_animations.py -- <dosya.glb>
"""
import sys

import bpy

path = sys.argv[sys.argv.index("--") + 1]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=path)

arm = next(o for o in bpy.data.objects if o.type == "ARMATURE")
print("OBJECTS", [o.name for o in bpy.data.objects])
arm.animation_data_create()
for track in list(arm.animation_data.nla_tracks):
    arm.animation_data.nla_tracks.remove(track)


def fmt(v):
    return "(" + ", ".join(f"{c:.2f}" for c in v) + ")"


for action in bpy.data.actions:
    arm.animation_data.action = action
    if hasattr(arm.animation_data, "action_suitable_slots") and arm.animation_data.action_suitable_slots:
        arm.animation_data.action_slot = arm.animation_data.action_suitable_slots[0]
    start, end = (int(f) for f in action.frame_range)
    print(f"ACTION {action.name} frames={start}-{end}")
    for frame in sorted({start, (start + end) // 2, end}):
        bpy.context.scene.frame_set(frame)
        pb = arm.pose.bones
        print(f"  f{frame:>3} hips={fmt(pb['hips'].head)} head={fmt(pb['head'].head)}"
              f" hand.l={fmt(pb['hand.l'].head)} hand.r={fmt(pb['hand.r'].head)}"
              f" foot.l={fmt(pb['foot.l'].head)}")
