"""7. bölümün restoranını (level_7.blend) kurar.

KayKit Restaurant Bits ile: oyuncular yemek salonunda, mutfak karosu üstünde;
oyun kurucunun arkasında ocaklı, lavabolu uzun bir tezgâh, üstünde davlumbazlar;
en arkada sipariş pencereli duvar, asma dolaplar ve iki buzdolabı; yanlarda
yuvarlak masalar ve sandalyeler. Sıcak iç mekân ışıkları oyunda (levels.dart)
ayarlanır.

Kullanım:
  blender --background --factory-startup --python tools/build_restaurant.py -- <çıktı.blend> [önizleme.png]

Koordinatlar build_scene.py ile aynı: sıra y=0'da, oyun kurucu y=7'de, kamera
y=-6.5'te +Y'ye bakıyor. Restaurant Bits karakterlerle aynı ölçekte; duvara
asılan parçalar (davlumbaz, dolap) kendi yüksekliklerinde kalır.
"""
import math
import os
import random
import sys

import bpy
from mathutils import Vector

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV = os.path.join(ROOT, "tools", "source_models", "environment")
KIT = os.path.join(ENV, "KayKit_Restaurant_Bits", "Assets", "gltf")
args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
OUT_BLEND = os.path.abspath(args[0]) if args else os.path.join(ENV, "level_7.blend")
OUT_PREVIEW = os.path.abspath(args[1]) if len(args) > 1 else None

random.seed(71)

# Oyundaki yerleşim (rise_crouch_game.dart ve stage_camera.dart ile aynı).
ROW_SIZE, SPACING, PLAYER_SLOT = 6, 1.45, 3
LEADER_Y = 7.0
CAMERA_POS = Vector(((PLAYER_SLOT - (ROW_SIZE - 1) / 2) * SPACING, -6.5, 4.0))
CAMERA_TARGET = Vector((0, 7.0, 1.8))
CAMERA_FOV_Y = 70.0

COUNTER_Y = 10.0  # mutfak tezgâhının ortası
WALL_Y = 12.6  # arka duvar
GROUND = "#8A6A52"

# Duvara asılan parçalar: tabanları yere indirilmez.
HANGING = {"extractorhood", "kitchencabinet", "kitchencabinet_half", "shelf_papertowel_decorated"}


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
    """Modeli yükler, ortasını merkeze, tabanını (asılı değilse) yere oturtur."""
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
    offset = Vector(((lo.x + hi.x) / 2, (lo.y + hi.y) / 2, 0 if name in HANGING else lo.z))
    for v in mesh.data.vertices:
        v.co -= offset
    mesh.data.update()
    source.objects.link(mesh)
    _prototypes[name] = mesh
    print(f"MODEL {name:<40} boy={hi.z - lo.z:.2f}")
    return mesh


def place(name, zone, x, y, scale=1.0, angle=None, z=0.0):
    """Bağlı bir kopya koyar; [angle] derece."""
    obj = model(name).copy()  # mesh verisi paylaşılır
    obj.location = (x, y, z)
    obj.rotation_mode = "XYZ"  # glTF içe aktarma kuaterniyona geçirir; açı yoksa uygulanmaz
    obj.rotation_euler = (0, 0, math.radians(random.uniform(-6, 6) if angle is None else angle))
    obj.scale = (scale,) * 3
    zones[zone].objects.link(obj)
    return obj


# Zemin: mutfak karoları (üst yüzleri zemin hizasında).
for ix in range(-4, 5):
    for iy in range(-2, 4):
        place("floor_kitchen", "Yakin", ix * 4.0, iy * 4.0 + 1.0, angle=0, z=-0.49)

# Tezgâh: oyun kurucunun arkasında soldan sağa ocaklar, lavabo, tezgâhlar.
COUNTER = ["kitchencounter_straight_A_decorated", "stove_multi_decorated", "kitchencounter_straight_decorated",
           "kitchencounter_sink_backsplash", "stove_single", "kitchencounter_straight_A_decorated",
           "stove_multi_decorated", "kitchencounter_straight_B_backsplash", "oven"]
for i, name in enumerate(COUNTER):
    x = (i - (len(COUNTER) - 1) / 2) * 2.0
    place(name, "Yakin", x, COUNTER_Y, angle=0)
    if name.startswith("stove"):
        place("extractorhood", "Orta", x, WALL_Y - 0.3, angle=0)
    elif name != "oven":
        place("kitchencabinet", "Orta", x, WALL_Y - 0.3, angle=0)
# Tezgâhın üstünde tencereler.
place("pot_A_stew", "Yakin", -6.0, COUNTER_Y, angle=0, z=1.2)
place("pot_large", "Yakin", 4.0, COUNTER_Y, angle=0, z=1.2)
# Tezgâhın iki ucunda buzdolapları, yanlarında kasalar.
place("fridge_A_decorated", "Yakin", -11.0, COUNTER_Y + 0.2, angle=0)
place("fridge_B", "Yakin", 11.0, COUNTER_Y + 0.2, angle=0)
place("crate_tomatoes", "Yakin", -13.0, COUNTER_Y - 0.5, angle=15)
place("crate_potatoes", "Yakin", 13.0, COUNTER_Y - 0.6, angle=-10)
place("crate_lettuce", "Yakin", 13.4, COUNTER_Y - 2.4, 0.9, angle=25)
# Salonla mutfağı ayıran iki sütun.
for x in (-4.6, 4.6):
    place("pillar_B", "Yakin", x, 8.2, angle=0)

# Yan taraflarda yemek masaları ve sandalyeler.
for side in (-1, 1):
    for y in (1.5, 6.0):
        x = side * 10.5  # yananların yürüdüğü kapıların yolunu kapatmasın
        place(random.choice(["table_round_A_decorated", "table_round_A"]), "Yakin", x, y, angle=random.uniform(0, 90))
        for k in range(4):
            a = k * 90 + 45
            place(random.choice(["chair_A", "chair_B"]), "Yakin",
                  x + 2.0 * math.cos(math.radians(a)), y + 2.0 * math.sin(math.radians(a)), angle=a + 90)

# Arka duvar: ortada sipariş penceresi; iki kat (üst kat düz duvar).
WALL = {0: "wall_orderwindow_decorated", 1: "wall_decorated", 2: "wall_window_open", 3: "wall"}
for i in range(-4, 5):
    place(WALL[min(abs(i), 3)], "Orta", i * 4.0, WALL_Y, angle=0)
    place("wall", "Orta", i * 4.0, WALL_Y, angle=0, z=4.0)
# Yan duvarlar.
for side in (-1, 1):
    for iy in range(-1, 4):
        place("wall_window_closed" if iy % 2 else "wall", "Uzak", side * 18.0, iy * 4.0, angle=90)


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

# Sıcak tavan ışığı.
lamp = bpy.data.objects.new("Lamba", bpy.data.lights.new("Lamba", "SUN"))
lamp.data.energy = 3.0
lamp.data.color = (1.0, 0.88, 0.72)
lamp.location = (4, -8, 12)
lamp.rotation_euler = (Vector((0, 0, 0)) - lamp.location).to_track_quat("-Z", "Y").to_euler()
guides.objects.link(lamp)

scene.world = bpy.data.worlds.new("Gokyuzu")
scene.world.color = srgb("#3A2A22")[:3]

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
