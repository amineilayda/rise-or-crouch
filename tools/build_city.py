"""6. bölümün şehir sokağını (level_6.blend) kurar.

KayKit City Bits ile: oyuncular kaldırımda; oyun kurucunun arkasında yaya
geçitli bir cadde, üstünde arabalar ve taksiler; köşelerde trafik ışıkları ve
sokak lambaları; caddenin karşısında bina sırası (iki çatıda su kulesi),
arkasında giderek yükselen binalar. Akşam göğü ve lamba ışıkları oyunda (levels.dart) ayarlanır.

Kullanım:
  blender --background --factory-startup --python tools/build_city.py -- <çıktı.blend> [önizleme.png]

Koordinatlar build_scene.py ile aynı: sıra y=0'da, oyun kurucu y=7'de, kamera
y=-6.5'te +Y'ye bakıyor. City Bits modelleri minyatür (araba 0,94 birim); hepsi
[S] kat büyütülür, bir yol karesi S*2 birim olur.
"""
import math
import os
import random
import sys

import bpy
from mathutils import Vector

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV = os.path.join(ROOT, "tools", "source_models", "environment")
KIT = os.path.join(ENV, "KayKit_City_Bits", "Assets", "gltf")
args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
OUT_BLEND = os.path.abspath(args[0]) if args else os.path.join(ENV, "level_6.blend")
OUT_PREVIEW = os.path.abspath(args[1]) if len(args) > 1 else None

random.seed(61)

# Oyundaki yerleşim (rise_crouch_game.dart ve stage_camera.dart ile aynı).
ROW_SIZE, SPACING, PLAYER_SLOT = 6, 1.45, 3
LEADER_Y = 7.0
CAMERA_POS = Vector(((PLAYER_SLOT - (ROW_SIZE - 1) / 2) * SPACING, -6.5, 4.0))
CAMERA_TARGET = Vector((0, 7.0, 1.8))
CAMERA_FOV_Y = 70.0

S = 3.5  # City Bits ölçeği
TILE = 2.0 * S  # bir yol / bina karesinin kenarı
ROAD_Y = 14.0  # caddenin ortası
BLOCK_Y = ROAD_Y + TILE  # caddenin karşısındaki ilk bina sırası
GROUND = "#C9C2B6"  # kaldırım grisi

BUILDINGS = ["building_A", "building_B", "building_C", "building_D",
             "building_E", "building_F", "building_G", "building_H"]
TALL = ["building_C", "building_D", "building_G", "building_H"]
CARS = ["car_hatchback", "car_sedan", "car_stationwagon", "car_taxi", "car_taxi", "car_police"]


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
    print(f"MODEL {name:<32} boy={(hi.z - lo.z) * S:.2f}")
    return mesh


def place(name, zone, x, y, scale=1.0, angle=None, z=0.0):
    """Bağlı bir kopya koyar; [scale] S ile çarpılır, [angle] derece."""
    obj = model(name).copy()  # mesh verisi paylaşılır
    obj.location = (x, y, z)
    obj.rotation_mode = "XYZ"  # glTF içe aktarma kuaterniyona geçirir; açı yoksa uygulanmaz
    obj.rotation_euler = (0, 0, math.radians(random.uniform(-8, 8) if angle is None else angle))
    obj.scale = (scale * S,) * 3
    zones[zone].objects.link(obj)
    return obj


# Yakın: oyun kurucunun arkasında X boyunca uzanan cadde; ortada yaya geçidi.
for i in range(-4, 5):
    name = "road_straight_crossing" if i == 0 else "road_straight"
    place(name, "Yakin", i * TILE, ROAD_Y, angle=90, z=0.01)
# İki şeritte arabalar: yakın şerit sağa, uzak şerit sola gider.
for lane_y, heading, xs in ((ROAD_Y - 1.7, -90, (-22, -12.5, 9, 19)), (ROAD_Y + 1.7, 90, (-17, -7.5, 13.5, 25))):
    for x in xs:
        place(random.choice(CARS), "Yakin", x + random.uniform(-1, 1), lane_y, angle=heading)

# Kaldırım: yaya geçidinin iki yanında trafik ışıkları, lambalar, banklar.
place("trafficlight_B", "Yakin", -4.2, ROAD_Y - TILE / 2 - 0.5, angle=0)
place("trafficlight_B", "Yakin", 4.2, ROAD_Y + TILE / 2 + 0.5, angle=180)
for x in (-11.0, 11.0):
    place("streetlight", "Yakin", x, ROAD_Y - TILE / 2 - 0.4, angle=0)
    place("streetlight", "Yakin", x, ROAD_Y + TILE / 2 + 0.4, angle=180)
place("bench", "Yakin", -6.5, 9.5, angle=0)
place("bench", "Yakin", 6.5, 9.5, angle=0)
place("firehydrant", "Yakin", -2.8, 9.8)
place("dumpster", "Yakin", 8.8, 7.0, angle=-90)
place("box_A", "Yakin", 9.4, 5.6)
place("box_B", "Yakin", 8.6, 5.3)
place("trash_A", "Yakin", 8.6, 8.6)
for x in (-8.5, -4.5, 4.5, 8.5):
    place("bush", "Yakin", x, 10.4, 1.1)

# Orta: caddenin karşısında birbirine bitişik bina sırası.
for i in range(-3, 4):
    place(BUILDINGS[(i + 5 * 3) % len(BUILDINGS)], "Orta", i * TILE, BLOCK_Y, angle=0)
# İki alçak binanın çatısında su kulesi.
for i in (-3, 2):
    name = BUILDINGS[(i + 5 * 3) % len(BUILDINGS)]
    place("watertower", "Orta", i * TILE + 1.2, BLOCK_Y + 1.5, z=model(name).dimensions.z * S - 0.3)
# Bina sırasının önünde arada bir sokak lambası.
for i in range(-3, 3, 2):
    place("streetlight", "Orta", i * TILE + TILE / 2, BLOCK_Y - TILE / 2 - 0.3, angle=0)

# Uzak: geride giderek yükselen binalar.
for row in range(1, 5):
    y = BLOCK_Y + row * TILE * 1.15
    scale = 1.0 + 0.35 * row
    for i in range(-6 - row, 7 + row):
        x = i * TILE * scale * 0.9 + random.uniform(-1, 1)
        # Kameranın görmediği yanlar dosyayı büyütmesin.
        if abs(x) > 10 + 0.5 * y:
            continue
        name = random.choice(TALL if row > 1 else BUILDINGS)
        place(name, "Uzak", x, y, scale * random.uniform(0.95, 1.25), angle=random.uniform(-6, 6))


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

# Akşam güneşi: alçak ve turuncu.
sun = bpy.data.objects.new("Gunes", bpy.data.lights.new("Gunes", "SUN"))
sun.data.energy = 3.0
sun.data.color = (1.0, 0.8, 0.6)
sun.location = (10, -12, 10)
sun.rotation_euler = (Vector((0, 0, 0)) - sun.location).to_track_quat("-Z", "Y").to_euler()
guides.objects.link(sun)

scene.world = bpy.data.worlds.new("Gokyuzu")
scene.world.color = srgb("#F2A66B")[:3]

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
