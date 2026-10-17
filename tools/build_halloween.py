"""5. bölümün perili mezarlığını (level_5.blend) kurar.

KayKit Halloween Bits ile: oyun kurucunun arkasında oyma balkabakları, mum ve
kafatasları; iki yanda mezar taşı sıraları, fenerli direkler ve kuru ağaçlar;
arkada demir parmaklıklı çit, kemerli kapı ve dev bir mahzen; uzakta turuncu
ve sarı çam ağaçları. Gece göğü, ay ışığı ve balkabağı ışıkları oyunda
(levels.dart) ayarlanır.

Kullanım:
  blender --background --factory-startup --python tools/build_halloween.py -- <çıktı.blend> [önizleme.png]

Koordinatlar build_scene.py ile aynı: sıra y=0'da, oyun kurucu y=7'de, kamera
y=-6.5'te +Y'ye bakıyor. KayKit modelleri karakterlerle aynı ölçekte; çoğu
kendi boyunda konur.
"""
import math
import os
import random
import sys

import bpy
from mathutils import Vector

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV = os.path.join(ROOT, "tools", "source_models", "environment")
KIT = os.path.join(ENV, "KayKit_HalloweenBits_1.0_FREE", "Assets", "gltf")
args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
OUT_BLEND = os.path.abspath(args[0]) if args else os.path.join(ENV, "level_5.blend")
OUT_PREVIEW = os.path.abspath(args[1]) if len(args) > 1 else None

random.seed(31)

# Oyundaki yerleşim (rise_crouch_game.dart ve stage_camera.dart ile aynı).
ROW_SIZE, SPACING, PLAYER_SLOT = 6, 1.45, 3
LEADER_Y = 7.0
CAMERA_POS = Vector(((PLAYER_SLOT - (ROW_SIZE - 1) / 2) * SPACING, -6.5, 4.0))
CAMERA_TARGET = Vector((0, 7.0, 1.8))
CAMERA_FOV_Y = 70.0

GROUND = "#3A3240"
FENCE_Y = 20.0  # mezarlığın arka çiti


