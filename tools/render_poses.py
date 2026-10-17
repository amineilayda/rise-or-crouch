"""Bir .glb karakterin animasyonlarından önizleme resmi (poz tablosu) çıkarır.

Kullanım:
  blender --background --factory-startup --python tools/render_poses.py -- <dosya.glb> <çıktı.png>
"""
import os
import sys
import tempfile

import bpy
import numpy as np
from mathutils import Vector

path, out_png = sys.argv[sys.argv.index("--") + 1:][:2]

W, H = 360, 420
VIEWS = {
    # Önden 3/4 ve yandan (karakter -Y'ye bakıyor).
    "front": Vector((2.2, -3.4, 1.0)),
    "side": Vector((4, 0, 0.75)),
}
# (animasyon, kare); None = son kare
POSES = [
    ("Idle", 0), ("Crouch", None), ("L_Idle_Deve", None), ("L_Deve_Cuce", None),
    ("Fail", None), ("Walk", 0), ("Walk", 4), ("Walk", 8),
]


def render(action_name, frame, view, filepath):
    # Her resim için sahneyi baştan kur: aynı sahnede animasyon değiştirince
    # Blender bazen render'a eski pozu veriyor.
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=path)
    for obj in [o for o in bpy.data.objects if o.name.startswith("Icosphere")]:
        bpy.data.objects.remove(obj)

    arm = next(o for o in bpy.data.objects if o.type == "ARMATURE")
    arm.animation_data_create()
    for track in list(arm.animation_data.nla_tracks):
        arm.animation_data.nla_tracks.remove(track)
    action = bpy.data.actions[action_name]
    arm.animation_data.action = action
    slots = getattr(arm.animation_data, "action_suitable_slots", None)
    if slots:
        arm.animation_data.action_slot = slots[0]

    scene = bpy.context.scene
    scene.render.engine = "BLENDER_WORKBENCH"
    scene.display.shading.light = "STUDIO"
    scene.display.shading.color_type = "TEXTURE"
    scene.render.resolution_x = W
    scene.render.resolution_y = H
    scene.world = bpy.data.worlds.new("w")
    scene.world.color = (0.85, 0.88, 0.92)

    cam_data = bpy.data.cameras.new("cam")
    cam_data.type = "ORTHO"
    cam_data.ortho_scale = 3.0
    cam = bpy.data.objects.new("cam", cam_data)
    scene.collection.objects.link(cam)
    scene.camera = cam
    cam.location = VIEWS[view]
    cam.rotation_euler = (Vector((0, 0, 0.95)) - cam.location).to_track_quat("-Z", "Y").to_euler()

    scene.frame_set(int(action.frame_range[1]) if frame is None else frame)
    scene.render.filepath = filepath
    bpy.ops.render.render(write_still=True)


tmp = tempfile.mkdtemp()
rows = []
for view in VIEWS:
    tiles = []
    for action_name, frame in POSES:
        tile = os.path.join(tmp, f"{action_name}_{view}.png")
        render(action_name, frame, view, tile)
        img = bpy.data.images.load(tile)
        tiles.append(np.array(img.pixels[:]).reshape(H, W, 4))
    rows.append(np.concatenate(tiles, axis=1))

# Blender piksel dizisi alttan başlar: ilk satır (önden) üstte kalsın diye ters sırala.
sheet = np.concatenate(rows[::-1], axis=0)
out = bpy.data.images.new("sheet", sheet.shape[1], sheet.shape[0], alpha=True)
out.pixels = sheet.ravel()
out.filepath_raw = out_png
out.file_format = "PNG"
out.save()
print("SHEET", out_png, "columns:", [p[0] for p in POSES], "rows:", list(VIEWS))
