"""Bir .glb dosyasındaki dönüş animasyonlarında işaret sıçramalarını düzeltir.

q ve -q aynı dönüştür. Blender'ın glTF dışa aktarıcısı bazen ardışık iki
karede işareti değiştiriyor. flame_3d ise böyle iki kare arasında ara değer
hesaplarken NaN üretip hata fırlatıyor; hata 3D çizimi kalıcı olarak bozuyor.
Bu araç her karenin işaretini bir öncekiyle aynı yöne çevirir (dot >= 0).

Kullanım:
  python tools/fix_quaternions.py <dosya.glb> [--check]
"""
import json
import struct
import sys

FLOAT = 5126


def _parse(data):
    json_len = struct.unpack_from("<I", data, 12)[0]
    gltf = json.loads(data[20:20 + json_len])
    bin_start = 20 + json_len + 8
    return gltf, bin_start


def _rotation_outputs(gltf):
    for anim in gltf.get("animations", []):
        for ch in anim["channels"]:
            if ch["target"]["path"] == "rotation":
                yield anim["name"], anim["samplers"][ch["sampler"]]["output"]


def fix_glb(path, check_only=False):
    """İşaret sıçramalarını düzeltir; bulunan sıçrama sayısını döndürür."""
    data = bytearray(open(path, "rb").read())
    gltf, bin_start = _parse(data)
    flips = 0
    for _, accessor_index in _rotation_outputs(gltf):
        acc = gltf["accessors"][accessor_index]
        assert acc["componentType"] == FLOAT and acc["type"] == "VEC4"
        view = gltf["bufferViews"][acc["bufferView"]]
        base = bin_start + view.get("byteOffset", 0) + acc.get("byteOffset", 0)
        stride = view.get("byteStride", 16)
        prev = None
        for i in range(acc["count"]):
            offset = base + i * stride
            q = struct.unpack_from("<4f", data, offset)
            if prev is not None and sum(a * b for a, b in zip(prev, q)) < 0:
                flips += 1
                q = tuple(-c for c in q)
                if not check_only:
                    struct.pack_into("<4f", data, offset, *q)
            prev = q
    if not check_only and flips:
        open(path, "wb").write(data)
    return flips


if __name__ == "__main__":
    target = sys.argv[1]
    check = "--check" in sys.argv
    count = fix_glb(target, check_only=check)
    print(f"{target}: {count} işaret sıçraması {'bulundu' if check else 'düzeltildi'}")
