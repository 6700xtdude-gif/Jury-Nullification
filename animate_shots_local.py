"""
Local 2D Cartoon Animator for Big Brown Bear (No Cloud Key Required)

Generates animated 1280x720 @ 24fps MP4 clips (and preview GIFs) from local concept art:
1. Shot 1A (assets/0-Wiener_Tuesdays_exterior_local.mp4):
   - Cyan 'WIENER TUESDAY'S' neon voltage hum + occasional ballast sputter
   - Independent blinking orange neon hot dog icon
   - Warm streetlamp glow pulse + orbiting animated night moths
   - Heavy lumbering bear-step camera bob + push-in toward the open doorway
2. Shot 5C (assets/5C-Oklahoma_neon_stool_local.mp4):
   - Pink 'OKLAHOMA' neon sign hum + erratic flickering on the dying 'MA' tubes
   - Extracted white feather sprite swaying left-to-right and drifting down onto the stool
   - Spinning red bar stool highlight sweep + decelerating cartoon ink motion arcs
   - Content bear belly hiccup + slow breathing cycle
"""

import math
import subprocess
from pathlib import Path
import imageio_ffmpeg  # type: ignore
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

BASE_DIR = Path(__file__).resolve().parent
ASSETS = BASE_DIR / "assets"
FPS = 24
DURATION = 4.0
N_FRAMES = int(FPS * DURATION)


