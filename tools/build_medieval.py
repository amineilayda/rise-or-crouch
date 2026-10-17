"""9. bölümün ortaçağ kalesini (level_9.blend) kurar.

KayKit Medieval Hexagon Pack ile: oyuncular kale avlusunda, düz çimenin
(oyunun zemin rengi) üstünde; oyun kurucunun arkasında ahşap bir sahne ve bayraklar; iki
yanda çadırlar, silah rafları, hedefler, variller ve kasalar; ortada kapılı taş
sur ve köşelerinde kuleler; surun ardında büyük kale ve kilise; en uzakta
ormanlı tepeler ve dağlar. Gökyüzü ve ışıklar oyunda (levels.dart) ayarlanır.

Kullanım:
  blender --background --factory-startup --python tools/build_medieval.py -- <çıktı.blend> [önizleme.png]

Koordinatlar build_scene.py ile aynı: sıra y=0'da, oyun kurucu y=7'de, kamera
y=-6.5'te +Y'ye bakıyor. Paket strateji oyunu ölçeğinde (varil 0,2 birim);
hepsi [S] kat büyütülür. Paketin altıgen zemin karoları kullanılmaz: üst
yüzleri oyunun zemin düzlemiyle aynı yükseklikte kalıp titreşiyordu.
"""
import math
import os
import random
import sys

import bpy
from mathutils import Vector

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV = os.path.join(ROOT, "tools", "source_models", "environment")
KIT = os.path.join(ENV, "KayKit_Medieval_Hexagon_Pack", "Assets", "gltf")
args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
OUT_BLEND = os.path.abspath(args[0]) if args else os.path.join(ENV, "level_9.blend")
OUT_PREVIEW = os.path.abspath(args[1]) if len(args) > 1 else None

random.seed(91)

# Oyundaki yerleşim (rise_crouch_game.dart ve stage_camera.dart ile aynı).
ROW_SIZE, SPACING, PLAYER_SLOT = 6, 1.45, 3
LEADER_Y = 7.0
CAMERA_POS = Vector(((PLAYER_SLOT - (ROW_SIZE - 1) / 2) * SPACING, -6.5, 4.0))
CAMERA_TARGET = Vector((0, 7.0, 1.8))
CAMERA_FOV_Y = 70.0

S = 4.0  # paket ölçeği
WALL_Y = 18.0  # sur
CASTLE_Y = 30.0
GROUND = "#6FA84A"

# Klasörleriyle modeller.
BLUE = "buildings/blue/"
NEUTRAL = "buildings/neutral/"
PROPS = "decoration/props/"
NATURE = "decoration/nature/"


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


def model(path):
    """Modeli yükler, tabanını yere ve ortasını merkeze oturtur."""
    if path in _prototypes:
        return _prototypes[path]
    name = path.rsplit("/", 1)[-1]
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=os.path.join(KIT, path + ".gltf"))
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
    _prototypes[path] = mesh
    print(f"MODEL {name:<32} boy={(hi.z - lo.z) * S:.2f}")
    return mesh


def place(path, zone, x, y, scale=1.0, angle=None, z=0.0):
    """Bağlı bir kopya koyar; [scale] S ile çarpılır, [angle] derece."""
    obj = model(path).copy()  # mesh verisi paylaşılır
    obj.location = (x, y, z)
    obj.rotation_mode = "XYZ"  # glTF içe aktarma kuaterniyona geçirir; açı yoksa uygulanmaz
    obj.rotation_euler = (0, 0, math.radians(random.uniform(-8, 8) if angle is None else angle))
    obj.scale = (scale * S,) * 3
    zones[zone].objects.link(obj)
    return obj


def scatter(zone, paths, count, x_range, y_range, min_dist, scale=(1.0, 1.0)):
    placed, tries = [], 0
    while len(placed) < count and tries < count * 200:
        tries += 1
        p = Vector((random.uniform(*x_range), random.uniform(*y_range)))
        if any((p - q).length < min_dist for q in placed):
            continue
        placed.append(p)
        place(random.choice(paths), zone, p.x, p.y, random.uniform(*scale), angle=random.uniform(0, 360))
    print(f"ZONE {zone}: {len(placed)}/{count}")


