"""Portrelere benzeyen basit "chibi" karakterleri (büyük kafa, kısa gövde,
tişört, kot, ayakkabı) KayKit Rig_Medium iskeletine giydirerek üretir.

Her parça tek bir kemiğe tam ağırlıkla bağlanır; böylece
make_animations.py'nin bütün animasyonları bu karakterlerde de çalışır.
Her renk ayrı malzeme = flame_3d'de ayrı yüzey; bir yüzey en fazla 16 kemik
kullanabildiği için bu bölme sınırın altında kalmayı da garantiler.

Kullanım:
  blender --background --factory-startup --python tools/make_chibi.py -- <iskelet_kaynağı.glb> <karakter> <çıktı.glb>
  karakter: player1 .. player5 (assets/images/portraits/ ile aynı sıra) ya da me (oyuncu)
Çıktı daha sonra make_animations.py'den geçirilir.
"""
import math
import sys

import bmesh
import bpy
from mathutils import Matrix, Vector

rig_path, character, out_path = sys.argv[sys.argv.index("--") + 1:][:3]

# --- Karakterler (renkler sRGB; portrelerdeki belirgin özellikler) ---
JEANS = "#3B5B8C"
SHOES = "#222222"
CHARACTERS = {
    # Sarı küt saç, açık ten, beyaz tişört.
    "player1": dict(skin="#F2C9A8", hair="#E8C45A", shirt="#F2F2F2", hair_style="bob"),
    # Kısa koyu kahve saç, koyu tişört.
    "player2": dict(skin="#E8B994", hair="#3A281E", shirt="#34343C", hair_style="short"),
    # Gri saç, gözlük, koyu yeşil tişört.
    "player3": dict(skin="#EBC2A0", hair="#A9A9A9", shirt="#3F5C36", hair_style="short", glasses=True),
    # Uzun kızıl saç, koyu bordo üst.
    "player4": dict(skin="#F3CDB0", hair="#B3262C", shirt="#4A2A36", hair_style="long"),
    # Koyu ten, kıvırcık koyu saç, mor tişört.
    "player5": dict(skin="#8A5636", hair="#2B1C14", shirt="#7B5CB8", hair_style="curly"),
    # Oyuncunun kendisi: portresi yok, sade; menüdeki turuncuyla ayırt edilir.
    "me": dict(skin="#F0C6A2", hair="#5A3B26", shirt="#FF8F00", hair_style="short"),
}
spec = CHARACTERS[character]

bpy.ops.wm.read_factory_settings(use_empty=True)

# İskeleti KayKit karakterinden al, karakterin kendi parçalarını sil.
bpy.ops.import_scene.gltf(filepath=rig_path)
arm = next(o for o in bpy.data.objects if o.type == "ARMATURE")
for obj in [o for o in bpy.data.objects if o.type != "ARMATURE"]:
    bpy.data.objects.remove(obj)
bones = arm.data.bones


def bone_head(name):
    return arm.matrix_world @ bones[name].head_local


# --- Malzemeler ---
_materials = {}


def material(hex_color, name):
    """Mat malzeme. Blender rengi doğrusal tutar; glTF'e de doğrusal yazılır."""
    key = (hex_color, name)
    if key in _materials:
        return _materials[key]
    srgb = [int(hex_color[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    linear = [c ** 2.2 for c in srgb]
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (*linear, 1)
    bsdf.inputs["Roughness"].default_value = 1.0
    bsdf.inputs["Metallic"].default_value = 0.0
    _materials[key] = mat
    return mat


SKIN = material(spec["skin"], "skin")
HAIR = material(spec["hair"], "hair")
SHIRT = material(spec["shirt"], "shirt")
PANTS = material(JEANS, "jeans")
SHOE = material(SHOES, "shoes")
DARK = material("#1A1A1A", "dark")
LENS = material("#A9C8D8", "lens")

# --- Parça üretimi ---
parts = []  # (nesne, köşe konumu -> kemik adı)


def _finish(bm, name, mat, bone_for, smooth=True):
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    mesh.materials.append(mat)
    for poly in mesh.polygons:
        poly.use_smooth = smooth
    bone = bone_for if callable(bone_for) else (lambda co, b=bone_for: b)
    parts.append((obj, bone))
    return obj


def sphere(name, center, radii, mat, bone, segments=24, rings=16, keep=None):
    """Elipsoid. keep(co) verilirse yalnızca onu sağlayan köşeler kalır."""
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=segments, v_segments=rings, radius=1.0)
    bmesh.ops.transform(bm, matrix=Matrix.Diagonal((*radii, 1)), verts=bm.verts)
    bmesh.ops.translate(bm, vec=Vector(center), verts=bm.verts)
    if keep is not None:
        bmesh.ops.delete(bm, geom=[v for v in bm.verts if not keep(v.co)], context="VERTS")
    return _finish(bm, name, mat, bone)


def capsule_x(name, x0, x1, z, radius, mat, bone, y=0.0):
    """X ekseni boyunca uzanan, uçları yuvarlak silindir (kollar)."""
    length = x1 - x0
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=16, v_segments=12, radius=radius)
    # Küreyi ortadan uzat: ekvatorun bir yanındaki köşeleri kaydır.
    for v in bm.verts:
        v.co = Vector((v.co.z, v.co.y, -v.co.x))  # kutupları X eksenine döndür
        if v.co.x > 0:
            v.co.x += length - 2 * radius
        v.co += Vector((x0 + radius, y, z))
    return _finish(bm, name, mat, bone)


def capsule_z(name, x, y, z0, z1, radius, mat, bone):
    """Z ekseni boyunca dikey silindir (bacaklar)."""
    length = z1 - z0
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=16, v_segments=12, radius=radius)
    for v in bm.verts:
        if v.co.z > 0:
            v.co.z += length - 2 * radius
        v.co += Vector((x, y, z0 + radius))
    return _finish(bm, name, mat, bone)


