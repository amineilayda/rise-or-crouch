"""4. bölümün korsan koyunu (level_4.blend) kurar.

Pirate Kit ile: oyun kurucunun arkasında hazine sandıkları, fıçılar, bombalar
ve altın yığınları; iki yanda palmiyeler; kumsalın bittiği yerde iskele ve
deniz; denizde demirli korsan gemisi, sandal, kayalık adacıklar ve sudan
yükselen bir ahtapot kolu. Gökyüzü ve ışıklar oyunda (levels.dart) ayarlanır.

Kullanım:
  blender --background --factory-startup --python tools/build_pirate.py -- <çıktı.blend> [önizleme.png]

Koordinatlar build_scene.py ile aynı: sıra y=0'da, oyun kurucu y=7'de, kamera
y=-6.5'te +Y'ye bakıyor.
"""
import math
import os
import random
import sys

import bpy
from mathutils import Vector

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV = os.path.join(ROOT, "tools", "source_models", "environment")
KIT = os.path.join(ENV, "Pirate_Kit")
args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
OUT_BLEND = os.path.abspath(args[0]) if args else os.path.join(ENV, "level_4.blend")
OUT_PREVIEW = os.path.abspath(args[1]) if len(args) > 1 else None

random.seed(4)

# Oyundaki yerleşim (rise_crouch_game.dart ve stage_camera.dart ile aynı).
ROW_SIZE, SPACING, PLAYER_SLOT = 6, 1.45, 3
LEADER_Y = 7.0
CAMERA_POS = Vector(((PLAYER_SLOT - (ROW_SIZE - 1) / 2) * SPACING, -6.5, 4.0))
CAMERA_TARGET = Vector((0, 7.0, 1.8))
CAMERA_FOV_Y = 70.0

SAND = "#E8D29A"
SEA = "#2C8FC2"
SHORE_Y = 20.0  # kumsalın bittiği, denizin başladığı çizgi
MAX_FACES = 2500  # bir modelin en fazla yüz sayısı (fazlası sadeleştirilir)


