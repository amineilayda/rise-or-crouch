"""KayKit Rig_Medium karakterlerine Rise or Crouch animasyonlarını ekler.

Kullanım:
  blender --background --factory-startup --python tools/make_animations.py -- <girdi.glb> <çıktı.glb>

Eklenen animasyonlar (30 FPS):
  Idle        ayakta bekleme (döngü)
  Crouch      ayaktan çömelmeye geçiş
  CrouchIdle  çömelmiş bekleme (döngü)
  StandUp     çömelmeden ayağa kalkış
  Fail        yanınca üzülme
  Cheer       sevinme, kollar havada (döngü)
"""
import math
import os
import sys

import bpy
import numpy as np
from mathutils import Quaternion, Vector

FPS = 30
X = Vector((1, 0, 0))
Y = Vector((0, 1, 0))

# Karakter -Y yönüne bakıyor. X ekseninde negatif dönüş bacağı öne,
# pozitif dönüş gövdeyi/başı öne eğer. Y ekseninde sol kol için pozitif aşağı.

src, dst = sys.argv[sys.argv.index("--") + 1:][:2]

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.context.scene.render.fps = FPS
bpy.ops.import_scene.gltf(filepath=src)

arm = next(o for o in bpy.data.objects if o.type == "ARMATURE")
bones = arm.data.bones
pbones = arm.pose.bones


def head(name):
    return bones[name].head_local


def apply_pose(p):
    for pb in pbones:
        rest = bones[pb.name].matrix_local.to_3x3()
        spec = p.get(pb.name, {})
        # Armatür eksenindeki dönüşü kemiğin kendi eksenine çevir.
        q = Quaternion()
        for axis, deg in spec.get("rot", []):
            q = Quaternion(axis, math.radians(deg)) @ q
        pb.rotation_mode = "QUATERNION"
        pb.rotation_quaternion = (rest.inverted() @ q.to_matrix() @ rest).to_quaternion()
        pb.location = rest.inverted() @ spec.get("loc", Vector())
        pb.scale = (1, 1, 1)


def legs_spec(drop, thigh, shin):
    """Kalça `drop` kadar iner; ayak bileği düz kalsın diye ayak ters döner."""
    p = {"hips": {"loc": Vector((0, 0, -drop))}}
    for side in ("l", "r"):
        p[f"upperleg.{side}"] = {"rot": [(X, thigh)]}
        p[f"lowerleg.{side}"] = {"rot": [(X, shin)]}
        p[f"foot.{side}"] = {"rot": [(X, -(thigh + shin))]}
    return p


_leg_cache = {}


def solve_legs(drop):
    """Kalça `drop` kadar inince ayak yerinde kalacak uyluk/baldır açılarını
    (derece) deneme-yanılma ile bulur. Pozitif baldır = diz öne bükülür."""
    if drop in _leg_cache:
        return _leg_cache[drop]
    target = head("foot.l").copy()

    def error(thigh, shin):
        apply_pose(legs_spec(drop, thigh, shin))
        bpy.context.view_layer.update()
        return (pbones["foot.l"].head - target).length

    thigh, shin = -drop * 250, drop * 500
    best = error(thigh, shin)
    step = 8.0
    while step > 0.02:
        for dt, ds in ((step, 0), (-step, 0), (0, step), (0, -step)):
            e = error(thigh + dt, shin + ds)
            if e < best:
                best, thigh, shin = e, thigh + dt, shin + ds
                break
        else:
            step /= 2
    print(f"LEGS drop={drop:.3f} thigh={thigh:.1f} shin={shin:.1f} foot_error={best * 100:.2f}cm")
    _leg_cache[drop] = (thigh, shin)
    return thigh, shin


def pose(hips_z=0.0, spine=0.0, chest=0.0, head_tilt=0.0, leg_drop=0.0,
         arm_down=70.0, arm_forward=0.0, elbow=10.0,
         thigh_l=0.0, thigh_r=0.0, knee_l=0.0, knee_r=0.0, swing=0.0):
    """Bir pozu kemik başına [(eksen, derece), ...] listesi olarak tanımlar.

    Yürüme için bacaklar ayrı ayrı: thigh_* pozitif = bacak öne, knee_* pozitif =
    diz bükülür; swing pozitif = sol kol öne, sağ kol geriye.
    """
    p = {
        "spine": {"rot": [(X, spine)]},
        "chest": {"rot": [(X, chest)]},
        "head": {"rot": [(X, head_tilt)]},
        "upperarm.l": {"rot": [(Y, arm_down), (X, -(arm_forward + swing))]},
        "upperarm.r": {"rot": [(Y, -arm_down), (X, -(arm_forward - swing))]},
        "lowerarm.l": {"rot": [(X, -elbow)]},
        "lowerarm.r": {"rot": [(X, -elbow)]},
    }
    if leg_drop > 0:
        p.update(legs_spec(leg_drop, *solve_legs(round(leg_drop, 4))))
    elif any((thigh_l, thigh_r, knee_l, knee_r)):
        for side, thigh, knee in (("l", thigh_l, knee_l), ("r", thigh_r, knee_r)):
            p[f"upperleg.{side}"] = {"rot": [(X, -thigh)]}
            p[f"lowerleg.{side}"] = {"rot": [(X, knee)]}
            # Ayak tabanı yere paralel kalsın.
            p[f"foot.{side}"] = {"rot": [(X, thigh - knee)]}
    p.setdefault("hips", {"loc": Vector()})
    p["hips"]["loc"] = p["hips"]["loc"] + Vector((0, 0, hips_z))
    return p


