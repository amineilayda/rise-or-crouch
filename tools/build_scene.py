"""KayKit Forest Nature Pack ile başlangıç orman sahnesini (level_1.blend) kurar.

Sahne Blender'da açılıp elle düzenlenebilir; sonra tools/export_scene.py ile
oyuna aktarılır.

Kullanım:
  blender --background --factory-startup --python tools/build_scene.py -- <çıktı.blend> [önizleme.png]

Koordinatlar: Blender Z yukarı. Oyundaki (x, y, z) noktası Blender'da
(x, -z, y)'dir. Sıra Blender'da y=0 çizgisinde, oyun kurucu y=7'de, kamera
y=-6.5'te ve +Y yönüne bakıyor.
"""
import math
import os
import random
import sys

import bpy
from mathutils import Vector

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PACK = os.path.join(
    ROOT, "tools", "source_models", "environment", "KayKit_Forest_Nature_Pack",
    "KayKit_Forest_Nature_Pack_1.0_FREE", "Assets", "gltf",
)
args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
OUT_BLEND = os.path.abspath(args[0]) if args else os.path.join(ROOT, "tools", "source_models", "environment", "level_1.blend")
OUT_PREVIEW = os.path.abspath(args[1]) if len(args) > 1 else None

random.seed(7)

# Oyundaki yerleşim (rise_crouch_game.dart ve stage_camera.dart ile aynı).
ROW_SIZE, SPACING, PLAYER_SLOT = 6, 1.45, 3
LEADER_Y = 7.0  # oyunda z = -7
CAMERA_POS = Vector(((PLAYER_SLOT - (ROW_SIZE - 1) / 2) * SPACING, -6.5, 4.0))
CAMERA_TARGET = Vector((0, 7.0, 1.8))
CAMERA_FOV_Y = 70.0


