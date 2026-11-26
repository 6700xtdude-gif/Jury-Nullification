"""
Big Brown Bear - Master Animatic & Sin City Edition Pipeline

Builds two locked 1280x720 @ 24fps master cuts (64.51s exact):
1. bigbrownbear_animatic_master.mp4:
   - Muted gritty tavern color + glowing neon
   - Untouched master voice track (Recording (6).m4a) + subtle synced Cartoon SFX bed
2. bigbrownbear_animatic_sincity_master.mp4:
   - High-contrast film-noir B&W across characters & barroom, preserving vivid glowing
     color ONLY on the neon signs (WIENER TUESDAY'S + hot dog, OKLAHOMA, bar neons)
     and the woman's playful rosy blush & floating pink hearts in Shot 5D!
"""

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path
import numpy as np

BASE_DIR = Path(__file__).resolve().parent
MANIFEST_PATH = BASE_DIR / "bigbrownbear_timing_manifest.json"
AUDIO_MASTER = BASE_DIR / "Recording (6).m4a"
SFX_BED = BASE_DIR / "assets" / "cartoon_sfx_bed.wav"
OUTPUT_MASTER = BASE_DIR / "bigbrownbear_animatic_master.mp4"
OUTPUT_SINCITY = BASE_DIR / "bigbrownbear_animatic_sincity_master.mp4"
BUILD_DIR = BASE_DIR / "_animatic_build"

TARGET_W = 1280
TARGET_H = 720
TARGET_FPS = 24


def find_ffmpeg() -> str | None:
    exe = shutil.which("ffmpeg")
    if exe:
        return exe
    try:
        import imageio_ffmpeg  # type: ignore

        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return None


def fit_filter() -> str:
    return (
        f"scale={TARGET_W}:{TARGET_H}:force_original_aspect_ratio=increase,"
        f"crop={TARGET_W}:{TARGET_H},fps={TARGET_FPS},setsar=1,format=yuv420p"
    )


def framing_filter(framing: str, loop_mode: str = "loop", speed: float = 1.0) -> str:
    zoom = {
        "medium_closeup": (1.28, 0.6, 0.45),
        "tight_gulp": (1.55, 0.5, 0.38),
        "bartender_focus": (1.32, 0.92, 0.42),
    }.get(framing)
    pts = f"setpts={1.0 / speed:.4f}*PTS," if abs(speed - 1.0) > 1e-3 else ""
    tail = ",tpad=stop_mode=clone:stop_duration=5" if loop_mode == "hold_end" else ""
    if not zoom:
        return pts + fit_filter() + tail
    z, fx, fy = zoom
    return pts + f"scale=iw*{z}:ih*{z},crop=iw/{z}:ih/{z}:(iw-iw/{z})*{fx}:(ih-ih/{z})*{fy}," + fit_filter() + tail


def still_filter(motion: str, duration: float) -> str:
    if motion != "slow_push":
        return fit_filter()
    frames = max(1, int(round(duration * TARGET_FPS)))
    step = 0.08 / frames
    return (
        f"scale={TARGET_W * 2}:{TARGET_H * 2}:force_original_aspect_ratio=increase,"
        f"crop={TARGET_W * 2}:{TARGET_H * 2},"
        f"zoompan=z='min(1+{step:.6f}*on,1.08)':d=1:"
        f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={TARGET_W}x{TARGET_H}:fps={TARGET_FPS},"
        f"setsar=1,format=yuv420p"
    )


