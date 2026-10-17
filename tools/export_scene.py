"""Bir ortam sahnesini (ör. level_1.blend) oyun için .glb'ye aktarır.

Sadece "Yakin", "Orta" ve "Uzak" koleksiyonlarındaki nesneler aktarılır;
"_Rehber" (zemin, karakter kutuları, kamera) ve "_Kaynak" aktarılmaz.

flame_3d için yapılanlar:
  - Aynı dokuyu kullanan kopya malzemeler teke indirilir (daha az çizim çağrısı).
  - Nesneler birleştirilir; her parça 65.535 köşe sınırının altında kalır
    (flame_3d indeksleri 16 bit okuyor).
  - Dokular doğrusal renk uzayına çevrilir (karakterlerdeki gibi, yoksa soluk).

Kullanım:
  blender --background --factory-startup --python tools/export_scene.py -- <sahne.blend> <çıktı.glb>
"""
import json
import os
import struct
import sys

import bpy
import numpy as np

ZONES = ("Yakin", "Orta", "Uzak")
# Dışa aktarıcı köşeleri UV/normal sınırlarında çoğaltabildiği için pay bırakılır.
MAX_VERTS_PER_CHUNK = 20000
GLTF_VERTEX_LIMIT = 65535

src, dst = [os.path.abspath(p) for p in sys.argv[sys.argv.index("--") + 1:][:2]]
bpy.ops.wm.open_mainfile(filepath=src)


def base_name(name):
    return name.rsplit(".", 1)[0] if name[-4:-3] == "." and name[-3:].isdigit() else name


# --- Kopya dokuları ve malzemeleri teke indir ---
for collection in (bpy.data.images, bpy.data.materials):
    canonical = {}
    for item in list(collection):
        key = base_name(item.name)
        if key in canonical:
            item.user_remap(canonical[key])
        else:
            canonical[key] = item

# --- Aktarılacak nesnelerin bağımsız kopyaları (dönüşümler uygulanmış) ---
export_col = bpy.data.collections.new("_Disari")
bpy.context.scene.collection.children.link(export_col)
objects = []
for zone in ZONES:
    col = bpy.data.collections.get(zone)
    if col is None:
        continue
    for obj in col.all_objects:
        if obj.type != "MESH":
            continue
        copy = obj.copy()
        copy.data = obj.data.copy()
        copy.parent = None
        copy.matrix_world = obj.matrix_world.copy()
        export_col.objects.link(copy)
        objects.append(copy)

bpy.ops.object.select_all(action="DESELECT")
for obj in objects:
    obj.select_set(True)
bpy.context.view_layer.objects.active = objects[0]
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

# --- Yakın nesneler bir arada kalsın diye konuma göre sırala ve gruplara böl ---
objects.sort(key=lambda o: (round(o.matrix_world.translation.y / 10), o.matrix_world.translation.x))
chunks, current, count = [], [], 0
for obj in objects:
    n = len(obj.data.vertices)
    if current and count + n > MAX_VERTS_PER_CHUNK:
        chunks.append(current)
        current, count = [], 0
    current.append(obj)
    count += n
if current:
    chunks.append(current)

joined = []
for i, chunk in enumerate(chunks):
    bpy.ops.object.select_all(action="DESELECT")
    for obj in chunk:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = chunk[0]
    if len(chunk) > 1:
        bpy.ops.object.join()
    result = bpy.context.view_layer.objects.active
    result.name = f"Ortam_{i + 1}"
    joined.append(result)
    print(f"CHUNK {result.name}: {len(chunk)} nesne, {len(result.data.vertices)} köşe")

# --- Dokuları doğrusal renk uzayına çevir ---
for image in list(bpy.data.images):
    width, height = image.size
    if width == 0 or not image.users:
        continue
    pixels = np.array(image.pixels[:], dtype=np.float32).reshape(-1, 4)
    pixels[:, :3] = np.power(pixels[:, :3], 2.2)
    linear = bpy.data.images.new(image.name + "_linear", width, height, alpha=True)
    linear.pixels = pixels.ravel()
    linear.file_format = "PNG"
    image.user_remap(linear)
    print("LINEARIZED", image.name, f"{width}x{height}")

# --- Dışa aktar ---
bpy.ops.object.select_all(action="DESELECT")
for obj in joined:
    obj.select_set(True)
os.makedirs(os.path.dirname(dst), exist_ok=True)
bpy.ops.export_scene.gltf(
    filepath=dst,
    export_format="GLB",
    use_selection=True,
    export_animations=False,
)

# --- Kontrol: hiçbir parça flame_3d'nin köşe sınırını aşmamalı ---
data = open(dst, "rb").read()
gltf = json.loads(data[20:20 + struct.unpack_from("<I", data, 12)[0]])
primitives = [p for m in gltf["meshes"] for p in m["primitives"]]
vertex_counts = [gltf["accessors"][p["attributes"]["POSITION"]]["count"] for p in primitives]
triangles = sum(gltf["accessors"][p["indices"]]["count"] // 3 for p in primitives)
print(f"CHECK parça={len(primitives)} malzeme={len(gltf.get('materials', []))} "
      f"en_büyük_parça={max(vertex_counts)} köşe, toplam={triangles} üçgen, "
      f"dosya={len(data) // 1024} KB")
if max(vertex_counts) > GLTF_VERTEX_LIMIT:
    raise SystemExit(f"HATA: bir parça {GLTF_VERTEX_LIMIT} köşeyi aşıyor; MAX_VERTS_PER_CHUNK'ı küçült.")
print("EXPORTED", dst)