# Yakın: oyun kurucunun arkasında ahşap sahne, iki yanında bayraklar.
place(NEUTRAL + "building_stage_A", "Yakin", 0.0, 10.6, angle=0)
for x in (-3.4, 3.4):
    place(PROPS + "flag_blue", "Yakin", x, 9.6, 1.4, angle=0)
# Yanlarda çadırlar, silah rafları, hedefler ve erzak.
for side in (-1, 1):
    place(PROPS + "tent", "Yakin", side * 9.6, 7.0, angle=side * 30)
    place(PROPS + "tent", "Yakin", side * 9.5, 11.5, angle=side * -20)
place(PROPS + "weaponrack", "Yakin", -5.2, 9.0, angle=15)
place(PROPS + "target", "Yakin", 5.4, 9.2, angle=-20)
place(PROPS + "target", "Yakin", 6.4, 10.4, angle=-35)
place(BLUE + "building_well_blue", "Yakin", -6.0, 13.0)
for x, y in ((4.6, 12.6), (5.3, 13.1), (-3.8, 12.4)):
    place(random.choice([PROPS + "barrel", PROPS + "crate_A_big", PROPS + "crate_B_big"]), "Yakin", x, y)
place(PROPS + "wheelbarrow", "Yakin", -3.6, 7.6, angle=60)
place(PROPS + "sack", "Yakin", -4.0, 8.4, 1.4)
place(PROPS + "resource_lumber", "Yakin", 7.0, 14.5)

# Orta: kapılı taş sur, köşelerde kuleler; surun önünde evler ve pazar.
for i in range(-3, 4):
    path = NEUTRAL + ("wall_straight_gate" if i == 0 else "wall_straight")
    place(path, "Orta", i * 2.0 * S, WALL_Y, angle=0)
for x in (-14.0, 14.0):
    place(BLUE + "building_tower_A_blue", "Orta", x, WALL_Y)
place(BLUE + "building_market_blue", "Orta", 9.5, 15.0, angle=-10)
place(BLUE + "building_home_A_blue", "Orta", -10.0, 15.0, angle=20)
place(BLUE + "building_tavern_blue", "Orta", -14.5, 12.0, angle=40)

# Uzak: surun ardında kale, kilise, kuleler; ormanlı tepeler ve dağlar.
place(BLUE + "building_castle_blue", "Uzak", 0.0, CASTLE_Y, 1.2, angle=0)
place(BLUE + "building_church_blue", "Uzak", -12.0, CASTLE_Y - 2.0, angle=10)
place(BLUE + "building_tower_B_blue", "Uzak", 11.0, CASTLE_Y - 3.0)
place(BLUE + "building_windmill_blue", "Uzak", 20.0, CASTLE_Y + 4.0, angle=-20)
scatter("Uzak", [NATURE + "trees_A_large", NATURE + "trees_B_large", NATURE + "trees_A_medium"],
        16, (-34, 34), (WALL_Y + 4, WALL_Y + 26), 7.0, (1.0, 1.4))
scatter("Uzak", [NATURE + "hills_A_trees", NATURE + "hills_B_trees", NATURE + "hills_C_trees"],
        8, (-50, 50), (55, 70), 14.0, (2.0, 3.0))
scatter("Uzak", [NATURE + "mountain_A_grass_trees", NATURE + "mountain_B_grass_trees",
                 NATURE + "mountain_C_grass"], 7, (-60, 60), (75, 95), 18.0, (3.5, 5.0))


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

sun = bpy.data.objects.new("Gunes", bpy.data.lights.new("Gunes", "SUN"))
sun.data.energy = 3.0
sun.data.color = (1.0, 0.92, 0.8)
sun.location = (10, -12, 14)
sun.rotation_euler = (Vector((0, 0, 0)) - sun.location).to_track_quat("-Z", "Y").to_euler()
guides.objects.link(sun)

scene.world = bpy.data.worlds.new("Gokyuzu")
scene.world.color = srgb("#8CC8F0")[:3]

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