def encode_mp4_and_gif(frames: list[Image.Image], mp4_out: Path, gif_out: Path | None = None) -> None:
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    tmp_dir = BASE_DIR / "_animatic_build" / mp4_out.stem
    tmp_dir.mkdir(parents=True, exist_ok=True)
    for old in tmp_dir.glob("f_*.png"):
        old.unlink()
    for idx, im in enumerate(frames):
        im.save(tmp_dir / f"f_{idx:04d}.png")

    cmd = [
        ff, "-y", "-framerate", str(FPS), "-i", str(tmp_dir / "f_%04d.png"),
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p",
        str(mp4_out),
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        raise RuntimeError(f"FFmpeg encode failed for {mp4_out.name}:\n{res.stderr[-600:]}")

    if gif_out is not None:
        # 12fps 640x360 crisp looping preview GIF
        sub = [f.resize((640, 360), Image.Resampling.LANCZOS) for f in frames[::2]]
        sub[0].save(
            gif_out, save_all=True, append_images=sub[1:], duration=int(1000 / 12), loop=0, optimize=False
        )


def build_shot_1a() -> list[Image.Image]:
    base = Image.open(ASSETS / "exterior_wiener_tuesdays.png").convert("RGB")
    arr0 = np.array(base, dtype=np.float32)
    H, W, _ = arr0.shape

    # Precompute masks for cyan text neon, orange hotdog neon, and streetlamp halo
    yy, xx = np.mgrid[0:H, 0:W]
    sign_box = (xx >= 520) & (xx <= 1020) & (yy >= 55) & (yy <= 295)
    hotdog_box = (xx >= 885) & (xx <= 1018) & (yy >= 55) & (yy <= 180)

    cyan_mask = sign_box & (~hotdog_box) & ((arr0[:, :, 2] - arr0[:, :, 0]) > 22) & (arr0[:, :, 1] > 110)
    hd_mask = hotdog_box & ((arr0[:, :, 0] - arr0[:, :, 2]) > 35) & (arr0[:, :, 0] > 120)

    # Soft glow overlays
    cyan_glow_im = Image.fromarray((cyan_mask.astype(np.uint8) * 255)).filter(ImageFilter.GaussianBlur(14))
    cyan_glow = np.array(cyan_glow_im, dtype=np.float32) / 255.0

    hd_glow_im = Image.fromarray((hd_mask.astype(np.uint8) * 255)).filter(ImageFilter.GaussianBlur(10))
    hd_glow = np.array(hd_glow_im, dtype=np.float32) / 255.0

    lamp_dist = np.sqrt(((xx - 203) / 110.0) ** 2 + ((yy - 108) / 95.0) ** 2)
    lamp_glow = np.clip(1.0 - lamp_dist, 0.0, 1.0) ** 2

    # Deterministic flicker patterns
    rng = np.random.default_rng(6700)
    frames: list[Image.Image] = []

    for i in range(N_FRAMES):
        t = i / FPS
        arr = arr0.copy()

        # 1. Cyan WIENER TUESDAY'S hum + brief sputter dips at t=0.75s and t=1.95s
        cyan_level = 1.0 + 0.08 * math.sin(2 * math.pi * 7.0 * t)
        if 0.72 <= t <= 0.84 or 1.92 <= t <= 2.00:
            cyan_level = 0.38 if (i % 2 == 0) else 1.18
        arr[cyan_mask] = np.clip(arr[cyan_mask] * cyan_level, 0, 255)
        arr[:, :, 1] += cyan_glow * (cyan_level - 0.85) * 55.0
        arr[:, :, 2] += cyan_glow * (cyan_level - 0.85) * 65.0

        # 2. Hotdog neon blink (classic diner blink every ~0.9s)
        hd_on = 0.28 if (0.45 <= (t % 1.1) <= 0.62) else (1.12 + 0.06 * math.sin(2 * math.pi * 5 * t))
        arr[hd_mask] = np.clip(arr[hd_mask] * hd_on, 0, 255)
        arr[:, :, 0] += hd_glow * (hd_on - 0.75) * 75.0
        arr[:, :, 1] += hd_glow * (hd_on - 0.75) * 35.0

        # 3. Streetlamp warm pulse
        lp = 0.06 * math.sin(2 * math.pi * 3.2 * t) + float(rng.uniform(-0.015, 0.015))
        arr[:, :, 0] += lamp_glow * lp * 140.0
        arr[:, :, 1] += lamp_glow * lp * 110.0

        im = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
        draw = ImageDraw.Draw(im)

        # 4. Two tiny cartoon moths orbiting the streetlamp bulb
        for m_idx, (rx, ry, spd, ph) in enumerate([(34, 16, 4.2, 0.0), (22, 24, -5.4, 2.1)]):
            mx = 203 + rx * math.cos(spd * t + ph)
            my = 112 + ry * math.sin(spd * t + ph * 1.3)
            wing = 3 + 2 * abs(math.sin(22 * t + m_idx))
            draw.ellipse((mx - wing, my - 2, mx + wing, my + 2), fill=(242, 228, 175), outline=(40, 35, 25))

        # 5. Heavy bear-footstep camera bob + steady push-in toward the open tavern door (x=885, y=455)
        prog = i / max(1, N_FRAMES - 1)
        zoom = 1.0 + 0.11 * prog
        step_bob = abs(math.sin(math.pi * 2.3 * t)) ** 3 * 7.0  # heavy lumbering thuds
        sway_x = math.sin(math.pi * 2.3 * t) * 4.5

        cw, ch = W / zoom, H / zoom
        cx = (W * 0.5) * (1 - prog * 0.22) + 885 * (prog * 0.22) + sway_x
        cy = (H * 0.5) * (1 - prog * 0.10) + 455 * (prog * 0.10) + step_bob
        x0 = max(0.0, min(W - cw, cx - cw / 2))
        y0 = max(0.0, min(H - ch, cy - ch / 2))

        cropped = im.crop((int(x0), int(y0), int(x0 + cw), int(y0 + ch))).resize(
            (1280, 720), Image.Resampling.LANCZOS
        )
        frames.append(cropped)

    return frames


def extract_feather_and_clean_plate(arr0: np.ndarray) -> tuple[Image.Image, np.ndarray]:
    """Extract the floating feather (with dark ink outline) and clean the wooden bar behind it."""
    # Feather + surrounding ink lines sit inside x:1124..1262, y:572..656 over vertical bar slats
    x1, y1, x2, y2 = 1124, 572, 1262, 656
    patch = arr0[y1:y2, x1:x2].copy()

    # Background wood reference sampled from clean vertical bar planks just to the left (x:1035..1120)
    wood_ref = arr0[y1:y2, 1040:1120]
    wood_med = np.median(wood_ref, axis=1, keepdims=True)  # per-row vertical wood gradient
    # Tile clean wood texture horizontally with subtle plank variation
    clean_patch = np.resize(wood_ref[:, 12:68, :], patch.shape).astype(np.float32)
    clean_patch = 0.65 * clean_patch + 0.35 * wood_med

    # Feather pixels differ strongly from medium-brown wood (either bright white feather or black ink outline)
    diff = np.linalg.norm(patch - wood_med, axis=2)
    bright = (patch[:, :, 0] > 140) & (patch[:, :, 1] > 135)
    dark_ink = (patch[:, :, 0] < 48) & (patch[:, :, 1] < 45)
    raw_mask = (diff > 36) | bright | dark_ink

    # Keep central feather region and feather out edges
    mask_im = Image.fromarray((raw_mask.astype(np.uint8) * 255))
    mask_im = mask_im.filter(ImageFilter.MaxFilter(3)).filter(ImageFilter.GaussianBlur(1.2))
    alpha = np.array(mask_im, dtype=np.uint8)
    # Zero out outer border of patch so no rectangular seam ever appears
    alpha[:3, :] = 0
    alpha[-3:, :] = 0
    alpha[:, :3] = 0
    alpha[:, -3:] = 0

    rgba = np.dstack([np.clip(patch, 0, 255).astype(np.uint8), alpha])
    feather_sprite = Image.fromarray(rgba, mode="RGBA")

    plate = arr0.copy()
    blend = (alpha[:, :, None].astype(np.float32)) / 255.0
    # Also clean the static black spin lines around the stool (y:672..736, x:1045..1110 & 1292..1355)
    plate[y1:y2, x1:x2] = plate[y1:y2, x1:x2] * (1.0 - blend) + clean_patch * blend
    for sx1, sx2, refx1, refx2 in [(1045, 1104, 995, 1042), (1294, 1356, 1356, 1375)]:
        sub = plate[666:738, sx1:sx2]
        ref = np.median(plate[666:738, refx1:refx2], axis=1, keepdims=True)
        ink = (sub[:, :, 0] < 45) & (sub[:, :, 1] < 45)
        sub[ink] = ref.repeat(sx2 - sx1, axis=1)[ink]
        plate[666:738, sx1:sx2] = sub

    return feather_sprite, plate


def build_shot_5c() -> list[Image.Image]:
    base = Image.open(ASSETS / "concept_5c_oklahoma_neon.jpg").convert("RGB")
    arr0 = np.array(base, dtype=np.float32)
    H, W, _ = arr0.shape

    feather_sprite, clean_plate = extract_feather_and_clean_plate(arr0)
    yy, xx = np.mgrid[0:H, 0:W]

    # Pink OKLAHOMA neon sign: full sign (605..975, 110..260), smooth boxless radial mask on 'MA'
    sign_box = (xx >= 605) & (xx <= 975) & (yy >= 110) & (yy <= 262)
    pink_tubes = sign_box & ((clean_plate[:, :, 0] - clean_plate[:, :, 1]) > 42) & (clean_plate[:, :, 0] > 165)

    # Isolate the actual 'MA' letter ridges via high-pass local contrast inside a smooth radial envelope
    blur_bg = np.array(base.filter(ImageFilter.GaussianBlur(7)), dtype=np.float32)
    ridge = np.clip(clean_plate[:, :, 0] - blur_bg[:, :, 0], 0.0, 80.0) / 28.0
    ma_env = np.exp(-(((xx - 912.0) / 46.0) ** 2 + ((yy - 188.0) / 36.0) ** 2))
    ma_tube_weight = np.clip(ridge * ma_env, 0.0, 1.0)
    ma_halo_weight = ma_env ** 1.4

    sign_glow = np.array(
        Image.fromarray((pink_tubes.astype(np.uint8) * 255)).filter(ImageFilter.GaussianBlur(16)),
        dtype=np.float32,
    ) / 255.0

    # Red stool cushion mask for spinning highlight sweep
    stool_box = (xx >= 1104) & (xx <= 1292) & (yy >= 668) & (yy <= 712)
    stool_red = stool_box & ((clean_plate[:, :, 0] - clean_plate[:, :, 1]) > 28)

    # Sputter schedule for the dying 'MA' neon letters (0.0 = dead dark, 1.0 = full bright pink)
    sputter_pattern = [
        0.15, 0.15, 1.15, 1.10, 0.20, 0.95, 1.15, 1.15, 1.10, 0.10, 0.10, 0.85,
        1.15, 1.15, 0.25, 1.10, 1.15, 0.15, 0.15, 0.15, 1.20, 1.15, 0.30, 1.05,
    ]

    frames: list[Image.Image] = []
    for i in range(N_FRAMES):
        t = i / FPS
        prog = i / max(1, N_FRAMES - 1)
        arr = clean_plate.copy()

        # 1. Bear contented hiccup at t=0.35s + gentle belly breathing (squash/stretch in x:40..735, y:300..768)
        hiccup = math.exp(-((t - 0.38) / 0.11) ** 2) * 9.0
        breath = math.sin(2 * math.pi * 0.75 * t) * 3.5 + hiccup
        by1, by2, bx1, bx2 = 300, H, 30, 740
        bear_patch = Image.fromarray(np.clip(arr[by1:by2, bx1:bx2], 0, 255).astype(np.uint8))
        new_h = max(10, int(round((by2 - by1) + breath)))
        warped = bear_patch.resize((bx2 - bx1, new_h), Image.Resampling.BICUBIC)
        if new_h >= (by2 - by1):
            arr[by1:by2, bx1:bx2] = np.array(warped.crop((0, new_h - (by2 - by1), bx2 - bx1, new_h)), dtype=np.float32)
        else:
            pad_top = (by2 - by1) - new_h
            arr[by1 + pad_top : by2, bx1:bx2] = np.array(warped, dtype=np.float32)

        # 2. OKLAHOMA pink neon buzz + flickering 'MA'
        hum = 1.04 + 0.05 * math.sin(2 * math.pi * 8.0 * t)
        arr[pink_tubes] = np.clip(arr[pink_tubes] * hum, 0, 255)
        arr[:, :, 0] += sign_glow * (hum - 0.92) * 85.0
        arr[:, :, 2] += sign_glow * (hum - 0.92) * 35.0

        ma_lvl = sputter_pattern[i % len(sputter_pattern)]
        if ma_lvl > 0.5:
            # Ignite the dimmed 'MA' letter ridges + soft radial pink halo (zero rectangular seam)
            arr[:, :, 0] += (ma_tube_weight * 95.0 + ma_halo_weight * 34.0) * ma_lvl
            arr[:, :, 1] += (ma_tube_weight * 48.0 + ma_halo_weight * 8.0) * ma_lvl
            arr[:, :, 2] += (ma_tube_weight * 62.0 + ma_halo_weight * 16.0) * ma_lvl
        else:
            arr[:, :, 0] -= ma_halo_weight * 18.0
            arr[:, :, 1] -= ma_halo_weight * 10.0
            arr[:, :, 2] -= ma_halo_weight * 12.0

        # 3. Spinning red stool seat — rotating specular sheen sweeping across the cushion
        ang_speed = 16.0 * (1.0 - 0.55 * prog)  # decelerates smoothly over the 4s shot
        sheen_x = 1198 + 78.0 * math.sin(ang_speed * t)
        sheen = np.exp(-((xx - sheen_x) / 26.0) ** 2) * stool_red
        arr[:, :, 0] = np.clip(arr[:, :, 0] + sheen * 48.0, 0, 255)
        arr[:, :, 1] = np.clip(arr[:, :, 1] + sheen * 26.0, 0, 255)
        arr[:, :, 2] = np.clip(arr[:, :, 2] + sheen * 22.0, 0, 255)

        im = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).convert("RGBA")
        draw = ImageDraw.Draw(im)

        # 4. Cartoon black-ink spin arcs whipping around the spinning red stool (alternating frames)
        spin_energy = max(0.2, 1.0 - 0.65 * prog)
        n_arcs = 3 if spin_energy > 0.45 else 2
        for a_idx in range(n_arcs):
            jitter_y = ((i * 7 + a_idx * 13) % 9) - 4
            arc_pad = 14 + a_idx * 11
            bbox = (1096 - arc_pad, 668 + jitter_y, 1300 + arc_pad, 718 + jitter_y)
            if (i + a_idx) % 2 == 0:
                draw.arc(bbox, start=152, end=208, fill=(22, 18, 16, 220), width=3)
                draw.arc(bbox, start=-28, end=28, fill=(22, 18, 16, 220), width=3)
            else:
                draw.arc(bbox, start=160, end=198, fill=(22, 18, 16, 180), width=2)
                draw.arc(bbox, start=-18, end=20, fill=(22, 18, 16, 180), width=2)

        # 5. Floating white feather swaying side-to-side like a pendulum and settling onto the stool seat!
        settle = min(1.0, t / 2.65)  # lands gently on the cushion right around 2.65s
        ease = 1.0 - (1.0 - settle) ** 2
        fy = int(round(535 + ease * 96))  # drops from y=535 down to y=631 (resting on the stool!)
        sway_amp = (1.0 - settle) * 26.0
        fx = int(round(1126 + math.sin(2 * math.pi * 1.35 * t) * sway_amp))
        tilt_deg = math.cos(2 * math.pi * 1.35 * t) * (1.0 - settle) * 18.0

        rotated_feather = feather_sprite.rotate(tilt_deg, resample=Image.Resampling.BICUBIC, expand=True)
        im.alpha_composite(rotated_feather, dest=(fx, fy))

        # 6. Subtle camera push-in to frame 1280x720 cleanly
        rgb = im.convert("RGB")
        zoom = 1.0 + 0.045 * prog
        cw, ch = W / zoom, H / zoom
        x0 = (W - cw) * 0.52
        y0 = (H - ch) * 0.46
        cropped = rgb.crop((int(x0), int(y0), int(x0 + cw), int(y0 + ch))).resize(
            (1280, 720), Image.Resampling.LANCZOS
        )
        frames.append(cropped)

    return frames


