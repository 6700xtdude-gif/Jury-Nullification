"""
Cartoon Sound FX & Tavern Ambience Synthesizer for Big Brown Bear
Generates a stereo 44.1kHz WAV track (assets/cartoon_sfx_bed.wav, 64.51s)
synced to the exact video cut timestamps, mixed subtly underneath the untouched
master voice recording (Recording (6).m4a).
"""

import math
import wave
from pathlib import Path
import numpy as np

BASE_DIR = Path(__file__).resolve().parent
OUT_WAV = BASE_DIR / "assets" / "cartoon_sfx_bed.wav"
SR = 44100
TOTAL_SEC = 64.51


def env_ad(n: int, atk_frac: float = 0.08, dec_pow: float = 2.0) -> np.ndarray:
    t = np.linspace(0.0, 1.0, max(1, n), endpoint=False)
    atk = np.clip(t / max(1e-4, atk_frac), 0.0, 1.0)
    dec = np.clip((1.0 - t) / max(1e-4, 1.0 - atk_frac), 0.0, 1.0) ** dec_pow
    return atk * dec


def add_clip(buf: np.ndarray, start_sec: float, sig: np.ndarray, pan: float = 0.0) -> None:
    """Mix mono signal into stereo buffer at start_sec with pan in [-1..+1]."""
    i0 = int(round(start_sec * SR))
    if i0 >= len(buf) or len(sig) == 0:
        return
    i1 = min(len(buf), i0 + len(sig))
    seg = sig[: i1 - i0]
    lg = math.cos((pan + 1.0) * math.pi / 4.0)
    rg = math.sin((pan + 1.0) * math.pi / 4.0)
    buf[i0:i1, 0] += seg * lg
    buf[i0:i1, 1] += seg * rg