def box(name, center, size, mat, bone):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.transform(bm, matrix=Matrix.Diagonal((*size, 1)), verts=bm.verts)
    bmesh.ops.translate(bm, vec=Vector(center), verts=bm.verts)
    return _finish(bm, name, mat, bone, smooth=False)


# --- Ölçüler (iskeletten) ---
head_z = bone_head("head").z          # boyun
shoulder_x = bone_head("upperarm.l").x
arm_z = bone_head("upperarm.l").z
elbow_x = bone_head("lowerarm.l").x
wrist_x = bone_head("wrist.l").x
hand_x = bone_head("hand.l").x
hip_z = bone_head("hips").z
leg_x = bone_head("upperleg.l").x
knee_z = bone_head("lowerleg.l").z
ankle_z = bone_head("foot.l").z
chest_z = bone_head("chest").z

HEAD_R = (0.46, 0.42, 0.44)
HEAD_C = Vector((0, 0, head_z + 0.38))


def head_surface_y(x, z, grow=1.0):
    """Kafa elipsoidinin ön yüzeyinin (−Y) y değeri."""
    rx, ry, rz = (r * grow for r in HEAD_R)
    k = 1 - (x / rx) ** 2 - ((z - HEAD_C.z) / rz) ** 2
    return -ry * math.sqrt(max(k, 0.0))


# Kafa ve yüz (karakter -Y yönüne bakıyor).
sphere("Head", HEAD_C, HEAD_R, SKIN, "head")
for side in (-1, 1):
    # Kulaklar (uzun / küt saç kapatıyor)
    if spec["hair_style"] in ("short", "curly"):
        sphere(f"Ear{side}", (side * 0.45, 0.0, HEAD_C.z - 0.02), (0.06, 0.07, 0.09), SKIN, "head", 12, 8)
    if not spec.get("glasses"):
        ex, ez = side * 0.14, HEAD_C.z - 0.01
        sphere(f"Eye{side}", (ex, head_surface_y(ex, ez) + 0.012, ez), (0.04, 0.02, 0.05), DARK, "head", 12, 8)
sphere("Nose", (0, head_surface_y(0, HEAD_C.z - 0.09) - 0.01, HEAD_C.z - 0.09), (0.05, 0.04, 0.045), SKIN, "head", 12, 8)

if spec.get("glasses"):
    gz = HEAD_C.z
    for side in (-1, 1):
        gx = side * 0.15
        gy = head_surface_y(gx, gz) - 0.02
        box(f"Frame{side}", (gx, gy, gz), (0.21, 0.03, 0.15), DARK, "head")
        box(f"Lens{side}", (gx, gy - 0.017, gz), (0.17, 0.01, 0.11), LENS, "head")
        # Sap: çerçeveden kulağa
        box(f"Arm{side}", (side * 0.33, gy * 0.5, gz + 0.04), (0.02, abs(gy), 0.02), DARK, "head")
    box("Bridge", (0, head_surface_y(0, gz) - 0.025, gz + 0.03), (0.1, 0.02, 0.025), DARK, "head")

# --- Saç ---
style = spec["hair_style"]
HAIR_GROW = 1.07
hair_r = tuple(r * HAIR_GROW for r in HEAD_R)


def cap(cut_front, cut_back, face_open=None):
    """Kafayı saran saç kepi: alın hizasında önde, ensede arkada kesilir.
    face_open verilirse (−1..0) yüzün önü dışında her yer cut_back'e kadar
    iner (yanlarda çeneye kadar küt saç)."""
    def keep(co):
        t = (co.y - HEAD_C.y) / hair_r[1]  # −1 ön, +1 arka
        if face_open is None:
            cut = cut_front + (cut_back - cut_front) * (t + 1) / 2
        else:
            k = min(max((t - face_open) / 0.25 + 0.5, 0.0), 1.0)
            cut = cut_front + (cut_back - cut_front) * k
        return co.z > cut
    return sphere("Hair", HEAD_C, hair_r, HAIR, "head", 64, 40, keep)


