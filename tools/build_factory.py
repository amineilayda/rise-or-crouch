"""8. bölümün fabrikasını (level_8.blend) kurar.

KayKit Prototype Bits ile: oyuncular fabrika zemininde; oyun kurucunun
arkasında üstünde kolilerin dizildiği uzun bir üretim bandı; iki yanda büyük
makineler, varil yığınları ve koli dolu paletler; tavanda çelik kirişler; en
arkada iki katlı duvar ve ortada yükleme kapısı. Soğuk fabrika ışıkları oyunda
(levels.dart) ayarlanır.

Kullanım:
  blender --background --factory-startup --python tools/build_factory.py -- <çıktı.blend> [önizleme.png]

Koordinatlar build_scene.py ile aynı: sıra y=0'da, oyun kurucu y=7'de, kamera
y=-6.5'te +Y'ye bakıyor. Prototype Bits karakterlerle aynı ölçekte.
"""
import math
import os
import random
import sys

import bpy
from mathutils import Vector

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV = os.path.join(ROOT, "tools", "source_models", "environment")
KIT = os.path.join(ENV, "KayKit_Prototype_Bits", "Assets", "gltf")
args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
OUT_BLEND = os.path.abspath(args[0]) if args else os.path.join(ENV, "level_8.blend")
OUT_PREVIEW = os.path.abspath(args[1]) if len(args) > 1 else None

random.seed(81)

# Oyundaki yerleşim (rise_crouch_game.dart ve stage_camera.dart ile aynı).
ROW_SIZE, SPACING, PLAYER_SLOT = 6, 1.45, 3
LEADER_Y = 7.0
CAMERA_POS = Vector(((PLAYER_SLOT - (ROW_SIZE - 1) / 2) * SPACING, -6.5, 4.0))
CAMERA_TARGET = Vector((0, 7.0, 1.8))
CAMERA_FOV_Y = 70.0

BELT_Y = 10.5  # üretim bandı
WALL_Y = 16.0  # arka duvar
BEAM_Z = 7.6  # tavan kirişlerinin yüksekliği
GROUND = "#5E6266"

BOXES = ["Box_A", "Box_B", "Box_C"]
BARRELS = ["Barrel_A", "Barrel_B", "Barrel_C"]


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


def place(name, zone, x, y, scale=1.0, angle=None, z=0.0):
    """Bağlı bir kopya koyar; [angle] derece."""
    obj = model(name).copy()  # mesh verisi paylaşılır
    obj.location = (x, y, z)
    obj.rotation_mode = "XYZ"  # glTF içe aktarma kuaterniyona geçirir; açı yoksa uygulanmaz
    obj.rotation_euler = (0, 0, math.radians(random.uniform(-6, 6) if angle is None else angle))
    obj.scale = (scale,) * 3
    zones[zone].objects.link(obj)
    return obj


# Zemin: fabrika karoları (üst yüzleri zemin hizasında).
for ix in range(-4, 5):
    for iy in range(-2, 5):
        place("Floor", "Yakin", ix * 4.0, iy * 4.0 + 1.0, angle=0, z=-0.49)

# Üretim bandı: uzun masalar yan yana, üstlerinde aralıklı koliler.
for i in range(-3, 4):
    x = i * 3.0
    place("table_medium_long", "Yakin", x, BELT_Y, angle=0)
    for dx in (-0.9, 0.6):
        if random.random() < 0.75:
            place(random.choice(BOXES), "Yakin", x + dx + random.uniform(-0.2, 0.2), BELT_Y, z=1.0)
# Bandın iki ucunda büyük makineler (üstlerinde küçük blok).
for side in (-1, 1):
    place("Cube_Prototype_Large_A", "Yakin", side * 12.5, BELT_Y + 0.5, angle=0)
    place("Cube_Prototype_Small", "Yakin", side * 12.5, BELT_Y + 0.5, angle=0, z=4.0)
# Salonu bölen sütunlar; variller kapıların (x ±6,5; y 7) dışında.
for side in (-1, 1):
    place("Pillar_B", "Yakin", side * 4.8, 8.4, angle=0)
    place(random.choice(BARRELS), "Yakin", side * 9.0, 8.0)
    place(random.choice(BARRELS), "Yakin", side * 9.7, 8.9)
    place(random.choice(BARRELS), "Yakin", side * 9.3, 8.4, z=1.0)
# Yanlarda koli dolu paletler.
for side in (-1, 1):
    for y in (1.0, 4.5):
        place(random.choice(["Pallet_Small_Decorated_A", "Pallet_Small_Decorated_B"]), "Yakin",
              side * 9.8, y, angle=random.choice((0, 90)))

# Orta: bandın arkasında makine sırası, koli yığınları, merdiven.
for x in (-7.0, 7.0):
    place("Cube_Prototype_Large_B", "Orta", x, 13.5, angle=0)
place("Pallet_Small_Decorated_B", "Orta", -2.5, 13.6, angle=0)
place("Pallet_Small_Decorated_A", "Orta", 2.5, 13.4, angle=90)
place("Primitive_Stairs", "Orta", 11.5, 13.8, angle=180)
# Tavan kirişleri: bandın üstünde X boyunca iki sıra.
for y in (12.2, WALL_Y - 0.6):
    for i in range(-4, 5):
        place("Primitive_Beam", "Orta", i * 4.0, y, angle=0, z=BEAM_Z)

# Arka duvar: ortada yükleme kapısı; iki kat.
WALL = {0: "Wall_Doorway", 1: "Wall_Window_Closed", 2: "Wall_Decorated", 3: "Wall"}
for i in range(-4, 5):
    place(WALL[min(abs(i), 3)], "Orta", i * 4.0, WALL_Y, angle=0)
    place("Wall_Window_Closed" if i % 2 else "Wall", "Orta", i * 4.0, WALL_Y, angle=0, z=4.0)
place("Door_A_Decorated", "Orta", -0.8, WALL_Y - 0.1, angle=0)
# Yan duvarlar.
for side in (-1, 1):
    for iy in range(-1, 4):
        place("Wall_Window_Closed" if iy % 2 else "Wall", "Uzak", side * 18.0, iy * 4.0, angle=90)


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

# Soğuk beyaz tavan ışığı.
lamp = bpy.data.objects.new("Lamba", bpy.data.lights.new("Lamba", "SUN"))
lamp.data.energy = 3.0
lamp.data.color = (0.9, 0.95, 1.0)
lamp.location = (4, -8, 12)
lamp.rotation_euler = (Vector((0, 0, 0)) - lamp.location).to_track_quat("-Z", "Y").to_euler()
guides.objects.link(lamp)

scene.world = bpy.data.worlds.new("Gokyuzu")
scene.world.color = srgb("#1C1E22")[:3]

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
