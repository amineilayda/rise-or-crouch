"""KayKit Dungeon Pack ile 2. bölümün zindan taht salonunu (level_2.blend) kurar.

Rastgele serpiştirme yerine 4 m'lik modüler ızgaraya oturan, tasarlanmış bir
salon: iki katlı duvarlar ve tavan, oyun kurucunun arkasından başlayan iki sıra
sancaklı sütun, arka duvarda meşalelerle çevrili büyük kapı, köşelerde fıçı ve
sandık yığınları, yan duvarlarda masa, hazine sandığı ve kılıç-kalkanlar.

Kullanım:
  blender --background --factory-startup --python tools/build_dungeon.py -- <çıktı.blend> [önizleme.png]

Koordinatlar build_scene.py ile aynı: sıra y=0'da, oyun kurucu y=7'de, kamera
y=-6.5'te +Y'ye bakıyor. Parçaların süslü ön yüzü -Y'dedir.
"""
import math
import os
import sys

import bpy
from mathutils import Vector

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PACK = os.path.join(ROOT, "tools", "source_models", "environment",
                    "KayKit_Dungeon_Pack_1.1_FREE", "Assets", "gltf")
args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
OUT_BLEND = os.path.abspath(args[0]) if args else os.path.join(ROOT, "tools", "source_models", "environment", "level_2.blend")
OUT_PREVIEW = os.path.abspath(args[1]) if len(args) > 1 else None

ROW_SIZE, SPACING, PLAYER_SLOT = 6, 1.45, 3
LEADER_Y = 7.0
CAMERA_POS = Vector(((PLAYER_SLOT - (ROW_SIZE - 1) / 2) * SPACING, -6.5, 4.0))
CAMERA_TARGET = Vector((0, 7.0, 1.8))

# Salon ölçüleri (4 m ızgara).
TILE = 4.0
HALF_WIDTH = 10.0          # iç duvar yüzü x = ±10
BACK_Y = 32.0              # arka duvarın iç yüzü
FRONT_Y = -8.0             # zemin/tavanın kameranın arkasındaki ucu
WALL_HEIGHT = 4.0
LEVELS = 2                 # iki katlı duvar, tavan 8 m'de
GRID_X = [-8.0, -4.0, 0.0, 4.0, 8.0]
GRID_Y = [FRONT_Y + TILE / 2 + TILE * i for i in range(int((BACK_Y - FRONT_Y) / TILE))]