if style == "short":
    cap(HEAD_C.z + 0.17, HEAD_C.z - 0.12)
elif style == "bob":
    cap(HEAD_C.z + 0.16, HEAD_C.z - 0.30, face_open=-0.62)
elif style == "long":
    cap(HEAD_C.z + 0.16, HEAD_C.z - 0.40, face_open=-0.62)
    # Sırta dökülen saç (kafaya bağlı: kafa eğilince birlikte döner).
    sphere("Back", (0, 0.24, HEAD_C.z - 0.42), (0.42, 0.16, 0.40), HAIR, "head", 20, 14)
elif style == "curly":
    cap(HEAD_C.z + 0.12, HEAD_C.z - 0.16)
    # Kepin üstüne serpiştirilmiş bukleler
    for i in range(22):
        # Altın açı ile yarım küreye eşit dağılım
        a = i * 2.39996
        h = 0.15 + 0.85 * (i / 21)
        r = math.sqrt(1 - h * h)
        d = Vector((math.cos(a) * r, math.sin(a) * r, h))
        if d.y < -0.6 and d.z < 0.55:
            continue  # yüzü kapatmasın
        pos = HEAD_C + Vector((d.x * hair_r[0], d.y * hair_r[1], d.z * hair_r[2]))
        sphere(f"Curl{i}", pos, (0.12, 0.12, 0.12), HAIR, "head", 12, 8)

# --- Gövde ---
def torso_bone(co):
    return "chest" if co.z > chest_z else "spine"


sphere("Torso", (0, 0, (hip_z + head_z) / 2 + 0.05), (0.33, 0.25, (head_z - hip_z) / 2 + 0.08), SHIRT, torso_bone)


def arm_bone(side):
    def pick(co):
        x = abs(co.x)
        if x < elbow_x:
            return f"upperarm.{side}"
        if x < wrist_x:
            return f"lowerarm.{side}"
        return f"hand.{side}"
    return pick


for side, sgn in (("l", 1), ("r", -1)):
    # Kısa kollu tişört: kolluk, ardından ten rengi kol ve yumruk el.
    sleeve = capsule_x(f"Sleeve.{side}", shoulder_x - 0.06, shoulder_x + 0.2, arm_z, 0.125, SHIRT, f"upperarm.{side}")
    limb = capsule_x(f"Arm.{side}", shoulder_x + 0.1, hand_x, arm_z, 0.09, SKIN, arm_bone(side))
    hand = sphere(f"Hand.{side}", (hand_x + 0.04, 0, arm_z), (0.115, 0.115, 0.115), SKIN, f"hand.{side}", 16, 10)
    if sgn < 0:
        for obj in (sleeve, limb, hand):
            for v in obj.data.vertices:
                v.co.x = -v.co.x
            obj.data.flip_normals()

# --- Kot ve ayakkabılar ---
sphere("Pelvis", (0, 0, hip_z + 0.1), (0.31, 0.23, 0.17), PANTS, "hips")


def leg_bone(side):
    return lambda co: f"upperleg.{side}" if co.z > knee_z else f"lowerleg.{side}"


for side, sgn in (("l", 1), ("r", -1)):
    capsule_z(f"Leg.{side}", sgn * leg_x, 0, ankle_z - 0.02, hip_z + 0.12, 0.125, PANTS, leg_bone(side))
    sphere(f"Shoe.{side}", (sgn * leg_x, -0.05, 0.075), (0.14, 0.2, 0.09), SHOE, f"foot.{side}", 16, 10)

# --- Kemiklere bağla, tek parça yap ---
for obj, bone_for in parts:
    groups = {}
    for v in obj.data.vertices:
        name = bone_for(v.co)
        if name not in groups:
            groups[name] = obj.vertex_groups.get(name) or obj.vertex_groups.new(name=name)
        groups[name].add([v.index], 1.0, "REPLACE")

bpy.ops.object.select_all(action="DESELECT")
for obj, _ in parts:
    obj.select_set(True)
bpy.context.view_layer.objects.active = parts[0][0]
bpy.ops.object.join()
body = bpy.context.view_layer.objects.active
body.name = character
body.parent = arm
modifier = body.modifiers.new("Armature", "ARMATURE")
modifier.object = arm

bpy.ops.object.select_all(action="DESELECT")
arm.select_set(True)
body.select_set(True)
bpy.ops.export_scene.gltf(filepath=out_path, export_format="GLB", use_selection=True, export_animations=False)
print("EXPORTED", out_path, "köşe:", len(body.data.vertices), "malzeme:", [m.name for m in body.data.materials])
