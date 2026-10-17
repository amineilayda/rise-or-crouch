"""3. bölümün karlı kristal vadisini (level_3.blend) kurar.

Crystal Pack'teki kristaller, KayKit Forest Nature Pack'in karla kaplanmış
(dokusu beyaza çekilmiş) ağaç ve kayaları ve alçak kar yığınları. Gökyüzü,
kar yağışı ve ışıklar oyunda (levels.dart) ayarlanır.

Kullanım:
  blender --background --factory-startup --python tools/build_snow.py -- <çıktı.blend> [önizleme.png]

Koordinatlar build_scene.py ile aynı: sıra y=0'da, oyun kurucu y=7'de, kamera
y=-6.5'te +Y'ye bakıyor.
"""
import math
import os
import random
import sys

import bpy
import numpy as np
from mathutils import Vector

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV = os.path.join(ROOT, "tools", "source_models", "environment")
CRYSTALS = os.path.join(ENV, "Crystal_Pack")
FOREST = os.path.join(ENV, "KayKit_Forest_Nature_Pack", "KayKit_Forest_Nature_Pack_1.0_FREE", "Assets", "gltf")
args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
OUT_BLEND = os.path.abspath(args[0]) if args else os.path.join(ENV, "level_3.blend")
OUT_PREVIEW = os.path.abspath(args[1]) if len(args) > 1 else None

random.seed(11)

# Oyundaki yerleşim (rise_crouch_game.dart ve stage_camera.dart ile aynı).
ROW_SIZE, SPACING, PLAYER_SLOT = 6, 1.45, 3
LEADER_Y = 7.0
CAMERA_POS = Vector(((PLAYER_SLOT - (ROW_SIZE - 1) / 2) * SPACING, -6.5, 4.0))
CAMERA_TARGET = Vector((0, 7.0, 1.8))
CAMERA_FOV_Y = 70.0

SNOW = "#EEF4FA"
# Ağaç ve kayaların dokusu bu renge bu oranda çekilir (karla kaplı görünüm).
FROST_COLOR = np.array([0.93, 0.96, 1.0], dtype=np.float32)
FROST_AMOUNT = 0.72


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


# --- Karla kaplı malzemeler ---
_frosted = {}


def frosted(mat):
    """Malzemenin, dokusu beyaza çekilmiş kopyası (export_scene kopyaları teke
    indirirken karışmasın diye adları farklı)."""
    if mat.name in _frosted:
        return _frosted[mat.name]
    copy = mat.copy()
    copy.name = "Karli_" + mat.name.split(".")[0]
    for node in copy.node_tree.nodes:
        if node.type == "TEX_IMAGE" and node.image is not None:
            name = "karli_" + node.image.name.split(".")[0]
            image = bpy.data.images.get(name)
            if image is None:
                src = node.image
                w, h = src.size
                pixels = np.array(src.pixels[:], dtype=np.float32).reshape(-1, 4)
                pixels[:, :3] = pixels[:, :3] * (1 - FROST_AMOUNT) + FROST_COLOR * FROST_AMOUNT
                image = bpy.data.images.new(name, w, h, alpha=True)
                image.pixels = pixels.ravel()
                image.file_format = "PNG"
                image.pack()  # .blend'e gömülsün (export_scene ayrı açıyor)
            node.image = image
    _frosted[mat.name] = copy
    return copy


# --- Modelleri birer kez yükle ---
_prototypes = {}


def prototype(path, frost=False):
    """Modeli yükler, tabanını yere ve ortasını merkeze oturtur."""
    if path in _prototypes:
        return _prototypes[path]
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    new = [o for o in bpy.data.objects if o not in before]
    mesh = next(o for o in new if o.type == "MESH")
    world = mesh.matrix_world.copy()
    for obj in new:
        for col in obj.users_collection:
            col.objects.unlink(obj)
        if obj is not mesh:
            bpy.data.objects.remove(obj)
    mesh.parent = None
    mesh.data.transform(world)
    mesh.matrix_world.identity()
    verts = [v.co for v in mesh.data.vertices]
    lo = Vector([min(v[i] for v in verts) for i in range(3)])
    hi = Vector([max(v[i] for v in verts) for i in range(3)])
    offset = Vector(((lo.x + hi.x) / 2, (lo.y + hi.y) / 2, lo.z))
    for v in mesh.data.vertices:
        v.co -= offset
    mesh.data.update()
    # Boyu köşelerden ölç: dimensions bir sonraki güncellemeye kadar eski kalıyor.
    mesh["height"] = hi.z - lo.z
    if frost:
        for i, mat in enumerate(mesh.data.materials):
            mesh.data.materials[i] = frosted(mat)
    source.objects.link(mesh)
    _prototypes[path] = mesh
    print(f"MODEL {os.path.basename(path):<28} boy={mesh['height']:.2f}")
    return mesh


def crystal(name):
    return prototype(os.path.join(CRYSTALS, name + ".glb"))


def nature(name):
    return prototype(os.path.join(FOREST, name + ".gltf"), frost=True)


def place(proto, zone, x, y, height, tilt=0.0):
    obj = proto.copy()  # mesh verisi paylaşılır
    obj.location = (x, y, 0)
    obj.rotation_euler = (random.uniform(-tilt, tilt), random.uniform(-tilt, tilt), random.uniform(0, 2 * math.pi))
    s = height / max(proto["height"], 0.01)
    obj.scale = (s, s, s)
    zones[zone].objects.link(obj)
    return obj