def validate_manifest(data: dict) -> list[str]:
    errors: list[str] = []
    cal = data.get("lip_sync_calibration", {})
    delay_ms = cal.get("mouth_flap_start_delay_ms")
    close_ms = cal.get("mouth_close_early_ms")
    if delay_ms is None or delay_ms <= 0:
        errors.append("mouth_flap_start_delay_ms must be > 0")
        return errors
    if close_ms is None or close_ms <= 0:
        errors.append("mouth_close_early_ms must be > 0")
        return errors

    lead = data.get("audio_lead_in")
    t = round(float(lead["duration_sec"]), 3) if lead else 0.0

    for seq in data.get("sequences", []):
        sid = seq["sequence"]
        start, end = float(seq["start_sec"]), float(seq["end_sec"])
        if abs(round(end - start, 3) - float(seq["duration_sec"])) > 1e-3:
            errors.append(f"Seq {sid}: end-start ({end - start:.3f}s) != duration_sec ({seq['duration_sec']}s)")
        exp_start = round(start + delay_ms / 1000.0, 3)
        exp_end = round(end - close_ms / 1000.0, 3)
        if abs(float(seq.get("mouth_flap_start_sec", -1)) - exp_start) > 1e-3:
            errors.append(f"Seq {sid}: mouth_flap_start_sec {seq.get('mouth_flap_start_sec')} != {exp_start}")
        if abs(float(seq.get("mouth_flap_end_sec", -1)) - exp_end) > 1e-3:
            errors.append(f"Seq {sid}: mouth_flap_end_sec {seq.get('mouth_flap_end_sec')} != {exp_end}")
        if seq.get("shots"):
            shots = seq["shots"]
            if sid == 5 and len(shots) < 3:
                errors.append(f"Seq {sid}: expected >=3 shots, got {len(shots)}")
            total = round(sum(float(s["duration_sec"]) for s in shots), 3)
            if abs(total - float(seq["duration_sec"])) > 1e-3:
                errors.append(f"Seq {sid}: shots sum {total}s != locked {seq['duration_sec']}s")
        if abs(start - t) > 1e-3:
            errors.append(f"Seq {sid}: start {start}s != running audio timeline {t:.3f}s")
        t = round(start + float(seq["duration_sec"]) + float(seq.get("pause_after_sec", 0)), 3)

    obs = float(data.get("audio_duration_sec_observed", t))
    if abs(t - obs) > 0.05:
        errors.append(f"Audio timeline ends at {t:.2f}s != observed audio {obs:.2f}s")
    return errors


def make_segment(sid: str, label: str, src: dict, duration: float, framing: str = "wide") -> dict:
    for key in ("clip", "fallback_clip"):
        clip_rel = src.get(key)
        if clip_rel and (BASE_DIR / clip_rel).exists():
            return {
                "id": sid,
                "label": label,
                "kind": "clip",
                "path": BASE_DIR / clip_rel,
                "trim_start": float(src.get("clip_trim_start_sec", 0.0)),
                "max_play": float(src["clip_max_play_sec"]) if "clip_max_play_sec" in src else None,
                "duration": duration,
                "framing": src.get("camera_framing", framing),
                "loop_mode": src.get("loop_mode", "loop"),
                "speed": float(src.get("playback_speed", 1.0)),
            }
    if "image" in src:
        return {
            "id": sid,
            "label": label,
            "kind": "image",
            "path": BASE_DIR / src["image"],
            "duration": duration,
            "motion": src.get("motion", "none"),
        }
    raise FileNotFoundError(f"No valid clip or image found for {sid}")


def build_segments(data: dict) -> tuple[list[dict], float, float]:
    segs: list[dict] = []
    for item in data.get("pre_audio_intro", []):
        segs.append(make_segment(item["id"], item["label"], item, float(item["duration_sec"])))
    pre_audio_len = round(sum(s["duration"] for s in segs), 3)

    lead = data.get("audio_lead_in")
    if lead:
        segs.append(make_segment(lead["id"], lead["label"], lead, float(lead["duration_sec"])))

    for seq in data["sequences"]:
        sid = seq["sequence"]
        pause = float(seq.get("pause_after_sec", 0.0))
        shots = seq.get("shots")
        if shots:
            rt = seq.get("reaction_tail")
            for i, shot in enumerate(shots):
                extra = 0.0
                if i == len(shots) - 1:
                    extra = float(rt["hold_on_9a_sec"]) if rt else pause
                dur = float(shot["duration_sec"]) + extra
                segs.append(make_segment(f"S{sid}_{shot['shot_id']}", shot["label"], shot, round(dur, 3)))
            if rt:
                segs.append(
                    make_segment(f"S{sid}_{rt['shot_id']}", rt["label"], rt, round(float(rt["duration_sec"]), 3))
                )
        else:
            segs.append(
                make_segment(f"S{sid}", seq["speaker"], seq, round(float(seq["duration_sec"]) + pause, 3))
            )

    outro_start = len(segs)
    for item in data.get("outro", []):
        segs.append(make_segment(item["id"], item["label"], item, float(item["duration_sec"])))
    outro_len = round(sum(s["duration"] for s in segs[outro_start:]), 3)
    return segs, pre_audio_len, outro_len