def _find_persp_coeffs(dst_pts: list[tuple[float, float]], src_pts: list[tuple[float, float]]) -> list[float]:
    matrix = []
    for (dx, dy), (sx, sy) in zip(dst_pts, src_pts):
        matrix.append([dx, dy, 1, 0, 0, 0, -sx * dx, -sx * dy])
        matrix.append([0, 0, 0, dx, dy, 1, -sy * dx, -sy * dy])
    A = np.array(matrix, dtype=np.float64)
    B = np.array([c for pt in src_pts for c in pt], dtype=np.float64)
    return np.linalg.solve(A, B).tolist()


def build_shot_5c_bear_growl() -> list[Image.Image]:
    """
    Solo low-angle shot looking UP at the towering growling bear (1.45s = 35 frames @ 24fps):
    - Uses authentic moving frames (0.12s..1.58s) from Clip 5 so jaws, tongue, drool, and eyes
      snarl natively in 100% matching art style.
    - Crops out the woman/claws on the right and applies an upward low-angle perspective tilt
      + menacing push-in + subtle roar tremor.
    """
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    src = BASE_DIR / "5-Bear_swallows_lady_at_bar_6f6f8af1.mp4"
    tmp = BASE_DIR / "_animatic_build" / "c5_growl_src"
    tmp.mkdir(parents=True, exist_ok=True)
    for old in tmp.glob("f_*.png"):
        old.unlink()

    n_frames = 35
    subprocess.run(
        [ff, "-y", "-ss", "0.12", "-t", "1.50", "-i", str(src), "-vf", "fps=24,scale=1280:720", str(tmp / "f_%04d.png")],
        check=True,
        capture_output=True,
    )
    raw_files = sorted(tmp.glob("f_*.png"))
    rng = np.random.default_rng(6700)
    frames: list[Image.Image] = []

    W, H = 1280, 720
    # Upward camera tilt: expand bottom / pinch top slightly in source lookup so bear towers overhead
    dst = [(0, 0), (W, 0), (W, H), (0, H)]
    src_quad = [(-55, -18), (W + 55, -18), (W - 35, H + 12), (35, H + 12)]
    coeffs = _find_persp_coeffs(dst, src_quad)

    # Dark overhead vignette for ominous towering feel
    yy, xx = np.mgrid[0:H, 0:W]
    vig = 1.0 - 0.24 * np.clip(((xx - W * 0.55) / (W * 0.65)) ** 2 + ((yy - H * 0.55) / (H * 0.65)) ** 2, 0.0, 1.4)

    for i in range(n_frames):
        im_src = Image.open(raw_files[min(i, len(raw_files) - 1)]).convert("RGB")
        prog = i / max(1, n_frames - 1)
        # Tight solo crop on bear's snarling head & shoulders (x=248..804, y=10..323), pushing closer
        jx = float(rng.uniform(-2.5, 2.5))
        jy = float(rng.uniform(-2.5, 2.5))
        cw = 556 * (1.0 - 0.10 * prog)
        ch = cw * 9.0 / 16.0
        x0 = 252 + 28 * prog + jx
        y0 = 12 + 10 * prog + jy
        crop = im_src.crop((int(x0), int(y0), int(x0 + cw), int(y0 + ch))).resize((W, H), Image.Resampling.LANCZOS)
        tilted = crop.transform((W, H), Image.Transform.PERSPECTIVE, coeffs, Image.Resampling.BICUBIC)
        arr = np.clip(np.array(tilted, dtype=np.float32) * vig[:, :, None], 0, 255).astype(np.uint8)
        frames.append(Image.fromarray(arr))

    return frames


