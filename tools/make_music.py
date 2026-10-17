"""Menü ve oyun için döngüye uygun, neşeli bir chiptune müziği üretir.

Dış kaynak yok: kare dalga melodi, üçgen dalga bas ve gürültü ritmi sentezlenir.
Döngünün başı ve sonu sessizlikten geçmeden birleşir (eşit uzunlukta ölçüler).

Kullanım:
  python tools/make_music.py [çıktı.wav]   (varsayılan: assets/audio/music.wav)
"""
import math
import random
import struct
import sys
import wave

RATE = 22050
BPM = 132
BEAT = 60 / BPM
STEP = BEAT / 2  # sekizlik nota

# C majör ilerleme: C - Am - F - G (her akor 1 ölçü = 8 sekizlik), iki tur.
CHORDS = [
    ("C", [60, 64, 67]),
    ("Am", [57, 60, 64]),
    ("F", [53, 57, 60]),
    ("G", [55, 59, 62]),
] * 2

# Melodi: ölçü başına 8 sekizlik; None = sus, sayı = MIDI nota.
MELODY = [
    [72, None, 76, 79, 76, None, 72, 74],
    [76, None, 72, None, 69, 72, 76, None],
    [77, None, 76, 74, 72, None, 69, 72],
    [74, None, 71, 74, 79, None, 77, 74],
    [72, 76, 79, 84, 79, 76, 72, 76],
    [69, 72, 76, 81, 76, 72, 69, 72],
    [77, 76, 74, 72, 74, None, 77, 81],
    [79, None, 74, None, 71, 74, 79, None],
]


def freq(midi):
    return 440.0 * 2 ** ((midi - 69) / 12)


def square(phase, duty=0.5):
    return 1.0 if (phase % 1.0) < duty else -1.0


def triangle(phase):
    p = phase % 1.0
    return 4 * p - 1 if p < 0.5 else 3 - 4 * p


def envelope(t, length, attack=0.005, release=0.04):
    if t < attack:
        return t / attack
    if t > length - release:
        return max(0.0, (length - t) / release)
    return 1.0


def main():
    out_path = sys.argv[1] if len(sys.argv) > 1 else "assets/audio/music.wav"
    steps = len(MELODY) * 8
    total = int(steps * STEP * RATE)
    buf = [0.0] * total
    rng = random.Random(7)
    step_len = int(STEP * RATE)

    for i in range(steps):
        bar, pos = divmod(i, 8)
        start = i * step_len
        root = CHORDS[bar][1][0]

        # Melodi (kare dalga, %25 duty: daha parlak).
        note = MELODY[bar][pos]
        if note is not None:
            f = freq(note)
            for n in range(step_len):
                t = n / RATE
                buf[start + n] += 0.16 * square(f * t, 0.25) * envelope(t, STEP) * (1 - 0.4 * t / STEP)

        # Bas (üçgen): kök ve oktav arasında zıplar.
        bass = root - 24 + (12 if pos % 2 else 0)
        f = freq(bass)
        for n in range(step_len):
            t = n / RATE
            buf[start + n] += 0.30 * triangle(f * t) * envelope(t, STEP, release=0.02)

        # Arpej (yumuşak kare): akor notaları sırayla, hızlı.
        chord = CHORDS[bar][1]
        arp_len = step_len // 2
        for half in range(2):
            f = freq(chord[(pos * 2 + half) % 3] + 12)
            for n in range(arp_len):
                t = n / RATE
                buf[start + half * arp_len + n] += 0.05 * square(f * t) * envelope(t, arp_len / RATE)

        # Ritim: 1 ve 3. vuruşta kick, 2 ve 4'te snare, her sekizlikte hi-hat.
        if pos in (0, 4):
            for n in range(min(step_len, int(0.12 * RATE))):
                t = n / RATE
                f = 120 * math.exp(-t * 30) + 45
                buf[start + n] += 0.45 * math.sin(2 * math.pi * f * t) * math.exp(-t * 25)
        if pos in (2, 6):
            for n in range(min(step_len, int(0.15 * RATE))):
                t = n / RATE
                buf[start + n] += 0.18 * (rng.random() * 2 - 1) * math.exp(-t * 28)
        for n in range(min(step_len, int(0.03 * RATE))):
            t = n / RATE
            buf[start + n] += 0.05 * (rng.random() * 2 - 1) * math.exp(-t * 120)

    peak = max(abs(x) for x in buf)
    scale = 0.85 / peak
    with wave.open(out_path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(RATE)
        w.writeframes(b"".join(struct.pack("<h", int(x * scale * 32767)) for x in buf))
    print(f"{out_path}: {total / RATE:.1f} sn")


if __name__ == "__main__":
    main()