def render_segment(ff: str, seg: dict, out: Path) -> None:
    if not seg["path"].exists():
        raise FileNotFoundError(f"Missing source for {seg['id']}: {seg['path']}")
    dur = f"{seg['duration']:.3f}"
    if seg["kind"] == "image":
        cmd = [
            ff, "-y", "-loop", "1", "-framerate", str(TARGET_FPS), "-i", str(seg["path"]),
            "-t", dur, "-vf", still_filter(seg["motion"], seg["duration"]),
        ]
        tag = f"still/{seg['motion']}"
    else:
        loop_mode = seg.get("loop_mode", "loop")
        max_play = seg.get("max_play")
        loop_args = ["-stream_loop", "-1"] if loop_mode == "loop" else []
        in_limit = ["-t", f"{max_play:.3f}"] if max_play is not None else []
        cmd = [
            ff, "-y", *loop_args, "-ss", f"{seg['trim_start']:.3f}", *in_limit, "-i", str(seg["path"]),
            "-t", dur, "-vf", framing_filter(seg["framing"], loop_mode, seg.get("speed", 1.0)),
        ]
        tag = f"clip/{seg['framing']}"
    cmd += ["-an", "-c:v", "libx264", "-preset", "veryfast", "-crf", "21", "-r", str(TARGET_FPS), str(out)]
    print(f"  [render] {seg['id']:<14} {seg['duration']:5.2f}s  {tag:<20} <- {seg['path'].name}")
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        raise RuntimeError(f"FFmpeg failed on {seg['id']}:\n{res.stderr[-800:]}")


def render_color_master(ff: str, segs: list[dict], pre_audio_len: float, out_path: Path) -> None:
    BUILD_DIR.mkdir(parents=True, exist_ok=True)
    for old in BUILD_DIR.glob("*.mp4"):
        old.unlink()
    parts = []
    for i, seg in enumerate(segs, start=1):
        part = BUILD_DIR / f"{i:02d}_{seg['id']}.mp4"
        render_segment(ff, seg, part)
        parts.append(part)

    concat = BUILD_DIR / "concat_list.txt"
    concat.write_text("".join(f"file '{p.as_posix()}'\n" for p in parts), encoding="utf-8")

    delay_ms = int(round(pre_audio_len * 1000))
    if SFX_BED.exists():
        # Mix 100% untouched voice + subtle Cartoon SFX bed (normalize=0 preserves full voice volume!)
        fc = f"[1:a]adelay={delay_ms}:all=1,apad[voc];[voc][2:a]amix=inputs=2:duration=first:dropout_transition=0:normalize=0[a]"
        audio_inputs = ["-i", str(AUDIO_MASTER), "-i", str(SFX_BED)]
        msg_sfx = "+ Cartoon SFX bed"
    else:
        fc = f"[1:a]adelay={delay_ms}:all=1,apad[a]"
        audio_inputs = ["-i", str(AUDIO_MASTER)]
        msg_sfx = "(voice only)"

    cmd = [
        ff, "-y", "-f", "concat", "-safe", "0", "-i", str(concat), *audio_inputs,
        "-filter_complex", fc,
        "-map", "0:v:0", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
        "-shortest", str(out_path),
    ]
    print(f"\n[+] Muxing {len(parts)} segments + voice ({delay_ms}ms delay) {msg_sfx} -> {out_path.name}")
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        raise RuntimeError(f"FFmpeg mux failed:\n{res.stderr[-800:]}")