def blend(a, b, k):
    """İki poz parametresi sözlüğü arasında ara değer."""
    return {key: a.get(key, 0.0) + (b.get(key, 0.0) - a.get(key, 0.0)) * k for key in a.keys() | b.keys()}


# Not: kol yukarıdayken (arm_down < 0) "öne" dönüş negatif arm_forward'dır.
STAND = dict(arm_down=70.0, elbow=10.0)
STAND_BREATHE = dict(chest=4.0, head_tilt=-2.0, arm_down=64.0, elbow=14.0)
# Kalkarken küçük bir zıplama: kalça (ve ayaklar) 5 cm havalanır.
STAND_HOP = dict(hips_z=0.05, head_tilt=-6.0, arm_down=50.0, elbow=20.0)
CROUCH = dict(leg_drop=0.22, spine=26.0, head_tilt=-20.0, arm_down=66.0, arm_forward=62.0, elbow=30.0)
# Çömelirken biraz fazla inip yerine oturur (daha "tok" bir hareket).
CROUCH_DEEP = dict(leg_drop=0.25, spine=30.0, head_tilt=-22.0, arm_down=62.0, arm_forward=70.0, elbow=34.0)
CROUCH_BREATHE = dict(leg_drop=0.21, spine=28.0, head_tilt=-21.0, arm_down=66.0, arm_forward=65.0, elbow=33.0)
FAIL = dict(spine=10.0, chest=6.0, head_tilt=18.0, arm_down=82.0, elbow=5.0)
CHEER_A = dict(hips_z=0.03, arm_down=-35.0, arm_forward=-15.0, elbow=10.0, head_tilt=-10.0)
CHEER_B = dict(arm_down=-50.0, arm_forward=-15.0, elbow=25.0, head_tilt=-5.0)

# --- Oyun kurucunun hareketleri ---
# DEVE: dikleşip iki kolu havaya kaldırır. CÜCE: çömelip kollarıyla aşağı bastırır.
LEADER_IDLE = STAND
# Kollar geniş V: dik kalkınca KayKit'in büyük kafasının arkasında kayboluyor.
LEADER_DEVE = dict(hips_z=0.03, head_tilt=-8.0, arm_down=-48.0, arm_forward=-22.0, elbow=6.0)
LEADER_DEVE_HIGH = dict(hips_z=0.06, head_tilt=-12.0, arm_down=-56.0, arm_forward=-18.0, elbow=2.0)
LEADER_DEVE_PUMP = dict(hips_z=0.0, head_tilt=-4.0, arm_down=-25.0, arm_forward=-25.0, elbow=40.0)
LEADER_CUCE = dict(leg_drop=0.2, spine=24.0, head_tilt=-26.0, arm_down=58.0, arm_forward=72.0, elbow=6.0)
LEADER_CUCE_LOW = dict(leg_drop=0.24, spine=30.0, head_tilt=-28.0, arm_down=62.0, arm_forward=58.0, elbow=4.0)
LEADER_CUCE_PUMP = dict(leg_drop=0.14, spine=18.0, head_tilt=-22.0, arm_down=40.0, arm_forward=90.0, elbow=30.0)


def transition(a, b, frames, steps=4, start=0):
    """Ayağın her ara karede de yerinde kalması için geçişi birkaç ara pozla verir."""
    return [(start + round(frames * i / steps), blend(a, b, i / steps)) for i in range(steps + 1)]


def snap(a, overshoot, settle, frames=10):
    """a'dan overshoot'a hızlı git (karelerin %70'i), sonra settle'a otur."""
    hit = round(frames * 0.7)
    return transition(a, overshoot, hit) + transition(overshoot, settle, frames - hit, steps=2, start=hit)[1:]


def pump(a, middle, frames=12):
    """Aynı komut tekrar gelince: pozdan çıkıp geri dön (vurgulama)."""
    half = frames // 2
    return transition(a, middle, half, steps=3) + transition(middle, a, frames - half, steps=3, start=half)[1:]


LEADER_POSES = {"Idle": LEADER_IDLE, "Deve": LEADER_DEVE, "Cuce": LEADER_CUCE}
LEADER_TARGETS = {
    "Deve": (LEADER_DEVE_HIGH, LEADER_DEVE, LEADER_DEVE_PUMP),
    "Cuce": (LEADER_CUCE_LOW, LEADER_CUCE, LEADER_CUCE_PUMP),
}