def build_sfx_bed() -> Path:
    n_total = int(round(TOTAL_SEC * SR))
    buf = np.zeros((n_total, 2), dtype=np.float32)
    rng = np.random.default_rng(6700)

    # 1. Shot 1A (3.00s - 5.64s): WIENER TUESDAY'S neon hum + sputter + 3 heavy bear footsteps
    dur_1a = 2.64
    n1 = int(dur_1a * SR)
    t1 = np.arange(n1) / SR
    neon_hum = (
        0.35 * np.sin(2 * np.pi * 60 * t1)
        + 0.45 * np.sin(2 * np.pi * 120 * t1)
        + 0.25 * np.sin(2 * np.pi * 180 * t1)
        + 0.12 * np.sin(2 * np.pi * 300 * t1)
    )
    # Ballast sputter crackles around t=0.75s and t=1.95s
    crackle = np.zeros_like(t1)
    for c_t in (0.76, 1.94):
        win = np.exp(-((t1 - c_t) / 0.045) ** 2)
        crackle += win * rng.normal(0, 0.85, size=n1) * (np.sin(2 * np.pi * 900 * t1) > 0)
    add_clip(buf, 3.00, (neon_hum * 0.055 + crackle * 0.07) * np.hanning(n1), pan=0.12)

    # 3 heavy muffled footsteps approaching doorway (3.40s, 4.25s, 5.05s)
    for st_t, pn in [(3.40, -0.2), (4.25, -0.1), (5.05, 0.0)]:
        ns = int(0.22 * SR)
        ts = np.arange(ns) / SR
        f_sweep = 95.0 * np.exp(-ts * 12.0) + 38.0
        thud = np.sin(2 * np.pi * np.cumsum(f_sweep) / SR) * env_ad(ns, 0.04, 2.6)
        grit = rng.normal(0, 0.22, size=ns) * env_ad(ns, 0.02, 4.0)
        add_clip(buf, st_t, (thud + grit) * 0.14, pan=pn)

    # 2. S1 Cut Inside (5.64s): Saloon batwing door creak/swing whoosh
    nd = int(0.38 * SR)
    td = np.arange(nd) / SR
    creak_f = 310 + 95 * np.sin(2 * np.pi * 6.5 * td)
    creak = (0.6 * np.sin(2 * np.pi * np.cumsum(creak_f) / SR) + 0.3 * np.sin(4 * np.pi * np.cumsum(creak_f) / SR))
    whoosh = rng.normal(0, 0.35, size=nd) * env_ad(nd, 0.15, 2.2)
    add_clip(buf, 5.64, (creak * 0.045 + whoosh * 0.06) * env_ad(nd, 0.10, 2.0), pan=-0.35)

    # 3. S2 / S4 Subtle glass-rag squeak/clink (11.15s & 22.45s)
    for gt in (11.15, 22.45):
        ng = int(0.14 * SR)
        tg = np.arange(ng) / SR
        clink = (np.sin(2 * np.pi * 2480 * tg) + 0.5 * np.sin(2 * np.pi * 3710 * tg)) * env_ad(ng, 0.02, 3.8)
        add_clip(buf, gt, clink * 0.035, pan=0.35)

    # 4. S5_5A Brawl Toss (26.85s - 29.05s): Cartoon hits, wood crash & glass clatter
    for ht, freq0, pn in [(27.05, 155, -0.3), (27.55, 130, 0.25), (28.10, 175, -0.15), (28.62, 118, 0.3)]:
        nh = int(0.28 * SR)
        th = np.arange(nh) / SR
        pow_f = freq0 * np.exp(-th * 9.5) + 42.0
        punch = np.sin(2 * np.pi * np.cumsum(pow_f) / SR) * env_ad(nh, 0.02, 2.4)
        crash = rng.normal(0, 0.5, size=nh) * env_ad(nh, 0.03, 3.0)
        add_clip(buf, ht, (punch * 0.14 + crash * 0.065), pan=pn)

    # 5. S5_5C_GROWL (30.42s - 31.78s): Low guttural cartoon bear growl rumble
    ngrw = int(1.30 * SR)
    tgrw = np.arange(ngrw) / SR
    fm = 92.0 + 18.0 * np.sin(2 * np.pi * 26.0 * tgrw) - 14.0 * tgrw
    growl = (
        0.65 * np.sin(2 * np.pi * np.cumsum(fm) / SR)
        + 0.35 * np.tanh(2.5 * np.sin(2 * np.pi * np.cumsum(fm * 1.5) / SR))
    ) * env_ad(ngrw, 0.18, 1.5)
    add_clip(buf, 30.42, growl * 0.085, pan=-0.1)

    # 6. S5_5D_LADY (31.85s - 33.80s):
    #    - 32.27s..32.95s: Playful rosy blush sparkling harp/celesta glissando!
    #    - 33.05s..33.74s: Grandiose faint descending cartoon slide-whistle!
    harp_notes = [523.25, 659.25, 783.99, 987.77, 1174.66, 1318.51, 1567.98]  # Cmaj9 sparkle!
    for idx, hz in enumerate(harp_notes):
        nn = int(0.32 * SR)
        tn = np.arange(nn) / SR
        bell = (np.sin(2 * np.pi * hz * tn) + 0.35 * np.sin(2 * np.pi * hz * 2.0 * tn)) * env_ad(nn, 0.02, 2.8)
        add_clip(buf, 32.27 + idx * 0.075, bell * 0.055, pan=0.15 + 0.04 * idx)

    nsw = int(0.68 * SR)
    tsw = np.arange(nsw) / SR
    sw_f = 1040.0 * ((320.0 / 1040.0) ** (tsw / 0.68)) + 18.0 * np.sin(2 * np.pi * 11.0 * tsw)
    whistle = np.sin(2 * np.pi * np.cumsum(sw_f) / SR) * env_ad(nsw, 0.08, 1.6)
    add_clip(buf, 33.05, whistle * 0.065, pan=0.2)

    # 7. S5_5E_GULP (33.80s - 35.45s): Big rubbery cartoon GULP + X-ray belly bloop!
    nglp = int(0.42 * SR)
    tglp = np.arange(nglp) / SR
    gulp_f = 190.0 + 390.0 * np.sin(np.pi * (tglp / 0.42)) ** 1.6
    gulp = (
        0.75 * np.sin(2 * np.pi * np.cumsum(gulp_f) / SR)
        + 0.25 * np.sin(4 * np.pi * np.cumsum(gulp_f) / SR)
    ) * env_ad(nglp, 0.14, 1.8)
    add_clip(buf, 34.05, gulp * 0.13, pan=-0.15)

    nblp = int(0.18 * SR)
    tblp = np.arange(nblp) / SR
    blp_f = 260.0 + 340.0 * (tblp / 0.18)
    bloop = np.sin(2 * np.pi * np.cumsum(blp_f) / SR) * env_ad(nblp, 0.08, 2.2)
    add_clip(buf, 34.78, bloop * 0.075, pan=-0.1)

    # 8. S5_5F_STOOL (35.45s - 36.75s): Sputtering OKLAHOMA neon + decelerating spinning stool squeaks
    ns5f = int(1.28 * SR)
    t5f = np.arange(ns5f) / SR
    ok_hum = (0.4 * np.sin(2 * np.pi * 120 * t5f) + 0.25 * np.sin(2 * np.pi * 240 * t5f)) * 0.045
    add_clip(buf, 35.45, ok_hum * np.hanning(ns5f), pan=0.05)
    for sq_t, sq_hz in [(35.52, 1420), (35.76, 1360), (36.06, 1290), (36.42, 1210)]:
        nsq = int(0.09 * SR)
        tsq = np.arange(nsq) / SR
        sq = np.sin(2 * np.pi * (sq_hz + 80 * np.sin(2 * np.pi * 18 * tsq)) * tsq) * env_ad(nsq, 0.15, 2.0)
        add_clip(buf, sq_t, sq * 0.032, pan=0.4)

    # 9. S7 Single Bartender Hand-Slam on Bartop (41.66s = 41.16s + 0.50s)
    nslm = int(0.24 * SR)
    tslm = np.arange(nslm) / SR
    slm_f = 185.0 * np.exp(-tslm * 14.0) + 48.0
    slam = (
        0.75 * np.sin(2 * np.pi * np.cumsum(slm_f) / SR)
        + 0.45 * rng.normal(0, 0.45, size=nslm) * env_ad(nslm, 0.01, 4.5)
    ) * env_ad(nslm, 0.015, 2.5)
    add_clip(buf, 41.66, slam * 0.15, pan=0.25)

    # 10. S9_9B Bear Spiral-Eyes Warble (59.35s) + Heavy Floorboard Faint THUD (60.08s)!
    nwrb = int(0.65 * SR)
    twrb = np.arange(nwrb) / SR
    wrb_f = 480.0 - 160.0 * (twrb / 0.65) + 55.0 * np.sin(2 * np.pi * 14.0 * twrb)
    warble = np.sin(2 * np.pi * np.cumsum(wrb_f) / SR) * env_ad(nwrb, 0.12, 1.6)
    add_clip(buf, 59.35, warble * 0.055, pan=-0.25)

    nfnt = int(0.42 * SR)
    tfnt = np.arange(nfnt) / SR
    fnt_f = 115.0 * np.exp(-tfnt * 9.0) + 34.0
    faint_boom = (
        0.85 * np.sin(2 * np.pi * np.cumsum(fnt_f) / SR)
        + 0.35 * rng.normal(0, 0.4, size=nfnt) * env_ad(nfnt, 0.01, 3.8)
    ) * env_ad(nfnt, 0.015, 2.2)
    add_clip(buf, 60.08, faint_boom * 0.22, pan=-0.25)

    # Clamp & write 16-bit PCM stereo WAV
    OUT_WAV.parent.mkdir(parents=True, exist_ok=True)
    pcm16 = np.clip(buf * 32767.0, -32768, 32767).astype(np.int16)
    with wave.open(str(OUT_WAV), "wb") as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(SR)
        wf.writeframes(pcm16.tobytes())
    return OUT_WAV


if __name__ == "__main__":
    p = build_sfx_bed()
    print(f"[+] Built Cartoon SFX bed: {p} ({p.stat().st_size / 1024:.0f} KB)")