def srgb(hex_color):
    c = [int(hex_color[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    return (*[v ** 2.2 for v in c], 1.0)


def collection(name):
    col = bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(col)
    return col


def flat_material(name, hex_color, roughness=1.0):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = srgb(hex_color)
    bsdf.inputs["Roughness"].default_value = roughness
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
    """Modeli yükler (birden çok parçalıysa birleştirir), tabanını yere ve
    ortasını merkeze oturtur."""
    if name in _prototypes:
        return _prototypes[name]
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=os.path.join(KIT, name + ".glb"))
    new = [o for o in bpy.data.objects if o not in before]
    meshes = [o for o in new if o.type == "MESH"]
    for mesh in meshes:
        mesh.data.transform(mesh.matrix_world)
        mesh.modifiers.clear()
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
    mesh.vertex_groups.clear()
    # Çok detaylı modelleri (gemi, kayalıklar, palmiyeler) sadeleştir: çoğu
    # uzakta duruyor ve telefonda kare hızını düşürüyor.
    faces = len(mesh.data.polygons)
    if faces > MAX_FACES:
        bpy.context.scene.collection.objects.link(mesh)
        decimate = mesh.modifiers.new("Sadelestir", "DECIMATE")
        decimate.ratio = MAX_FACES / faces
        with bpy.context.temp_override(object=mesh, active_object=mesh):
            bpy.ops.object.modifier_apply(modifier=decimate.name)
        bpy.context.scene.collection.objects.unlink(mesh)
    verts = [v.co for v in mesh.data.vertices]
    lo = Vector([min(v[i] for v in verts) for i in range(3)])
    hi = Vector([max(v[i] for v in verts) for i in range(3)])
    offset = Vector(((lo.x + hi.x) / 2, (lo.y + hi.y) / 2, lo.z))
    for v in mesh.data.vertices:
        v.co -= offset
    mesh.data.update()
    # Boyu köşelerden ölç: dimensions bir sonraki güncellemeye kadar eski kalıyor.
    mesh["height"] = hi.z - lo.z
    source.objects.link(mesh)
    _prototypes[name] = mesh
    print(f"MODEL {name:<26} boy={mesh['height']:.2f}")
    return mesh


def place(name, zone, x, y, height, angle=None, sink=0.0):
    """[height] boyunda bir kopya koyar; [sink] kadar zemine/suya gömer."""
    proto = model(name)
    obj = proto.copy()  # mesh verisi paylaşılır
    obj.location = (x, y, -sink)
    obj.rotation_euler = (0, 0, random.uniform(0, 2 * math.pi) if angle is None else math.radians(angle))
    s = height / max(proto["height"], 0.01)
    obj.scale = (s, s, s)
    zones[zone].objects.link(obj)
    return obj


def scatter(zone, names, count, x_range, y_range, min_dist, height, keep_corridor=True):
    placed, tries = [], 0
    while len(placed) < count and tries < count * 200:
        tries += 1
        p = Vector((random.uniform(*x_range), random.uniform(*y_range)))
        if any((p - q).length < min_dist for q in placed):
            continue
        # Sıra ile oyun kurucu arasındaki koridor boş kalsın.
        if keep_corridor and -1.5 < p.y < LEADER_Y + 1.5 and abs(p.x) < 8:
            continue
        placed.append(p)
        place(random.choice(names), zone, p.x, p.y, random.uniform(*height))
    print(f"ZONE {zone}: {len(placed)}/{count}")


PALMS = ["Palm Tree", "Palm Tree-A6cKJYFsIb", "Palm Tree-P0tgwyXBgr"]
STONES = ["Rock", "Rock-4vHWF8XUBn", "Rock-6cytS1cPiL", "Rock-BvlfuHFAuI", "Rock-cg6yBEddtZ"]
CLIFFS = ["Rocks-38eDa0gjwZ", "Rocks-IFU6cm2Xow", "Rocks-fy3szRMvuE", "Rocks-e1rgb5i2kF"]
LOOT = ["Barrel", "Bomb", "Bucket", "Gold Bag", "Coins", "Wood"]

# Yakın: oyun kurucunun arkasında hazine (sahnenin "vitrini").
place("Chest Gold", "Yakin", -2.6, 9.6, 1.1, angle=-15)
place("Chest Closed", "Yakin", 2.9, 9.8, 0.9, angle=20)
place("Gold Bag", "Yakin", -1.5, 10.2, 0.6)
place("Coins", "Yakin", 1.6, 9.4, 0.35)
place("Coins", "Yakin", -3.6, 9.1, 0.3)
place("Bomb", "Yakin", 4.0, 10.6, 0.65)
place("Bomb", "Yakin", 4.5, 10.0, 0.5)
# Kenarlarda fıçı yığınları ve palmiyeler (çerçeve).
for x, y in ((-6.0, 10.5), (-6.8, 11.3), (-6.3, 12.0), (6.2, 11.0), (6.9, 11.8)):
    place("Barrel", "Yakin", x, y, random.uniform(0.85, 1.0))
place("Palm Tree", "Yakin", -8.0, 13.0, 7.5)
place("Palm Tree-A6cKJYFsIb", "Yakin", 8.5, 13.5, 6.5)
scatter("Yakin", STONES, 8, (-10, 10), (9.5, 16), 1.8, (0.4, 0.9))
scatter("Yakin", LOOT, 7, (-10, 10), (11, 17), 1.6, (0.4, 0.8))

# Orta: kumsalın sonunda iskele, palmiyeler ve kayalar.
for i, y in enumerate((SHORE_Y - 1.5, SHORE_Y + 1.1, SHORE_Y + 3.7)):
    place("Dock Broken" if i == 2 else "Dock", "Orta", 3.0, y, 3.0, angle=90)
place("Small Ship", "Orta", 6.2, SHORE_Y + 5.5, 1.8, angle=75, sink=0.4)
scatter("Orta", PALMS, 12, (-18, 18), (14, SHORE_Y), 3.0, (5.5, 8.0))
scatter("Orta", STONES, 6, (-18, 18), (14, SHORE_Y), 2.5, (0.6, 1.3))
place("Rocks-e1rgb5i2kF", "Orta", -13.0, SHORE_Y + 1.0, 2.6)
place("Rocks-38eDa0gjwZ", "Orta", 15.0, SHORE_Y + 2.0, 4.5)

# Uzak: denizde demirli gemi, ahtapot kolu ve kayalık adacıklar.
place("Ship", "Uzak", -9.0, 42.0, 13.0, angle=60, sink=1.2)
place("Tentacle", "Uzak", 13.0, 34.0, 8.0, angle=200, sink=1.0)
for x, y, h in ((22, 48, 7), (-30, 55, 9), (6, 64, 6), (-16, 70, 8), (34, 66, 10)):
    place(random.choice(CLIFFS), "Uzak", x, y, h, sink=0.8)
scatter("Uzak", PALMS, 10, (-40, 40), (48, 72), 6.0, (6.0, 9.0), keep_corridor=False)

# Deniz: kumsalın bittiği yerden ufka kadar düz su (oyuna aktarılır).
sea = bpy.data.objects.new("Deniz", bpy.data.meshes.new("Deniz"))
sea.data.from_pydata(
    [(-150, SHORE_Y, 0.03), (150, SHORE_Y, 0.03), (150, 160, 0.03), (-150, 160, 0.03)], [], [(0, 1, 2, 3)]
)
sea.data.materials.append(flat_material("Deniz", SEA, roughness=0.4))
zones["Uzak"].objects.link(sea)


# --- Rehber: zemin, karakter yer tutucuları, kamera, ışık ---
ground = bpy.data.objects.new("Zemin", bpy.data.meshes.new("Zemin"))
ground.data.from_pydata([(-100, -100, 0), (100, -100, 0), (100, 100, 0), (-100, 100, 0)], [], [(0, 1, 2, 3)])
ground.data.materials.append(flat_material("Zemin", SAND))
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
box("OyunKurucu", (0, LEADER_Y, 1.0), (1.2, 0.9, 2.0), "#A8302E")

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
sun.data.energy = 3.2
sun.data.color = (1.0, 0.92, 0.78)
sun.location = (8, -12, 14)
sun.rotation_euler = (Vector((0, 0, 0)) - sun.location).to_track_quat("-Z", "Y").to_euler()
guides.objects.link(sun)

scene.world = bpy.data.worlds.new("Gokyuzu")
scene.world.color = srgb("#7FC8F0")[:3]

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