def srgb(hex_color):
    c = [int(hex_color[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    return (*[v ** 2.2 for v in c], 1.0)


def collection(name):
    col = bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(col)
    return col


bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
source = collection("_Kaynak")
guides = collection("_Rehber")
# export_scene.py bu üç koleksiyonu aktarır.
zones = {name: collection(name) for name in ("Yakin", "Orta", "Uzak")}
bpy.context.view_layer.layer_collection.children["_Kaynak"].exclude = True

_prototypes = {}


def prototype(name):
    if name in _prototypes:
        return _prototypes[name]
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=os.path.join(PACK, name + ".gltf"))
    new = [o for o in bpy.data.objects if o not in before]
    new_names = [o.name for o in new]
    meshes = [o for o in new if o.type == "MESH"]
    for obj in meshes:
        world = obj.matrix_world.copy()
        obj.parent = None
        obj.matrix_world = world
    # Birden çok parçalı modelleri (ör. sandık + kapağı) tek nesneye birleştir.
    # (Seçilebilmeleri için henüz gizli koleksiyona taşınmadan.)
    if len(meshes) > 1:
        bpy.ops.object.select_all(action="DESELECT")
        for obj in meshes:
            obj.select_set(True)
        bpy.context.view_layer.objects.active = meshes[0]
        bpy.ops.object.join()
    proto = meshes[0]
    for obj_name in new_names:
        obj = bpy.data.objects.get(obj_name)
        if obj is None:
            continue  # birleştirmede silindi
        if obj is proto:
            for col in obj.users_collection:
                col.objects.unlink(obj)
            source.objects.link(obj)
        else:
            bpy.data.objects.remove(obj)
    proto.location = (0, 0, 0)
    proto.rotation_euler = (0, 0, 0)
    _prototypes[name] = proto
    return proto


def place(name, zone, x, y, z=0.0, rot=0.0, scale=1.0):
    """[rot] derece: 0 = ön yüz kameraya (-Y), 90 = +X'e, -90 = -X'e, 180 = +Y'ye."""
    obj = prototype(name).copy()
    obj.location = (x, y, z)
    obj.rotation_euler = (0, 0, math.radians(rot))
    obj.scale = (scale, scale, scale)
    zones[zone].objects.link(obj)
    return obj


# --- Zemin ve tavan ---
for x in GRID_X:
    for y in GRID_Y:
        place("floor_tile_large", "Yakin", x, y)
        place("ceiling_tile", "Uzak", x, y, z=WALL_HEIGHT * LEVELS)

# --- Yan duvarlar: alt kat kemer/pencere ritmi, üst kat pencereli ---
LOWER = ["wall", "wall_window_closed", "wall_arched", "wall"]
UPPER = ["wall_window_closed", "wall"]
for side, rot in ((-1, 90), (1, -90)):
    x = side * (HALF_WIDTH + 0.5)
    for k, y in enumerate(GRID_Y):
        place(LOWER[k % len(LOWER)], "Uzak", x, y, 0, rot)
        place(UPPER[k % len(UPPER)], "Uzak", x, y, WALL_HEIGHT, rot)
    for level in range(LEVELS):  # arka köşeler
        place("pillar", "Uzak", x, BACK_Y + 0.5, WALL_HEIGHT * level)

# --- Arka duvar: ortada büyük kapı, yanlarında kemerler ---
back_lower = {-8: "wall", -4: "wall_arched", 0: "wall_doorway", 4: "wall_arched", 8: "wall"}
back_upper = {-8: "wall", -4: "wall_window_closed", 0: "wall", 4: "wall_window_closed", 8: "wall"}
for x in GRID_X:
    place(back_lower[int(x)], "Uzak", x, BACK_Y + 0.5, 0)
    place(back_upper[int(x)], "Uzak", x, BACK_Y + 0.5, WALL_HEIGHT)
# Kapının üstünde kalkanlı büyük sancak, köşelerde üçlü sancaklar.
place("banner_shield_red", "Orta", 0, BACK_Y + 0.32, WALL_HEIGHT)
for x in (-8, 8):
    place("banner_triple_red", "Orta", x, BACK_Y + 0.35, WALL_HEIGHT)
# Kapıyı çevreleyen meşaleler.
for x in (-2.5, 2.5):
    place("torch_mounted", "Orta", x, BACK_Y, 2.4)

# --- İki sıra sütun (oyun kurucunun arkasından başlar; yürüyen yananların
# yolunu kesmesin diye) ve üst katta sancaklar ---
PILLAR_X = 5.0
for i, y in enumerate((11.0, 19.0, 27.0)):
    for side in (-1, 1):
        x = side * PILLAR_X
        place("pillar_decorated", "Orta", x, y, 0)
        place("pillar", "Orta", x, y, WALL_HEIGHT)
        place("banner_patternA_red" if i % 2 == 0 else "banner_red", "Orta", x, y - 0.37, WALL_HEIGHT)

# --- Yan duvar süsleri: meşaleler sütun aralarında, kılıç-kalkan, raf ---
for side, rot in ((-1, 90), (1, -90)):
    wall_x = side * HALF_WIDTH
    for y in (7.0, 15.0, 23.0):
        place("torch_mounted", "Orta", wall_x, y, 2.4, rot)
place("sword_shield", "Orta", -HALF_WIDTH, 11.0, 2.6, 90)
place("sword_shield_gold", "Orta", HALF_WIDTH, 19.0, 2.6, -90)
place("shelf_small_candles", "Orta", -HALF_WIDTH, 27.0, 2.0, 90)
place("shelf_small_candles", "Orta", HALF_WIDTH, 27.0, 2.0, -90)

# --- Eşyalar: gruplar halinde, duvarlara ve köşelere yaslı ---
# Arka sol köşe: sandık ve fıçı yığını.
place("box_stacked", "Orta", -8.2, 29.6, rot=-12)
place("crates_stacked", "Orta", -5.8, 30.6, rot=20)
place("barrel_small_stack", "Orta", -8.6, 26.2, rot=90)
# Arka sağ köşe: büyük fıçılar ve şarap fıçısı.
place("keg_decorated", "Orta", 7.8, 30.4, rot=180)
place("barrel_large", "Orta", 8.8, 27.0)
place("barrel_large", "Orta", 5.9, 30.8, scale=0.8)
# Sol duvar ortası: uzun ziyafet masası ve sandalyeler.
place("table_long_decorated_A", "Orta", -8.3, 17.0, rot=0)
for y in (15.6, 18.4):
    place("chair", "Orta", -6.9, y, rot=-90)
# Sağ duvar ortası: hazine sandığı ve altın yığınları.
place("chest_gold", "Orta", 8.6, 17.0, rot=-90)
place("coin_stack_large", "Orta", 8.2, 19.4, rot=30)
place("coin_stack_medium", "Orta", 8.9, 14.9, rot=-20)
# Ön tarafta yıkıntı ve birkaç fıçı (kenarlarda, görüşü kapatmadan).
place("rubble_large", "Yakin", -9.2, 3.0, rot=90, scale=0.8)
place("barrel_large", "Yakin", 9.0, 3.5, scale=0.9)
place("crates_stacked", "Yakin", 8.7, 0.8, rot=-15)
# Oyun kurucunun iki yanında mumlar.
for x in (-2.4, 2.4):
    place("candle_triple", "Yakin", x, LEADER_Y + 1.5, scale=1.4)


# --- Rehber: karakter yer tutucuları, kamera, ışık ---
def box(name, center, size, hex_color):
    bpy.ops.mesh.primitive_cube_add(location=center)
    obj = bpy.context.active_object
    obj.name = name
    obj.scale = (size[0] / 2, size[1] / 2, size[2] / 2)
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = srgb(hex_color)
    obj.data.materials.append(mat)
    for col in obj.users_collection:
        col.objects.unlink(obj)
    guides.objects.link(obj)


for i in range(ROW_SIZE):
    x = (i - (ROW_SIZE - 1) / 2) * SPACING
    box("Oyuncu" if i == PLAYER_SLOT else f"Kisi_{i + 1}", (x, 0, 0.65), (0.8, 0.6, 1.3),
        "#3B6FD8" if i == PLAYER_SLOT else "#9AA5B1")
box("OyunKurucu", (0, LEADER_Y, 1.1), (1.2, 0.9, 2.2), "#D84B3B")

cam = bpy.data.objects.new("OyunKamerasi", bpy.data.cameras.new("OyunKamerasi"))
cam.data.sensor_fit = "VERTICAL"
cam.data.angle_y = math.radians(70)
cam.data.clip_end = 500
cam.location = CAMERA_POS
cam.rotation_euler = (CAMERA_TARGET - CAMERA_POS).to_track_quat("-Z", "Y").to_euler()
guides.objects.link(cam)
scene.camera = cam
scene.render.resolution_x, scene.render.resolution_y = 1080, 2340
scene.render.resolution_percentage = 50
scene.world = bpy.data.worlds.new("Karanlik")
scene.world.color = srgb("#14110F")[:3]

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