# --- Yürüme (yanan oyuncu sıradan çıkarken): boynu bükük, 20 karelik döngü ---
_WALK_BODY = dict(spine=6.0, head_tilt=14.0, arm_down=74.0, elbow=12.0)
WALK_CONTACT_L = dict(_WALK_BODY, hips_z=-0.015, thigh_l=26.0, knee_l=4.0, thigh_r=-20.0, knee_r=18.0, swing=-22.0)
WALK_PASS_L = dict(_WALK_BODY, hips_z=0.02, thigh_l=0.0, knee_l=4.0, thigh_r=8.0, knee_r=55.0, swing=0.0)
WALK_CONTACT_R = dict(_WALK_BODY, hips_z=-0.015, thigh_r=26.0, knee_r=4.0, thigh_l=-20.0, knee_l=18.0, swing=22.0)
WALK_PASS_R = dict(_WALK_BODY, hips_z=0.02, thigh_r=0.0, knee_r=4.0, thigh_l=8.0, knee_l=55.0, swing=0.0)

ACTIONS = {
    "Idle": [(0, STAND), (30, STAND_BREATHE), (60, STAND)],
    "Walk": [(0, WALK_CONTACT_L), (5, WALK_PASS_L), (10, WALK_CONTACT_R), (15, WALK_PASS_R), (20, WALK_CONTACT_L)],
    "Crouch": snap(STAND, CROUCH_DEEP, CROUCH),
    "CrouchIdle": [(0, CROUCH), (30, CROUCH_BREATHE), (60, CROUCH)],
    "StandUp": snap(CROUCH, STAND_HOP, STAND),
    "Fail": [(0, STAND), (15, FAIL), (40, FAIL)],
    "Cheer": [(0, CHEER_B), (10, CHEER_A), (20, CHEER_B)],
}
# Oyun kurucu: her başlangıç pozundan her hedefe bir geçiş (L_<nereden>_<nereye>).
# Oyun bu animasyonu bir kez oynatıp son karede bekletir.
for source, source_pose in LEADER_POSES.items():
    for target, (overshoot, settle, middle) in LEADER_TARGETS.items():
        keys = pump(settle, middle) if source == target else snap(source_pose, overshoot, settle, frames=12)
        ACTIONS[f"L_{source}_{target}"] = keys
# Bacak açılarını animasyonlar oluşturulmadan önce çöz (sonrasında Blender
# pozu animasyondan yeniden hesaplar ve ölçüm bozulur).
ACTIONS = {name: [(f, pose(**params)) for f, params in keys] for name, keys in ACTIONS.items()}


arm.animation_data_create()
for name, keys in ACTIONS.items():
    action = bpy.data.actions.new(name)
    action.use_fake_user = True
    arm.animation_data.action = action
    for frame, p in keys:
        apply_pose(p)
        for pb in pbones:
            pb.keyframe_insert("location", frame=frame, group=pb.name)
            pb.keyframe_insert("rotation_quaternion", frame=frame, group=pb.name)
    track = arm.animation_data.nla_tracks.new()
    track.name = name
    track.strips.new(name, 0, action)
    arm.animation_data.action = None

# --- Dokuları doğrusal renk uzayına çevir ---
# flame_3d'nin shader'ı dokuyu olduğu gibi (doğrusal sanarak) okuyup sonuca
# gamma düzeltmesi uyguluyor; sRGB dokular bu yüzden soluk görünüyor. Pikselleri
# önceden doğrusala çevirince (renk^2.2) ekranda orijinal renkler çıkıyor.
for image in list(bpy.data.images):
    width, height = image.size
    if width == 0 or image.name.endswith("_linear"):
        continue
    pixels = np.array(image.pixels[:], dtype=np.float32).reshape(-1, 4)
    pixels[:, :3] = np.power(pixels[:, :3], 2.2)
    linear = bpy.data.images.new(image.name + "_linear", width, height, alpha=True)
    linear.pixels = pixels.ravel()
    linear.file_format = "PNG"
    image.user_remap(linear)
    print("LINEARIZED", image.name, f"{width}x{height}")

# --- Sadece karakteri dışa aktar (sahnedeki fazlalık nesneler hariç) ---
bpy.ops.object.select_all(action="DESELECT")
arm.select_set(True)
for child in arm.children_recursive:
    child.select_set(True)
bpy.context.view_layer.objects.active = arm
bpy.ops.export_scene.gltf(
    filepath=dst,
    export_format="GLB",
    use_selection=True,
    export_animations=True,
    export_animation_mode="ACTIONS",
)

# Blender bazen ardışık karelerde dönüşün işaretini çeviriyor; flame_3d bunu
# kaldıramıyor (bkz. fix_quaternions.py).
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fix_quaternions import fix_glb  # noqa: E402

print("QUATERNION_FLIPS_FIXED", fix_glb(dst))
print("EXPORTED", dst)