def _draw_heart(draw: ImageDraw.ImageDraw, cx: float, cy: float, size: float, fill: tuple, outline: tuple) -> None:
    pts = []
    for k in range(36):
        ang = 2 * math.pi * k / 36
        hx = 16 * (math.sin(ang) ** 3)
        hy = -(13 * math.cos(ang) - 5 * math.cos(2 * ang) - 2 * math.cos(3 * ang) - math.cos(4 * ang))
        pts.append((cx + hx * size / 16.0, cy + hy * size / 16.0))
    draw.polygon(pts, fill=fill, outline=outline, width=2)


def build_shot_5d_lady_solo() -> list[Image.Image]:
    """
    Solo close-up of the woman (1.95s = 47 frames @ 24fps):
    - 100% authentic Clip 5 woman artwork with the bear's claw cleanly erased using Clip 5 @ 3.00s clean wall.
    - 3-stage overacting melodrama:
      1) Frightened gasp (0.00s - 0.42s): wide terrified eyes & trembling shock lines
      2) Playful blushing coquette (0.45s - 1.15s): warm rosy blush cheeks bloom, heavy fluttering
         half-lidded lashes, dainty scandalized 'Oh my!' O-mouth, floating cartoon hearts!
      3) Grandiose theatrical faint (1.18s - 1.95s): eyes flutter completely shut with dramatic lashes,
         back-of-hand / swoon tilt (-13 deg Dutch lean + downward sink) & dizzy swoon stars!
    """
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    src = BASE_DIR / "5-Bear_swallows_lady_at_bar_6f6f8af1.mp4"
    tmp = BASE_DIR / "_animatic_build" / "c5_lady_src"
    tmp.mkdir(parents=True, exist_ok=True)
    for old in tmp.glob("f_*.png"):
        old.unlink()

    subprocess.run(
        [ff, "-y", "-ss", "0.18", "-t", "0.95", "-i", str(src), "-vf", "fps=24,scale=1280:720", str(tmp / "f_%04d.png")],
        check=True,
        capture_output=True,
    )
    clean_p = tmp / "clean_3s.png"
    subprocess.run(
        [ff, "-y", "-ss", "3.05", "-i", str(src), "-frames:v", "1", "-vf", "scale=1280:720", str(clean_p)],
        check=True,
        capture_output=True,
    )
    im_cl = np.array(Image.open(clean_p).convert("RGB"), dtype=np.float32)
    raw_files = sorted(tmp.glob("f_*.png"))

    # Clean-plate mask removing bear's claw AND half-bartender on left (x < 956 above y=262, x < 915 down to y=520)
    mask = np.zeros((720, 1280), dtype=np.float32)
    for y in range(525):
        lim = 958 if y < 262 else 912
        ramp = 26
        mask[y, : lim - ramp] = 1.0
        for x in range(lim - ramp, lim):
            mask[y, x] = max(0.0, 1.0 - (x - (lim - ramp)) / float(ramp))

    # Build clean oversized solo plates (crop x=748..1280, y=96..395 -> 1600x900 for full rotation headroom!)
    pW, pH = 1600, 900
    plates: list[Image.Image] = []
    for rf in raw_files:
        im_f = np.array(Image.open(rf).convert("RGB"), dtype=np.float32)
        comp = np.clip(im_f * (1.0 - mask[:, :, None]) + im_cl * mask[:, :, None], 0, 255).astype(np.uint8)
        plates.append(Image.fromarray(comp).crop((748, 96, 1280, 395)).resize((pW, pH), Image.Resampling.LANCZOS))

    n_frames = 47  # 1.95s @ 24fps
    frames: list[Image.Image] = []
    yy, xx = np.mgrid[0:pH, 0:pW]

    for i in range(n_frames):
        t = i / FPS
        p_idx = (i % min(10, len(plates))) if t < 1.15 else min(5, len(plates) - 1)
        arr = np.array(plates[p_idx], dtype=np.float32)

        # Fast exact cartoon eye-socket finder (<2ms/frame): find white sclera seeds, then flood-fill
        # exterior from each eye box border stopping at the black ink eye ring (luma < 80)!
        luma_full = arr.mean(axis=2)
        fzone = (xx >= 665) & (xx <= 945) & (yy >= 450) & (yy <= 575)
        seeds = fzone & (arr[:, :, 0] > 215) & (arr[:, :, 1] > 210) & (arr[:, :, 2] > 205)
        s_ys, s_xs = np.where(seeds)
        x_split = int(np.median(s_xs)) if len(s_xs) else 780

        eye_boxes = []
        for seed_side in [seeds & (xx < x_split), seeds & (xx >= x_split)]:
            eys, exs = np.where(seed_side)
            if len(exs) < 80:
                continue
            # Flood-fill INWARD from white sclera seeds stopping at the black ink eye ring (luma < 95),
            # then fill ONLY the small enclosed pupil dot (< 600 px) inside that eyeball!
            bx1, by1 = max(0, int(exs.min()) - 14), max(0, int(eys.min()) - 14)
            bx2, by2 = min(pW, int(exs.max()) + 18), min(pH, int(eys.max()) + 28)
            sub_luma = luma_full[by1:by2, bx1:bx2]
            sub_b = arr[by1:by2, bx1:bx2, 2]
            # Eyeball sclera has B >= 166 (nose-bridge peach skin has B < 155, black ink ring has B < 80)!
            passable = (sub_luma >= 115) & (sub_b >= 166)
            bh, bw = passable.shape
            scl = np.zeros((bh, bw), dtype=bool)
            q: list[tuple[int, int]] = []
            for sy, sx in zip(eys - by1, exs - bx1):
                if passable[sy, sx] and not scl[sy, sx]:
                    scl[sy, sx] = True
                    q.append((int(sy), int(sx)))
            qi = 0
            while qi < len(q):
                cy, cx = q[qi]
                qi += 1
                for ny, nx in ((cy - 1, cx), (cy + 1, cx), (cy, cx - 1), (cy, cx + 1)):
                    if 0 <= ny < bh and 0 <= nx < bw and passable[ny, nx] and not scl[ny, nx]:
                        scl[ny, nx] = True
                        q.append((ny, nx))
            # Fill any enclosed interior hole (the black pupil!) not reachable from box border across ~scl
            outside = np.zeros((bh, bw), dtype=bool)
            oq: list[tuple[int, int]] = []
            for rx in range(bw):
                for ry in (0, bh - 1):
                    if not scl[ry, rx] and not outside[ry, rx]:
                        outside[ry, rx] = True
                        oq.append((ry, rx))
            for ry in range(bh):
                for rx in (0, bw - 1):
                    if not scl[ry, rx] and not outside[ry, rx]:
                        outside[ry, rx] = True
                        oq.append((ry, rx))
            oqi = 0
            while oqi < len(oq):
                cy, cx = oq[oqi]
                oqi += 1
                for ny, nx in ((cy - 1, cx), (cy + 1, cx), (cy, cx - 1), (cy, cx + 1)):
                    if 0 <= ny < bh and 0 <= nx < bw and not scl[ny, nx] and not outside[ny, nx]:
                        outside[ny, nx] = True
                        oq.append((ny, nx))
            interior_sub = ~outside
            iy, ix = np.where(interior_sub)
            if len(ix) > 150:
                full_mask = np.zeros((pH, pW), dtype=bool)
                full_mask[by1:by2, bx1:bx2] = interior_sub
                eye_boxes.append((full_mask, bx1 + int(ix.min()), by1 + int(iy.min()), bx1 + int(ix.max()), by1 + int(iy.max())))

        # Rosy blush cheeks softly tinted onto her real shaded skin just below her two eyeballs!
        blush_amt = float(np.clip((t - 0.36) / 0.26, 0.0, 1.0))
        if blush_amt > 0 and len(eye_boxes) == 2:
            (_, lx1, ly1, lx2, ly2), (_, rx1, ry1, rx2, ry2) = eye_boxes
            lcx, lcy = lx1 + 14, ly2 + 22
            rcx, rcy = rx2 - 10, ry2 + 22
            blush_field = np.clip(
                np.exp(-(((xx - lcx) / 42.0) ** 2 + ((yy - lcy) / 22.0) ** 2))
                + np.exp(-(((xx - rcx) / 46.0) ** 2 + ((yy - rcy) / 24.0) ** 2)),
                0.0,
                1.0,
            )
            # Mask out dark ink lines & white teeth so ink stays crisp black!
            luma = arr.mean(axis=2)
            skin_like = np.clip((luma - 65.0) / 45.0, 0.0, 1.0) * np.clip((235.0 - luma) / 30.0, 0.0, 1.0)
            pulse = 1.0 + 0.14 * math.sin(2 * math.pi * 4.0 * t)
            b = blush_field * skin_like * blush_amt * pulse
            arr[:, :, 0] = np.clip(arr[:, :, 0] + b * 52.0, 0, 255)
            arr[:, :, 1] = np.clip(arr[:, :, 1] - b * 54.0, 0, 255)
            arr[:, :, 2] = np.clip(arr[:, :, 2] - b * 38.0, 0, 255)

        # Eyelids masked STRICTLY INSIDE her real white eyeballs (zero boxes outside eye sockets!)
        if t >= 0.42 and len(eye_boxes) == 2:
            if t < 1.15:
                # Coquettish playful half-lidded flutter!
                flutter = 0.54 + 0.16 * math.sin(2 * math.pi * 6.5 * t)
            else:
                # Grandiose full swoon — eyes flutter completely shut!
                flutter = min(1.05, 0.62 + (t - 1.15) / 0.18)

            for side_mask, ex1, ey1, ex2, ey2 in eye_boxes:
                ecx = 0.5 * (ex1 + ex2)
                erx = max(8.0, 0.5 * (ex2 - ex1))
                in_socket = side_mask
                lid_y = ey1 + (ey2 - ey1) * flutter
                lid_curve = lid_y + 0.08 * (xx - ecx)
                lid_fill = in_socket & (yy <= lid_curve)
                lash_band = in_socket & (np.abs(yy - lid_curve) <= 3.5)

                shade = 0.88 + 0.12 * np.cos(np.clip((xx - ecx) / erx, -1.2, 1.2) * 1.2)
                arr[lid_fill, 0] = 196.0 * shade[lid_fill]
                arr[lid_fill, 1] = 152.0 * shade[lid_fill]
                arr[lid_fill, 2] = 136.0 * shade[lid_fill]
                if flutter < 0.96:
                    arr[lash_band] = [20, 15, 15]
                else:
                    closed_curve = ey1 + (ey2 - ey1) * 0.68 + 7.0 * np.cos(np.clip((xx - ecx) / erx, -1.1, 1.1) * 1.3)
                    closed_lash = in_socket & (np.abs(yy - closed_curve) <= 3.5)
                    arr[closed_lash] = [20, 15, 15]

        im = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).convert("RGBA")
        draw = ImageDraw.Draw(im)

        # Floating playful pink cartoon hearts + grandiose swoon sparkles!
        if t >= 0.42:
            for bx, by, sc, ph in [(565, 340, 20.0, 0.0), (505, 445, 15.0, 1.5), (1045, 320, 18.0, 2.6), (995, 425, 13.0, 0.8)]:
                rise = (t - 0.42) * 46.0
                wob = math.sin(5.8 * t + ph) * 12.0
                _draw_heart(draw, bx + wob, by - rise, sc, fill=(238, 86, 122, 240), outline=(22, 14, 16, 255))

        # Phase 3 grandiose theatrical faint swoon: zoom in slightly + smooth -9 deg backward swoon lean (ZERO black corners!)
        rgb = im.convert("RGB")
        if t >= 1.15:
            swoon_p = min(1.0, (t - 1.15) / 0.78)
            ease = swoon_p * swoon_p * (3 - 2 * swoon_p)
            angle = -8.5 * ease
            # Pre-zoom 1.14x around center so 1600x900 rotated -8.5 deg has ZERO black corners inside 1280x720!
            z = 1.0 + 0.14 * ease
            zw, zh = int(pW * z), int(pH * z)
            big = rgb.resize((zw, zh), Image.Resampling.BICUBIC)
            rot = big.rotate(angle, resample=Image.Resampling.BICUBIC, center=(zw // 2, int(zh * 0.72)))
            cx = zw // 2 - int(24 * ease)
            cy = zh // 2 - int(28 * ease)
            cropped = rot.crop((cx - 640, cy - 360, cx + 640, cy + 360))
        else:
            # Center crop 1280x720 from 1600x900 with subtle excited gasp tremble
            jit_y = int(3 * math.sin(28 * t)) if t < 0.42 else 0
            x0, y0 = (pW - 1280) // 2, (pH - 720) // 2 + jit_y
            cropped = rgb.crop((x0, y0, x0 + 1280, y0 + 720))

        frames.append(cropped)

    return frames


def scrub_clip1_flies() -> Path:
    """
    Remove tiny buzzing black flies & 0.2s 'no.' text artifact from Clip 1:
    - Starts at 0.85s (past the 0.2s 'no.' artifact).
    - Computes temporal median background on the plaster wall above the bear & bartender,
      replacing transient dark fly specks without touching character line art.
    """
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    src = BASE_DIR / "1-Bear_demanding_beer_at_bar_9c18c2c5.mp4"
    out_mp4 = ASSETS / "1-Bear_demanding_beer_clean.mp4"
    tmp = BASE_DIR / "_animatic_build" / "clip1_clean"
    tmp.mkdir(parents=True, exist_ok=True)
    for old in tmp.glob("f_*.png"):
        old.unlink()

    subprocess.run(
        [ff, "-y", "-ss", "0.85", "-i", str(src), "-vf", "fps=24,scale=1280:720", str(tmp / "f_%04d.png")],
        check=True,
        capture_output=True,
    )
    files = sorted(tmp.glob("f_*.png"))
    stack = np.stack([np.array(Image.open(p).convert("RGB")) for p in files], axis=0)
    med = np.percentile(stack, 75, axis=0).astype(np.uint8)

    # Only scrub tiny isolated dark specks (area <= 110 px, <= 16x16 bbox) on bright plaster wall — never touch heads/hats!
    for idx, p in enumerate(files):
        frame = stack[idx].copy()
        diff_dark = ((med.astype(np.int16) - frame.astype(np.int16)).mean(axis=2) > 28) & (med.mean(axis=2) > 135)
        diff_dark[220:, :] = False  # ceiling/upper wall only
        ys, xs = np.where(diff_dark)
        visited = np.zeros_like(diff_dark, dtype=bool)
        for y0, x0 in zip(ys, xs):
            if visited[y0, x0]:
                continue
            # Small BFS flood-fill capped at 130 pixels
            comp = [(y0, x0)]
            visited[y0, x0] = True
            q_idx = 0
            while q_idx < len(comp) and len(comp) <= 130:
                cy, cx = comp[q_idx]
                q_idx += 1
                for ny, nx in ((cy - 1, cx), (cy + 1, cx), (cy, cx - 1), (cy, cx + 1)):
                    if 0 <= ny < 220 and 0 <= nx < 1280 and diff_dark[ny, nx] and not visited[ny, nx]:
                        visited[ny, nx] = True
                        comp.append((ny, nx))
            if len(comp) <= 110:
                cys = [c[0] for c in comp]
                cxs = [c[1] for c in comp]
                if (max(cys) - min(cys) <= 16) and (max(cxs) - min(cxs) <= 18):
                    pad = 2
                    r1, r2 = max(0, min(cys) - pad), min(220, max(cys) + pad + 1)
                    c1, c2 = max(0, min(cxs) - pad), min(1280, max(cxs) + pad + 1)
                    frame[r1:r2, c1:c2] = med[r1:r2, c1:c2]
        Image.fromarray(frame).save(p)

    subprocess.run(
        [ff, "-y", "-framerate", "24", "-i", str(tmp / "f_%04d.png"), "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p", str(out_mp4)],
        check=True,
        capture_output=True,
    )
    return out_mp4


def build_shot_9a() -> list[Image.Image]:
    """
    Scene 9A (51.36s -> 55.31s = 3.95s @ 24fps = 95 frames):
    - Uses 100% AUTHENTIC Clip 7 artwork (single close-up on the Clip 7 bartender,
      zero off-style AI bear, zero style jump between Seq 8 -> Shot 9A -> Shot 9B!).
    - Bartender holds his smug deadpan smirk during setup + 1.0s pause, then his real jaw
      drops ONLY on the measured syllables of 'Well, that was a barbiturate.'
    """
    base = Image.open(ASSETS / "9A_authentic_clip7_bartender.png").convert("RGB")
    arr0 = np.array(base, dtype=np.uint8)
    H, W, _ = arr0.shape
    n9 = int(round(3.95 * FPS))

    ff = imageio_ffmpeg.get_ffmpeg_exe()
    audio_path = BASE_DIR / "Recording (6).m4a"
    raw = subprocess.run(
        [ff, "-ss", "51.36", "-t", "3.95", "-i", str(audio_path), "-ac", "1", "-ar", "16000", "-f", "s16le", "-"],
        capture_output=True,
        check=True,
    ).stdout
    pcm = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
    spf = 16000.0 / FPS

    # Extract bartender's authentic lower jaw/chin patch below mouth line (y=490..592, x=325..558)
    jx1, jx2, jy1, jy2 = 325, 558, 490, 592
    jaw_patch = Image.fromarray(arr0[jy1:jy2, jx1:jx2]).convert("RGBA")
    jw, jh = jx2 - jx1, jy2 - jy1
    jmask = Image.new("L", (jw, jh), 0)
    md = ImageDraw.Draw(jmask)
    md.rounded_rectangle((6, 0, jw - 7, jh - 5), radius=18, fill=255)
    jmask = jmask.filter(ImageFilter.GaussianBlur(4))
    jaw_patch.putalpha(jmask)

    frames: list[Image.Image] = []
    for i in range(n9):
        t = i / FPS
        t_aud = 51.36 + t
        s0, s1 = int(i * spf), min(len(pcm), int((i + 1) * spf))
        rms = float(np.sqrt(np.mean(pcm[s0:s1] ** 2))) if s1 > s0 else 0.0

        im = base.copy().convert("RGBA")

        open_px = 0
        if 54.02 <= t_aud <= 54.88 and rms > 0.020:
            open_px = 24 if rms > 0.075 else 13

        if open_px > 0:
            im.alpha_composite(jaw_patch, dest=(jx1, jy1 + open_px))
            draw = ImageDraw.Draw(im)

            mx1, mx2, my1 = 352, 522, 488
            my2 = my1 + open_px + 4
            draw.rounded_rectangle(
                (mx1, my1, mx2, my2), radius=8, fill=(36, 16, 20, 255), outline=(18, 14, 14, 255), width=4
            )
            teeth_h = min(8, max(5, open_px // 3 + 2))
            draw.rectangle(
                (mx1 + 7, my1 + 2, mx2 - 7, my1 + 2 + teeth_h),
                fill=(228, 220, 202, 255),
                outline=(28, 22, 20, 255),
                width=1,
            )
            for tx in range(mx1 + 28, mx2 - 16, 24):
                draw.line((tx, my1 + 2, tx, my1 + 2 + teeth_h), fill=(60, 52, 48, 200), width=1)
            if open_px >= 18:
                draw.pieslice((mx1 + 38, my2 - 12, mx2 - 36, my2 + 7), start=180, end=360, fill=(162, 82, 86, 255))
            draw.line((mx1 - 4, my1 + 1, (mx1 + mx2) // 2, my1, mx2 + 6, my1 - 3), fill=(18, 14, 14, 255), width=4)

        # Subtle slow push-in on the bartender's deadpan delivery
        prog = i / max(1, n9 - 1)
        zoom = 1.0 + 0.045 * prog
        cw, ch = W / zoom, H / zoom
        x0 = (W - cw) * 0.44
        y0 = (H - ch) * 0.45
        cropped = im.convert("RGB").crop((int(x0), int(y0), int(x0 + cw), int(y0 + ch))).resize(
            (1280, 720), Image.Resampling.LANCZOS
        )
        frames.append(cropped)

    return frames


def main() -> None:
    brain_dir = Path(r"C:\Users\6700XT\.gemini\antigravity\brain\bee6e213-b286-43be-893b-5f3424068ade")

    print("[1/3] Animating Shot 1A (WIENER TUESDAY'S exterior)...")
    f1 = build_shot_1a()
    out_1a = ASSETS / "0-Wiener_Tuesdays_exterior_local.mp4"
    encode_mp4_and_gif(f1, out_1a, brain_dir / "preview_1a_anim.gif")
    print(f"      -> {out_1a.name} ({out_1a.stat().st_size / 1024:.0f} KB)")

    print("[2/3] Animating Shot 5C (OKLAHOMA neon + spinning stool + drifting feather)...")
    f5 = build_shot_5c()
    out_5c = ASSETS / "5C-Oklahoma_neon_stool_local.mp4"
    encode_mp4_and_gif(f5, out_5c, brain_dir / "preview_5c_anim.gif")
    print(f"      -> {out_5c.name} ({out_5c.stat().st_size / 1024:.0f} KB)")

    print("[3/3] Animating Shot 9A (Bartender deadpan 'barbiturate' punchline, bear mouth shut)...")
    f9 = build_shot_9a()
    out_9a = ASSETS / "9A-Bartender_punchline_local.mp4"
    encode_mp4_and_gif(f9, out_9a, brain_dir / "preview_9a_punchline.gif")
    print(f"      -> {out_9a.name} ({out_9a.stat().st_size / 1024:.0f} KB) + preview_9a_punchline.gif")


if __name__ == "__main__":
    main()