def scatter(zone, protos, count, x_range, y_range, min_dist, height, tilt=0.0, keep_corridor=True):
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
        place(random.choice(protos), zone, p.x, p.y, random.uniform(*height), tilt)
    print(f"ZONE {zone}: {len(placed)}/{count}")


# Kristal grupları: kümeler, tek parçalar, alçak döküntüler, büyük kütleler.
CLUSTERS = [crystal(n) for n in ("Crystal-3saqXqoOti", "Crystal-Wj8Qjq38T8", "Crystal-WzWPKHFMkL",
                                 "Crystal-dxCmHfpqc5", "Crystal-oNWj2mo2vS", "Crystal-N0yUOaSuL9")]
SHARDS = [crystal(n) for n in ("Crystal-SbLlgMXrQ1", "Crystal-fvPiJt42Q1", "Crystal")]
RUBBLE = [crystal(n) for n in ("Crystal-tEF4oKBc3A", "Crystal-ySa8IekR6i")]
MASSIVE = [crystal(n) for n in ("Crystal-H4cOcCir1M", "Crystal-N0yUOaSuL9", "Crystal-WzWPKHFMkL")]
# Yalnızca çam ağaçları (yapraklı ağaçlar karlı vadiye uymuyor).
TREES = [nature(n) for n in ("Tree_3_A_Color1", "Tree_3_B_Color1", "Tree_3_C_Color1",
                             "Tree_4_A_Color1", "Tree_4_B_Color1", "Tree_4_C_Color1")]
ROCKS = [nature(n) for n in ("Rock_1_A_Color1", "Rock_2_A_Color1", "Rock_3_A_Color1", "Rock_3_F_Color1")]

# Kar yığınları: yarısı gömülü basık küreler.
SNOW_MAT = flat_material("KarYigini", SNOW)


def drift(zone, x, y, radius, height):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=20, ring_count=10, location=(x, y, 0))
    obj = bpy.context.active_object
    obj.scale = (radius, radius * random.uniform(0.7, 1.2), height)
    obj.rotation_euler = (0, 0, random.uniform(0, math.pi))
    obj.data.materials.append(SNOW_MAT)
    bpy.ops.object.shade_smooth()
    for col in obj.users_collection:
        col.objects.unlink(obj)
    zones[zone].objects.link(obj)


# Yakın: oyun kurucunun arkasında iki yanda kristal kümeleri (çerçeve),
# kenarlarda tek kristaller, döküntüler ve kar yığınları.
place(CLUSTERS[0], "Yakin", -5.2, 11.5, 3.6)
place(CLUSTERS[3], "Yakin", 5.6, 12.0, 3.2)
place(SHARDS[2], "Yakin", -3.0, 13.0, 4.2, 0.12)
place(SHARDS[0], "Yakin", 3.4, 13.5, 3.0, 0.12)
scatter("Yakin", SHARDS, 8, (-9, 9), (9.5, 15), 1.8, (1.0, 2.2), tilt=0.25)
scatter("Yakin", RUBBLE, 6, (-9, 9), (9.5, 15), 2.2, (0.4, 0.8))
scatter("Yakin", ROCKS, 5, (-9, 9), (9.5, 15), 2.0, (0.4, 0.9))
for _ in range(14):
    x, y = random.uniform(-10, 10), random.uniform(1.5, 15)
    if abs(x) < 8 and -1.5 < y < LEADER_Y + 1.5:
        x = math.copysign(random.uniform(8.5, 11), x)  # koridoru boş bırak
    drift("Yakin", x, y, random.uniform(0.8, 1.8), random.uniform(0.25, 0.5))

# Orta: karlı çam ağaçları arasında kristal kümeleri.
scatter("Orta", TREES, 16, (-15, 15), (15, 30), 3.2, (4.5, 7.0))
scatter("Orta", CLUSTERS, 9, (-15, 15), (15, 30), 3.0, (2.0, 4.5))
scatter("Orta", ROCKS, 6, (-15, 15), (15, 30), 3.0, (0.8, 1.6))

# Uzak: dev kristal kütleleri ve karlı orman duvarı.
scatter("Uzak", MASSIVE, 9, (-34, 34), (34, 70), 9.0, (8.0, 15.0))
scatter("Uzak", TREES, 45, (-32, 32), (32, 70), 3.6, (6.5, 10.0))
for _ in range(10):
    drift("Uzak", random.uniform(-40, 40), random.uniform(35, 75), random.uniform(5, 10), random.uniform(1.5, 3.5))


# --- Rehber: zemin, karakter yer tutucuları, kamera, ışık ---
ground = bpy.data.objects.new("Zemin", bpy.data.meshes.new("Zemin"))
ground.data.from_pydata([(-100, -100, 0), (100, -100, 0), (100, 100, 0), (-100, 100, 0)], [], [(0, 1, 2, 3)])
ground.data.materials.append(flat_material("Zemin", SNOW))
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
box("OyunKurucu", (0, LEADER_Y, 1.0), (1.2, 0.9, 2.0), "#8FB3D9")

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

# Soğuk, yumuşak güneş.
sun = bpy.data.objects.new("Gunes", bpy.data.lights.new("Gunes", "SUN"))
sun.data.energy = 2.6
sun.data.color = (0.9, 0.95, 1.0)
sun.location = (8, -12, 14)
sun.rotation_euler = (Vector((0, 0, 0)) - sun.location).to_track_quat("-Z", "Y").to_euler()
guides.objects.link(sun)

scene.world = bpy.data.worlds.new("Gokyuzu")
scene.world.color = srgb("#C9D9E8")[:3]

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
