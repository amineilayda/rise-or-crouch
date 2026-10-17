"""Oyun kurucunun (Rogue) bölüme özel kıyafetini üretir. Yüz, saç ve küpe
aynı kalır; yalnızca kıyafet kareleri yeniden boyanır.

Temalar:
  snow     3. bölüm: soluk mavi tunik ve pelerin, kar beyazı kayışlar ve botlar
  dungeon  2. bölüm: kahverengi deri tunik, koyu kızıl-kahve pelerin, demir
           kayışlar, koyu deri eldiven ve botlar
  pirate   4. bölüm: kırmızı korsan ceketi, siyah pelerin, altın kayışlar,
           siyah botlar ve sol gözde göz bandı (kafa kemiğine bağlı)

Rogue'un dokusu 8×4 renk karesinden oluşan bir atlas; hangi karenin hangi
parçada kullanıldığı modelin UV'lerinden çıkarıldı (bkz. TILES). Her karenin
üstten alta renk geçişi korunur, sadece rengi değişir.

Kullanım:
  blender --background --factory-startup --python tools/make_rogue_outfit.py -- <Rogue.glb> <tema> <çıktı.glb>
Çıktı daha sonra make_animations.py'den geçirilir.
"""
import math
import sys

import bmesh
import bpy
import numpy as np
from mathutils import Matrix, Vector

src, theme, dst = sys.argv[sys.argv.index("--") + 1:][:3]

COLS, ROWS = 8, 4
# Kareler (satır, sütun) üstten sayılır:
#   (1, 0) tunik ve pantolon üstü   (1, 1) pelerin ve göğüs   (1, 7) pantolon
#   (0, 5) omuz ve bel kayışları    (0, 6) kemerler
#   (2, 7) eldivenler               (2, 3) botlar
THEMES = {
    "snow": {
        (1, 0): "#8FB3D9", (1, 1): "#BCD6EE", (1, 7): "#7393B4",
        (0, 5): "#EAF2FA", (0, 6): "#DCE8F4",
        (2, 7): "#E4EEF8", (2, 3): "#D2E2F2",
    },
    "dungeon": {
        # Zindan loş olduğu için kahveler biraz açık tutuldu.
        (1, 0): "#A8743F", (1, 1): "#8E4A2A", (1, 7): "#6E5038",
        (0, 5): "#A4A4AC", (0, 6): "#5A402A",
        (2, 7): "#7E5634", (2, 3): "#5E4028",
    },
    "pirate": {
        (1, 0): "#A8302E", (1, 1): "#2A2A30", (1, 7): "#4E3A2A",
        (0, 5): "#D4A84A", (0, 6): "#2E2219",
        (2, 7): "#6E4A2C", (2, 3): "#262626",
    },
}
# Göz bandı olan temalar. Rogue'un gözleri (±0.19, -0.42, 1.60) civarında,
# kafanın ortası z≈1.62; karakter -Y'ye bakıyor.
EYE_PATCH = {"pirate"}
EYE = Vector((0.19, -0.425, 1.60))
HEAD_CENTER = Vector((0, -0.02, 1.66))
TILES = THEMES[theme]


def srgb(hex_color):
    return np.array([int(hex_color[i:i + 2], 16) / 255 for i in (1, 3, 5)], dtype=np.float32)


bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=src)

image = next(i for i in bpy.data.images if i.size[0] > 0)
w, h = image.size
pixels = np.array(image.pixels[:], dtype=np.float32).reshape(h, w, 4)  # satır 0 = alt
tw, th = w // COLS, h // ROWS
for (row, col), hex_color in TILES.items():
    y0 = h - (row + 1) * th
    tile = pixels[y0:y0 + th, col * tw:(col + 1) * tw, :3]
    # Parlaklık geçişini koru: koyu uç %70, açık uç %100 parlaklıkta.
    lum = tile @ np.array([0.299, 0.587, 0.114], dtype=np.float32)
    lo, hi = lum.min(), lum.max()
    k = (lum - lo) / (hi - lo) if hi > lo else np.ones_like(lum)
    shade = 0.7 + 0.3 * k
    pixels[y0:y0 + th, col * tw:(col + 1) * tw, :3] = shade[..., None] * srgb(hex_color)

outfit = bpy.data.images.new(f"{image.name.split('.')[0]}_{theme}", w, h, alpha=True)
outfit.pixels = pixels.ravel()
outfit.file_format = "PNG"
image.user_remap(outfit)
print("RECOLORED", image.name, theme, f"{w}x{h}", "kare:", len(TILES))



def add_eye_patch():
    """Siyah göz bandı ve kafayı çaprazlama saran ince kayış."""
    arm = next(o for o in bpy.data.objects if o.type == "ARMATURE")
    mat = bpy.data.materials.new("GozBandi")
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (0.012, 0.012, 0.014, 1)
    bsdf.inputs["Roughness"].default_value = 0.8

    # Bant: göze yapışık basık elips.
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=20, v_segments=12, radius=1.0)
    bmesh.ops.transform(bm, matrix=Matrix.Diagonal((0.085, 0.03, 0.09, 1)), verts=bm.verts)
    bmesh.ops.translate(bm, vec=EYE + Vector((0, -0.01, 0)), verts=bm.verts)
    patch_mesh = bpy.data.meshes.new("GozBandi")
    bm.to_mesh(patch_mesh)
    bm.free()
    patch = bpy.data.objects.new("GozBandi", patch_mesh)
    bpy.context.collection.objects.link(patch)

    # Kayış: kafayı saran ince halka.
    bpy.ops.mesh.primitive_torus_add(major_radius=0.6, minor_radius=0.016, major_segments=64, minor_segments=8)
    strap = bpy.context.active_object
    # Bandın olduğu yanda göz hizasında, karşı yanda alnın üstünde.
    strap.location = HEAD_CENTER
    strap.rotation_euler = (0, math.radians(22), 0)
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    # Halkayı kafanın (saç dahil) yüzeyine oturt: havada durmasın.
    wrap = strap.modifiers.new("Sar", "SHRINKWRAP")
    wrap.target = bpy.data.objects["Rogue_Head"]
    wrap.wrap_method = "NEAREST_SURFACEPOINT"
    wrap.offset = 0.012
    bpy.ops.object.modifier_apply(modifier=wrap.name)

    bpy.ops.object.select_all(action="DESELECT")
    patch.select_set(True)
    strap.select_set(True)
    bpy.context.view_layer.objects.active = patch
    bpy.ops.object.join()
    patch.data.materials.clear()
    patch.data.materials.append(mat)
    for poly in patch.data.polygons:
        poly.use_smooth = True
    group = patch.vertex_groups.new(name="head")
    group.add(list(range(len(patch.data.vertices))), 1.0, "REPLACE")
    patch.parent = arm
    patch.modifiers.new("Armature", "ARMATURE").object = arm
    print("EYE_PATCH köşe:", len(patch.data.vertices))


if theme in EYE_PATCH:
    add_eye_patch()

bpy.ops.export_scene.gltf(filepath=dst, export_format="GLB", export_animations=False)
print("EXPORTED", dst)