def render_sincity_master(ff: str, color_master: Path, out_path: Path) -> None:
    """
    Stream color_master through a vectorized 'Sin City' selective-color filter:
    - High-contrast film-noir B&W across characters, fur, wood, and clothes
    - Preserves glowing color ONLY on neon signs (WIENER TUESDAY'S + neon hot dog,
      OKLAHOMA, bar neons) and the woman's playful rosy blush + floating pink hearts!
    """
    print(f"\n[+] Building 'Sin City' B&W + Selective Neon/Blush Master -> {out_path.name}")
    frame_bytes = TARGET_W * TARGET_H * 3
    yy = np.arange(TARGET_H)[:, None]
    xx = np.arange(TARGET_W)[None, :]
    upper_wall = yy < 285
    ext_sign_box = (xx >= 440) & (xx <= 985) & (yy >= 20) & (yy <= 295)
    lady_blush_zone = (xx >= 350) & (xx <= 1050) & (yy >= 120) & (yy <= 690)

    dec = subprocess.Popen(
        [ff, "-v", "error", "-i", str(color_master), "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
        stdout=subprocess.PIPE,
    )
    enc = subprocess.Popen(
        [
            ff, "-y", "-v", "error",
            "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{TARGET_W}x{TARGET_H}", "-r", str(TARGET_FPS), "-i", "-",
            "-i", str(color_master),
            "-map", "0:v:0", "-map", "1:a:0",
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p",
            "-c:a", "copy", "-shortest", str(out_path),
        ],
        stdin=subprocess.PIPE,
    )
    assert dec.stdout is not None and enc.stdin is not None

    f_idx = 0
    while True:
        buf = dec.stdout.read(frame_bytes)
        if len(buf) < frame_bytes:
            break
        t = f_idx / TARGET_FPS
        f_idx += 1

        rgb = np.frombuffer(buf, dtype=np.uint8).reshape((TARGET_H, TARGET_W, 3)).astype(np.float32)
        r, g, b = rgb[:, :, 0], rgb[:, :, 1], rgb[:, :, 2]

        # Punchy film-noir grayscale S-curve
        gray = 0.299 * r + 0.587 * g + 0.114 * b
        noir = np.clip((gray - 118.0) * 1.18 + 114.0, 0.0, 255.0)

        # Selective color weight [0..1]
        keep = np.zeros((TARGET_H, TARGET_W), dtype=np.float32)

        # 1) Cyan / blue / green neon tubes anywhere in upper bar wall or exterior sign
        cool_neon = np.clip((np.maximum(g, b) - r - 14.0) / 28.0, 0.0, 1.0) * np.clip((np.maximum(g, b) - 95.0) / 55.0, 0.0, 1.0)
        keep = np.maximum(keep, cool_neon * (upper_wall | ext_sign_box))

        # 2) Exterior Shot 1A (3.00s..5.64s): also keep glowing orange neon hotdog inside sign box!
        if 2.95 <= t <= 5.70:
            hotdog = ext_sign_box & (r > 135) & ((r - b) > 45)
            keep = np.maximum(keep, hotdog.astype(np.float32) * np.clip((r - 125.0) / 55.0, 0.0, 1.0))

        # 3) Interior pink/magenta neon signs (OKLAHOMA, DINGER, DIVE heart) strictly in upper wall (never bartender's nose!)
        pink_neon = upper_wall & (r > 130) & (b > 95) & ((r - g) > 26)
        keep = np.maximum(keep, pink_neon.astype(np.float32) * np.clip((r - g - 20.0) / 35.0, 0.0, 1.0))

        # 4) Shot 5D Woman Solo (31.85s..33.80s): keep her rosy pink blush & floating pink cartoon hearts!
        if 31.82 <= t <= 33.82:
            rosy = lady_blush_zone & ((r - g) > 36) & (b > 75) & ((r - b) < 135)
            keep = np.maximum(keep, rosy.astype(np.float32) * np.clip((r - g - 32.0) / 32.0, 0.0, 1.0))

        # Slight neon saturation boost (1.18x) on kept color pixels so neon pops against noir B&W!
        c_boost = np.clip(gray[:, :, None] + (rgb - gray[:, :, None]) * 1.22, 0.0, 255.0)
        out = noir[:, :, None] * (1.0 - keep[:, :, None]) + c_boost * keep[:, :, None]
        enc.stdin.write(out.astype(np.uint8).tobytes())

    enc.stdin.close()
    dec.wait()
    rc = enc.wait()
    if rc != 0:
        raise RuntimeError(f"Sin City FFmpeg encode exited with {rc}")


def main() -> int:
    ap = argparse.ArgumentParser(description="Big Brown Bear Master & Sin City Animatic Pipeline")
    ap.add_argument("--render", action="store_true", help="Render Color Master MP4")
    ap.add_argument("--sincity", action="store_true", help="Also render Sin City B&W + Neon Master MP4")
    args = ap.parse_args()

    print("=" * 72)
    print(" Big Brown Bear — Master Animatic Pipeline (Color + Sin City + SFX)")
    print("=" * 72)

    data = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    errors = validate_manifest(data)
    if errors:
        print("[-] Manifest validation errors:")
        for e in errors:
            print(f"    - {e}")
        return 1

    segs, pre_len, outro_len = build_segments(data)
    audio_span = round(sum(s["duration"] for s in segs) - pre_len - outro_len, 3)
    total = round(pre_len + audio_span + outro_len, 3)
    print(f"[+] Timeline      : pre-card {pre_len:.2f}s + audio {audio_span:.2f}s + end-card {outro_len:.2f}s = {total:.2f}s")
    print(f"[+] Segments      : {len(segs)} locked cuts | SFX bed: {'PRESENT' if SFX_BED.exists() else 'NONE'}")

    if args.render or args.sincity:
        ff = find_ffmpeg()
        if not ff:
            print("[-] FFmpeg not found. Run: uv run --with imageio-ffmpeg --with numpy python assemble_animatic.py --render --sincity")
            return 1
        render_color_master(ff, segs, pre_len, OUTPUT_MASTER)
        print(f"[+] Color Master  : {OUTPUT_MASTER.name} ({OUTPUT_MASTER.stat().st_size / 1048576:.2f} MB)")
        if args.sincity:
            render_sincity_master(ff, OUTPUT_MASTER, OUTPUT_SINCITY)
            print(f"[+] Sin City Cut  : {OUTPUT_SINCITY.name} ({OUTPUT_SINCITY.stat().st_size / 1048576:.2f} MB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
