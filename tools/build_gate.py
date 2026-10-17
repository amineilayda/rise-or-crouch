"""Yanan oyuncuların içine girip kaybolduğu kapıyı hazırlar: gövde ve iki kanat.

"Gate Tower" (Artbake Graphics, CC-BY-4.0; tools/source_models/props/gate_tower)
modelini içe aktarır, kemerli geçidin ortası (taş gövdenin merkezi) orijine
gelecek, tabanı yere oturacak şekilde taşır ve [SCALE] ile küçültür. Kapı +Y'ye
bakar; oyunda (glTF'te) bu -Z olur.

- Renkler canlandırılır: gri taş sıcak kum rengine, çatı kiremit kırmızısına,
  ahşap ve demir kuşaklar daha sıcak tonlara boyanır (dokular .blend'e gömülür).
- Geçidin arka ağzı düz siyah bir duvarla kapatılır (arkadaki sahne görünmesin).
- Modelde 90° dışa açık duran iki kanat gövdeden ayrılır, kapalı konuma
  döndürülür ve her biri menteşesi orijinde olacak şekilde ayrı kaydedilir;
  oyun kanatları menteşeleri etrafında döndürüp açar (rise_crouch_game.dart).
  Menteşelerin oyundaki (glTF) yerleri sonda yazdırılır: GATE_HINGE ...

Üç dosya kaydeder (gate.blend, gate_door_left.blend, gate_door_right.blend);
her biri tools/export_scene.py ile assets/models/props/ altına aktarılır:
  blender --background --factory-startup --python tools/build_gate.py
  for p in gate gate_door_left gate_door_right; do
    blender --background --factory-startup --python tools/export_scene.py -- \\
        tools/source_models/props/$p.blend assets/models/props/$p.glb
  done
"""
import math
import os

import bmesh
import bpy
import numpy as np
from mathutils import Matrix, Vector

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROPS = os.path.join(ROOT, "tools", "source_models", "props")
SRC = os.path.join(PROPS, "gate_tower", "scene.gltf")

# Kemer karakterlerden biraz yüksek olsun (kemer ~1,6 m, kule ~3,7 m).
SCALE = 0.45

# Dokuların yeni tonları: parlaklık korunur, renk bununla çarpılır.
TINTS = {
    "smlstone_baseColor": (1.45, 1.22, 0.92),  # sıcak kum taşı
    "gray_baseColor": (1.40, 1.18, 0.90),  # geçidin içi
    "schingle_baseColor": (1.75, 0.62, 0.42),  # kiremit kırmızısı çatı
    "brown_baseColor": (1.35, 0.80, 0.45),  # çatı kenarı ve kuşaklar
    "wood_baseColor": (1.40, 0.92, 0.55),  # sıcak ahşap
}

# Kanatlar: modelde menteşeden +Y'ye (dışa) uzanıyorlar. Taban (x) aralıkları
# kanadın kalınlığını, y aralığı uzunluğunu kapsar.
DOOR_Y = (2.2, 3.85)
DOORS = {"left": (-1.65, -1.38), "right": (1.28, 1.55)}


def tint_textures():
    for img in list(bpy.data.images):
        key = os.path.splitext(img.name)[0]
        if key not in TINTS or not img.size[0]:
            continue
        px = np.array(img.pixels[:], dtype=np.float32).reshape(-1, 4)
        lum = px[:, :3] @ np.array([0.3, 0.59, 0.11], dtype=np.float32)
        px[:, :3] = np.clip(lum[:, None] * np.array(TINTS[key], dtype=np.float32), 0, 1)
        # Taş dokuları gri tonlamalı PNG; üstüne yazınca renk kaybolur. Boyanmış
        # hâl yeni bir RGBA dokuya yazılıp eskisinin yerine konur.
        width, height = img.size
        tinted = bpy.data.images.new(key + "_canli", width, height, alpha=True)
        tinted.pixels = px.ravel()
        tinted.file_format = "PNG"
        tinted.pack()  # .blend'e gömülsün
        img.user_remap(tinted)
        print("TINTED", img.name, np.round(px[:, :3].mean(0), 2))


def loose_parts(obj):
    """[obj]'nin bağlı parçalarının köşe indeks kümeleri."""
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bm.verts.ensure_lookup_table()
    seen, parts = set(), []
    for v in bm.verts:
        if v.index in seen:
            continue
        stack, comp = [v], set()
        while stack:
            a = stack.pop()
            if a.index in seen:
                continue
            seen.add(a.index)
            comp.add(a.index)
            stack.extend(e.other_vert(a) for e in a.link_edges)
        parts.append(comp)
    bm.free()
    return parts


def split_off(obj, indices, name):
    """[indices] köşelerini (ve yüzlerini) [obj]'den ayırıp yeni nesne yapar."""
    bpy.ops.object.select_all(action="DESELECT")
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="DESELECT")
    bpy.ops.object.mode_set(mode="OBJECT")
    for i in indices:
        obj.data.vertices[i].select = True
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.separate(type="SELECTED")
    bpy.ops.object.mode_set(mode="OBJECT")
    new = [o for o in bpy.context.selected_objects if o is not obj][0]
    new.name = name
    return new


bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=SRC)
meshes = [o for o in bpy.data.objects if o.type == "MESH"]
for mesh in meshes:
    mesh.data.transform(mesh.matrix_world)
for obj in [o for o in bpy.data.objects if o.type != "MESH"]:
    bpy.data.objects.remove(obj)
for mesh in meshes:
    mesh.parent = None
    mesh.matrix_world.identity()
tint_textures()

# --- Kanatları ayır (ahşap düzlemler ve üstlerindeki demir kuşaklar) ---
doors = {}
for side, (x0, x1) in DOORS.items():
    pieces = []
    # Her ayırmada köşe indeksleri değişir: parçalar her nesne için yeniden bulunur.
    for mesh in list(meshes):
        indices = set()
        for comp in loose_parts(mesh):
            cos = [mesh.data.vertices[i].co for i in comp]
            if all(x0 <= c.x <= x1 and DOOR_Y[0] <= c.y <= DOOR_Y[1] for c in cos):
                indices |= comp
        if indices:
            pieces.append(split_off(mesh, indices, f"Kanat_{side}"))
    bpy.ops.object.select_all(action="DESELECT")
    for p in pieces:
        p.select_set(True)
    bpy.context.view_layer.objects.active = pieces[0]
    if len(pieces) > 1:
        bpy.ops.object.join()
    doors[side] = bpy.context.view_layer.objects.active
    print("DOOR", side, len(pieces), "parça")

# --- Geçidin arka ağzına düz siyah duvar: kapıdan bakınca arkadaki sahne
# görünmesin. Kemerden geniş ve yüksek; taşan kısmı duvarların içinde kalır.
# Yananlar kulenin ortasında kaybolduğu için yollarını kesmez. ---
back_y = min(v.co.y for m in meshes if m.data.materials and m.data.materials[0].name == "gray"
             for v in m.data.vertices) + 0.15
back = bpy.data.meshes.new("ArkaDuvar")
back.from_pydata(
    [(-1.7, back_y, 0), (1.6, back_y, 0), (1.6, back_y, 3.8), (-1.7, back_y, 3.8)], [], [(0, 1, 2, 3)])
black = bpy.data.materials.new("siyah")
black.use_nodes = True
black.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.01, 0.01, 0.01, 1)
black.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 1.0
back.materials.append(black)
back_obj = bpy.data.objects.new("ArkaDuvar", back)
bpy.context.scene.collection.objects.link(back_obj)

# --- Merkez: taş gövdenin (smlstone) ortası, taban yerde; ölçek ---
stone = next(m for m in meshes if m.data.materials and m.data.materials[0].name == "smlstone")
pts = [v.co for v in stone.data.vertices]
center = Vector(((min(p.x for p in pts) + max(p.x for p in pts)) / 2,
                 (min(p.y for p in pts) + max(p.y for p in pts)) / 2,
                 min(p.z for p in pts)))
move = Matrix.Scale(SCALE, 4) @ Matrix.Translation(-center)
body = [m for m in bpy.data.objects if m.type == "MESH" and m not in doors.values()]
for mesh in body + list(doors.values()):
    mesh.data.transform(move)

# --- Kanatlar: menteşe orijine, kapalı konuma (kemerin ortasına kadar) ---
hinges = {}
for side, door in doors.items():
    vs = [v.co for v in door.data.vertices]
    hinge = Vector(((min(v.x for v in vs) + max(v.x for v in vs)) / 2, min(v.y for v in vs), 0))
    hinges[side] = hinge
mid_x = (hinges["left"].x + hinges["right"].x) / 2
for side, door in doors.items():
    hinge = hinges[side]
    length = max(v.co.y for v in door.data.vertices) - hinge.y
    # Kanatlar ortada birleşsin ama üst üste binmesin (aynı düzlemde titreşmesin).
    reach = abs(mid_x - hinge.x) - 0.01
    angle = -math.pi / 2 if side == "left" else math.pi / 2  # +Y → içe doğru
    door.data.transform(
        Matrix.Rotation(angle, 4, "Z")
        @ Matrix.Diagonal((1, reach / length, 1, 1))
        @ Matrix.Translation(-hinge))
    # Oyunda (glTF: x, z, -y) menteşenin yeri.
    print(f"GATE_HINGE {side} x={hinge.x:.3f} z={-hinge.y:.3f}")


def save(objects, name):
    """[objects] dışındaki her şeyi siler, "Yakin" koleksiyonuna koyup kaydeder."""
    yakin = bpy.data.collections.get("Yakin") or bpy.data.collections.new("Yakin")
    if yakin.name not in bpy.context.scene.collection.children:
        bpy.context.scene.collection.children.link(yakin)
    for obj in list(bpy.data.objects):
        for col in list(obj.users_collection):
            col.objects.unlink(obj)
        if obj in objects:
            yakin.objects.link(obj)
    path = os.path.join(PROPS, name + ".blend")
    bpy.ops.wm.save_as_mainfile(filepath=path)
    print("SAVED", path)


all_pts = [v.co for m in body for v in m.data.vertices]
print("SIZE", [round(max(p[i] for p in all_pts) - min(p[i] for p in all_pts), 2) for i in range(3)])
save(body, "gate")
save([doors["left"]], "gate_door_left")
save([doors["right"]], "gate_door_right")