def srgb(hex_color):
    c = [int(hex_color[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    return (*[v ** 2.2 for v in c], 1.0)


def collection(name):
    col = bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(col)
    return col


def flat_material(name, hex_color):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    mat.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = srgb(hex_color)
    mat.diffuse_color = srgb(hex_color)
    return mat


bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
source = collection("_Kaynak")
guides = collection("_Rehber")
# export_scene.py bu üç koleksiyonu aktarır.
zones = {name: collection(name) for name in ("Yakin", "Orta", "Uzak")}
bpy.context.view_layer.layer_collection.children["_Kaynak"].exclude = True


# --- Modelleri birer kez yükle ---
_prototypes = {}


def model(name):
    """Modeli yükler, tabanını yere ve ortasını merkeze oturtur."""
    if name in _prototypes:
        return _prototypes[name]
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=os.path.join(KIT, name + ".gltf"))
    new = [o for o in bpy.data.objects if o not in before]
    meshes = [o for o in new if o.type == "MESH"]
    for mesh in meshes:
        mesh.data.transform(mesh.matrix_world)
    for obj in new:
        if obj not in meshes:
            bpy.data.objects.remove(obj)
    for mesh in meshes:
        mesh.parent = None
        mesh.matrix_world.identity()
    if len(meshes) > 1:
        bpy.ops.object.select_all(action="DESELECT")
        for mesh in meshes:
            mesh.select_set(True)
        bpy.context.view_layer.objects.active = meshes[0]
        bpy.ops.object.join()
    mesh = meshes[0]
    for col in list(mesh.users_collection):
        col.objects.unlink(mesh)
    verts = [v.co for v in mesh.data.vertices]
    lo = Vector([min(v[i] for v in verts) for i in range(3)])
    hi = Vector([max(v[i] for v in verts) for i in range(3)])
    offset = Vector(((lo.x + hi.x) / 2, (lo.y + hi.y) / 2, lo.z))
    for v in mesh.data.vertices:
        v.co -= offset
    mesh.data.update()
    source.objects.link(mesh)
    _prototypes[name] = mesh
    print(f"MODEL {name:<32} boy={hi.z - lo.z:.2f}")
    return mesh


def place(name, zone, x, y, scale=1.0, angle=None):
    """Bağlı bir kopya koyar. Model -Y'ye (kameraya) bakar; [angle] derece."""
    obj = model(name).copy()  # mesh verisi paylaşılır
    obj.location = (x, y, 0)
    obj.rotation_euler = (0, 0, math.radians(random.uniform(-12, 12) if angle is None else angle))
    obj.scale = (scale, scale, scale)
    zones[zone].objects.link(obj)
    return obj


def scatter(zone, names, count, x_range, y_range, min_dist, scale=(1.0, 1.0)):
    placed, tries = [], 0
    while len(placed) < count and tries < count * 200:
        tries += 1
        p = Vector((random.uniform(*x_range), random.uniform(*y_range)))
        if any((p - q).length < min_dist for q in placed):
            continue
        # Sıra ile oyun kurucu arasındaki koridor boş kalsın.
        if -1.5 < p.y < LEADER_Y + 1.5 and abs(p.x) < 8:
            continue
        placed.append(p)
        place(random.choice(names), zone, p.x, p.y, random.uniform(*scale), angle=random.uniform(0, 360))
    print(f"ZONE {zone}: {len(placed)}/{count}")


GRAVES = ["grave_A", "grave_B", "gravestone", "grave_A_destroyed", "gravemarker_A", "gravemarker_B"]
SMALL = ["pumpkin_orange", "pumpkin_yellow", "pumpkin_orange_small", "pumpkin_yellow_small",
         "skull", "bone_A", "bone_B", "bone_C", "candle_melted", "candle_triple"]
DEAD_TREES = ["tree_dead_large", "tree_dead_medium", "tree_dead_small", "tree_dead_large_decorated"]
PINES = ["tree_pine_orange_large", "tree_pine_orange_medium", "tree_pine_yellow_large",
         "tree_pine_yellow_medium", "tree_pine_orange_small", "tree_pine_yellow_small"]

# Yakın: oyun kurucunun arkasında "sahne": iki oyma balkabağı, mumlar, kafatası.
place("pumpkin_orange_jackolantern", "Yakin", -2.4, 9.3, 1.0, angle=15)
place("pumpkin_yellow_jackolantern", "Yakin", 2.5, 9.4, 1.0, angle=-15)
place("skull_candle", "Yakin", -0.9, 10.2, 0.8, angle=5)
place("candle_triple", "Yakin", 1.0, 10.0, 1.0)
place("candle_melted", "Yakin", -3.6, 9.0, 1.0)
place("candle", "Yakin", 3.7, 9.1, 1.0)
place("shrine_candles", "Yakin", 0.0, 11.4, 1.2, angle=0)
# İki yanda fenerli direkler ve oyma balkabağı + mezar sıraları.
place("post_lantern", "Yakin", -6.0, 9.5, 1.1, angle=90)
place("post_skull", "Yakin", 6.2, 9.7, 1.1, angle=-90)
for i, y in enumerate((9.5, 12.5, 15.5)):
    for side in (-1, 1):
        for j, x in enumerate((4.6, 7.4, 10.2)):
            name = GRAVES[(i * 3 + j + (side > 0)) % len(GRAVES)]
            place(name, "Yakin", side * x + random.uniform(-0.3, 0.3), y + random.uniform(-0.3, 0.3), 0.9)
place("coffin_decorated", "Yakin", -8.6, 17.6, 0.9, angle=80)
place("bench_decorated", "Yakin", 8.4, 17.8, 1.0, angle=-10)
place("ribcage", "Yakin", -4.8, 17.0, 0.9)
scatter("Yakin", SMALL, 14, (-11, 11), (8.5, 18.5), 1.3, (0.8, 1.1))
place("tree_dead_large_decorated", "Yakin", -10.5, 11.0, 1.4, angle=30)
place("tree_dead_large", "Yakin", 11.0, 12.0, 1.5, angle=-40)

# Orta: arka çit ve ortada kemerli kapı, kapının ardında mahzen.
for x in range(-22, 23, 4):
    if x == 0:
        place("fence_gate", "Orta", 0.0, FENCE_Y, 1.0, angle=0)
        continue
    broken = random.random() < 0.25
    place("fence_broken" if broken else "fence", "Orta", float(x), FENCE_Y, 1.0, angle=0)
place("arch_gate", "Orta", 0.0, FENCE_Y + 3.0, 1.2, angle=0)
place("crypt", "Orta", 0.0, FENCE_Y + 9.0, 1.3, angle=0)
place("pillar", "Orta", -5.5, FENCE_Y + 5.0, 1.0)
place("pillar", "Orta", 5.5, FENCE_Y + 5.0, 1.0)
place("lantern_standing", "Orta", -2.4, FENCE_Y + 1.5, 1.0)
place("lantern_standing", "Orta", 2.4, FENCE_Y + 1.5, 1.0)
scatter("Orta", DEAD_TREES, 8, (-20, 20), (FENCE_Y - 1.5, FENCE_Y + 6), 3.5, (1.2, 1.7))
scatter("Orta", GRAVES, 10, (-20, 20), (FENCE_Y + 2, FENCE_Y + 12), 3.0, (0.9, 1.1))

# Uzak: turuncu-sarı çam ormanı ve kuru ağaçlar.
scatter("Uzak", PINES, 45, (-38, 38), (FENCE_Y + 12, 70), 3.8, (1.2, 2.0))
scatter("Uzak", DEAD_TREES, 12, (-38, 38), (FENCE_Y + 10, 60), 5.0, (1.6, 2.2))


# --- Rehber: zemin, karakter yer tutucuları, kamera, ışık ---
ground = bpy.data.objects.new("Zemin", bpy.data.meshes.new("Zemin"))
ground.data.from_pydata([(-100, -100, 0), (100, -100, 0), (100, 100, 0), (-100, 100, 0)], [], [(0, 1, 2, 3)])
ground.data.materials.append(flat_material("Zemin", GROUND))
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
        "#FF8F00" if is_player else "#9AA5B1")
box("OyunKurucu", (0, LEADER_Y, 1.0), (1.2, 0.9, 2.0), "#6A3A8A")

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

# Ay ışığı: soğuk mor-mavi.
moon = bpy.data.objects.new("Ay", bpy.data.lights.new("Ay", "SUN"))
moon.data.energy = 2.2
moon.data.color = (0.75, 0.75, 1.0)
moon.location = (8, -12, 14)
moon.rotation_euler = (Vector((0, 0, 0)) - moon.location).to_track_quat("-Z", "Y").to_euler()
guides.objects.link(moon)

scene.world = bpy.data.worlds.new("Gokyuzu")
scene.world.color = srgb("#2A1E3E")[:3]

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