def srgb(hex_color):
    """'#RRGGBB' → Blender'ın beklediği doğrusal RGBA."""
    c = [int(hex_color[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    return (*[v ** 2.2 for v in c], 1.0)


def collection(name, hide_render=False):
    col = bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(col)
    col.hide_render = hide_render
    return col


def flat_material(name, hex_color):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    mat.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = srgb(hex_color)
    mat.diffuse_color = srgb(hex_color)
    return mat


bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene

source = collection("_Kaynak")  # her modelin tek kopyası (gizli)
guides = collection("_Rehber")  # zemin, karakter yerleri, kamera (oyuna aktarılmaz)
zones = {name: collection(name) for name in ("Yakin", "Orta", "Uzak")}
bpy.context.view_layer.layer_collection.children["_Kaynak"].exclude = True


# --- Modelleri birer kez yükle ---
_prototypes = {}


def prototype(name):
    if name in _prototypes:
        return _prototypes[name]
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=os.path.join(PACK, name + ".gltf"))
    new = [o for o in bpy.data.objects if o not in before]
    mesh = next(o for o in new if o.type == "MESH")
    for obj in new:
        for col in obj.users_collection:
            col.objects.unlink(obj)
        if obj is not mesh:
            bpy.data.objects.remove(obj)
    mesh.parent = None
    mesh.location = (0, 0, 0)
    mesh.rotation_euler = (0, 0, 0)
    source.objects.link(mesh)
    _prototypes[name] = mesh
    print(f"MODEL {name:<28} boyut={tuple(round(d, 2) for d in mesh.dimensions)}")
    return mesh


def place(name, zone, x, y, height=None, scale=1.0):
    """Modelin bağlantılı bir kopyasını koyar; [height] verilirse o boya ölçekler."""
    proto = prototype(name)
    obj = proto.copy()  # mesh verisi paylaşılır (Alt+D gibi)
    obj.location = (x, y, 0)
    obj.rotation_euler = (0, 0, random.uniform(0, 2 * math.pi))
    s = (height / max(proto.dimensions.z, 0.01)) if height else scale
    obj.scale = (s, s, s)
    zones[zone].objects.link(obj)
    return obj


def scatter(zone, names, count, x_range, y_range, min_dist, **size):
    """Bölgeye birbirine [min_dist]'ten yakın olmayan rastgele noktalar serpiştirir."""
    placed, tries = [], 0
    while len(placed) < count and tries < count * 200:
        tries += 1
        p = Vector((random.uniform(*x_range), random.uniform(*y_range)))
        if any((p - q).length < min_dist for q in placed):
            continue
        # Sıra ile oyun kurucu arasındaki koridor boş kalsın (çimen hariç).
        if size.get("keep_corridor", True) and -1.5 < p.y < LEADER_Y + 1.5 and abs(p.x) < 8:
            continue
        placed.append(p)
        kwargs = {}
        if "height" in size:
            kwargs["height"] = random.uniform(*size["height"])
        else:
            kwargs["scale"] = random.uniform(*size.get("scale", (1, 1)))
        place(random.choice(names), zone, p.x, p.y, **kwargs)
    print(f"ZONE {zone}: {len(placed)}/{count} {names[0].split('_')[0]}")


TREES = ["Tree_1_A_Color1", "Tree_1_B_Color1", "Tree_2_A_Color1", "Tree_2_B_Color1",
         "Tree_2_C_Color1", "Tree_3_A_Color1", "Tree_3_B_Color1", "Tree_4_A_Color1", "Tree_4_B_Color1"]
BUSHES = ["Bush_1_A_Color1", "Bush_1_C_Color1", "Bush_2_A_Color1", "Bush_2_C_Color1",
          "Bush_3_A_Color1", "Bush_4_A_Color1", "Bush_4_C_Color1"]
ROCKS = ["Rock_1_A_Color1", "Rock_1_E_Color1", "Rock_2_A_Color1", "Rock_2_D_Color1",
         "Rock_3_A_Color1", "Rock_3_F_Color1", "Rock_3_K_Color1"]
GRASS = ["Grass_1_A_Color1", "Grass_1_C_Color1", "Grass_2_A_Color1", "Grass_2_C_Color1"]

# Yakın: oyun kurucunun arkası ve kenarlar — çalılar, küçük kayalar, iki "çerçeve" ağaç.
scatter("Yakin", BUSHES, 12, (-7, 7), (9.5, 14), 1.6, height=(0.7, 1.3))
scatter("Yakin", ROCKS, 6, (-7, 7), (9.5, 14), 2.0, height=(0.4, 0.9))
place("Tree_2_B_Color1", "Yakin", -6.2, 12.5, height=6.5)
place("Tree_1_B_Color1", "Yakin", 6.4, 13.0, height=7.0)
# Zemin örtüsü: çimen tutamları her yerde (alçak, görüşü kapatmaz).
# Kameraya çok yakın olanlar ekranı kaplamasın diye sıranın arkasından başlar.
scatter("Yakin", GRASS, 60, (-9, 9), (1.0, 14), 0.9, scale=(0.35, 0.7), keep_corridor=False)

# Orta: ağaç kümeleri ve kayalar.
scatter("Orta", TREES, 18, (-14, 14), (15, 30), 3.2, height=(5.0, 7.5))
scatter("Orta", ROCKS, 7, (-14, 14), (15, 30), 3.0, height=(0.8, 1.8))
scatter("Orta", BUSHES, 10, (-14, 14), (14, 30), 2.0, height=(0.8, 1.4))

# Uzak: sık bir orman duvarı ve büyük kayalar (tepe gibi).
scatter("Uzak", TREES, 55, (-32, 32), (32, 70), 3.6, height=(7.0, 11.0))
scatter("Uzak", ROCKS, 8, (-30, 30), (35, 70), 9.0, height=(4.0, 8.0))


# --- Rehber: zemin, karakter yer tutucuları, kamera, ışık ---
ground = bpy.data.objects.new("Zemin", bpy.data.meshes.new("Zemin"))
ground.data.from_pydata([(-100, -100, 0), (100, -100, 0), (100, 100, 0), (-100, 100, 0)], [], [(0, 1, 2, 3)])
ground.data.materials.append(flat_material("Zemin", "#7CC850"))
guides.objects.link(ground)


def box(name, center, size, hex_color):
    bpy.ops.mesh.primitive_cube_add(location=center)
    obj = bpy.context.active_object
    obj.name = name
    obj.scale = (size[0] / 2, size[1] / 2, size[2] / 2)
    obj.data.materials.append(flat_material(name, hex_color))
    for col in obj.users_collection:
        col.objects.unlink(obj)
    guides.objects.link(obj)


for i in range(ROW_SIZE):
    x = (i - (ROW_SIZE - 1) / 2) * SPACING
    is_player = i == PLAYER_SLOT
    box("Oyuncu" if is_player else f"Kisi_{i + 1}", (x, 0, 0.65), (0.8, 0.6, 1.3),
        "#3B6FD8" if is_player else "#9AA5B1")
box("OyunKurucu", (0, LEADER_Y, 1.0), (1.2, 0.9, 2.0), "#D84B3B")

cam = bpy.data.objects.new("OyunKamerasi", bpy.data.cameras.new("OyunKamerasi"))
cam.data.sensor_fit = "VERTICAL"
cam.data.angle_y = math.radians(CAMERA_FOV_Y)
cam.data.clip_end = 500
cam.location = CAMERA_POS
cam.rotation_euler = (CAMERA_TARGET - CAMERA_POS).to_track_quat("-Z", "Y").to_euler()
guides.objects.link(cam)
scene.camera = cam
scene.render.resolution_x, scene.render.resolution_y = 1080, 2340
scene.render.resolution_percentage = 50

# Güneş: oyundaki ana ışıkla aynı yönden (sağ arka üstten).
sun = bpy.data.objects.new("Gunes", bpy.data.lights.new("Gunes", "SUN"))
sun.data.energy = 3.0
sun.data.color = (1.0, 0.89, 0.72)
sun.location = (8, -12, 14)
sun.rotation_euler = (Vector((0, 0, 0)) - sun.location).to_track_quat("-Z", "Y").to_euler()
guides.objects.link(sun)

scene.world = bpy.data.worlds.new("Gokyuzu")
scene.world.color = srgb("#8FD3F4")[:3]

os.makedirs(os.path.dirname(OUT_BLEND), exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=OUT_BLEND)
print("SAVED", OUT_BLEND, "nesne:", sum(len(c.objects) for c in zones.values()))

if OUT_PREVIEW:
    scene.render.engine = "BLENDER_WORKBENCH"
    scene.display.shading.light = "STUDIO"
    scene.display.shading.color_type = "TEXTURE"
    scene.display.shading.show_shadows = True
    scene.render.filepath = OUT_PREVIEW
    bpy.ops.render.render(write_still=True)
    print("PREVIEW", OUT_PREVIEW)
