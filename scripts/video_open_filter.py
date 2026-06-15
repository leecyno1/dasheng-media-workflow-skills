#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any


PRESETS: dict[str, dict[str, Any]] = {
    "warm_cinema": {
        "label": "暖光电影",
        "filters": {
            "soft": {
                "hqdn3d": "0.7:0.6:2.0:1.8",
                "bilateral": "sigmaS=0.55:sigmaR=0.055:planes=1",
                "colorbalance": "rs=0.025:gs=0.006:bs=-0.035:rm=0.020:gm=0.006:bm=-0.030:rh=0.014:gh=0.004:bh=-0.018",
                "eq": "brightness=0.012:contrast=1.035:saturation=1.060:gamma=1.012",
                "unsharp": "5:5:0.22:3:3:0.08",
                "vignette": "angle=PI/7",
                "slim_factor": 0.988,
            },
            "medium": {
                "hqdn3d": "0.9:0.8:2.8:2.2",
                "bilateral": "sigmaS=0.75:sigmaR=0.070:planes=1",
                "colorbalance": "rs=0.046:gs=0.014:bs=-0.050:rm=0.034:gm=0.012:bm=-0.036:rh=0.026:gh=0.010:bh=-0.022",
                "eq": "brightness=0.034:contrast=1.040:saturation=1.095:gamma=1.035",
                "unsharp": "5:5:0.30:3:3:0.10",
                "vignette": "",
                "slim_factor": 0.982,
            },
            "strong": {
                "hqdn3d": "1.1:1.0:3.6:2.8",
                "bilateral": "sigmaS=1.05:sigmaR=0.085:planes=1",
                "colorbalance": "rs=0.055:gs=0.014:bs=-0.066:rm=0.042:gm=0.012:bm=-0.052:rh=0.028:gh=0.008:bh=-0.032",
                "eq": "brightness=0.026:contrast=1.075:saturation=1.105:gamma=1.024",
                "unsharp": "5:5:0.34:3:3:0.12",
                "vignette": "angle=PI/6",
                "slim_factor": 0.976,
            },
        },
    }
}

AUDIO_ENHANCE_FILTER = (
    "highpass=f=80,"
    "lowpass=f=12000,"
    "afftdn=nf=-25,"
    "dynaudnorm=f=150:g=15:p=0.95,"
    "acompressor=threshold=-18dB:ratio=2.5:attack=5:release=80,"
    "loudnorm=I=-14:LRA=8:TP=-1.0,"
    "alimiter=limit=0.95"
)


def run(cmd: list[str], *, capture: bool = False) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        text=True,
        stdout=subprocess.PIPE if capture else None,
        stderr=subprocess.PIPE if capture else None,
        check=True,
    )


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def ffprobe(path: Path) -> dict[str, Any]:
    result = run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "stream=index,codec_type,width,height,duration:format=duration",
            "-of",
            "json",
            str(path),
        ],
        capture=True,
    )
    return json.loads(result.stdout)


def even(value: float) -> int:
    return max(2, int(math.floor(value / 2) * 2))


def video_size(probe: dict[str, Any]) -> tuple[int, int]:
    for stream in probe.get("streams") or []:
        if stream.get("codec_type") == "video":
            return int(stream["width"]), int(stream["height"])
    raise ValueError("input video has no video stream")


def duration(probe: dict[str, Any]) -> float:
    return float((probe.get("format") or {}).get("duration") or 0)


def build_filter(width: int, height: int, preset: str, strength: str, slim_factor: float | None) -> str:
    preset_data = PRESETS[preset]["filters"][strength]
    factor = slim_factor if slim_factor is not None else float(preset_data["slim_factor"])
    if not 0.94 <= factor <= 1.0:
        raise ValueError("--slim-factor must be between 0.94 and 1.0")
    slim_width = even(width * factor)
    pad_x = max(0, (width - slim_width) // 2)
    filters = [
        f"scale={slim_width}:{height}:flags=lanczos",
        f"pad={width}:{height}:{pad_x}:0:color=black",
        f"hqdn3d={preset_data['hqdn3d']}",
        f"bilateral={preset_data['bilateral']}",
        f"colorbalance={preset_data['colorbalance']}",
        "colorlevels=rimin=0.010:gimin=0.008:bimin=0.006:rimax=0.995:gimax=0.995:bimax=0.990",
        f"eq={preset_data['eq']}",
        "gradfun=strength=0.55:radius=12",
        f"unsharp={preset_data['unsharp']}",
        "format=yuv420p",
    ]
    if preset_data["vignette"]:
        filters.insert(-1, f"vignette={preset_data['vignette']}")
    return ",".join(filters)


def render_video(
    source: Path,
    output: Path,
    video_filter: str,
    *,
    ss: float | None = None,
    seconds: float | None = None,
    copy_audio: bool = False,
) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y"]
    if ss is not None:
        cmd.extend(["-ss", f"{ss:.3f}"])
    cmd.extend(["-i", str(source), "-vf", video_filter])
    if seconds is not None:
        cmd.extend(["-t", f"{seconds:.3f}"])
    cmd.extend(["-c:v", "libx264", "-preset", "veryfast", "-crf", "19"])
    if copy_audio:
        cmd.extend(["-c:a", "copy"])
    else:
        cmd.extend(["-c:a", "aac", "-b:a", "192k", "-af", AUDIO_ENHANCE_FILTER])
    cmd.extend(["-movflags", "+faststart", str(output)])
    run(cmd)


def frame(path: Path, source: Path, at: float) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    run(
        [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-ss",
            f"{at:.3f}",
            "-i",
            str(source),
            "-frames:v",
            "1",
            str(path),
        ]
    )


def write_review_html(path: Path, source: Path, output: Path, preview: Path, report: dict[str, Any]) -> None:
    html = f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>Dasheng 滤镜审核</title>
<style>
body {{ margin:0; padding:28px; font-family:-apple-system,BlinkMacSystemFont,"PingFang SC",sans-serif; background:#101010; color:#f5f5f5; }}
a {{ color:#86c9ff; }}
.meta {{ color:#bbb; line-height:1.7; margin:10px 0 22px; }}
.grid {{ display:grid; grid-template-columns:1fr 1fr; gap:18px; }}
.card {{ background:#1b1b1d; border:1px solid #333; border-radius:14px; padding:14px; }}
video {{ width:100%; max-height:72vh; border-radius:10px; background:#000; }}
@media (max-width: 900px) {{ .grid {{ grid-template-columns:1fr; }} }}
</style>
</head>
<body>
<h1>Dasheng 滤镜审核</h1>
<div class="meta">
预设：{report["preset_label"]} / 强度：{report["strength"]} / 轻拉瘦比例：{report["slim_factor"]}<br />
输出：<a href="{output.resolve().as_uri()}">{output.name}</a> · 预览：<a href="{preview.resolve().as_uri()}">{preview.name}</a>
</div>
<div class="grid">
  <section class="card"><h2>原片</h2><video controls src="{source.resolve().as_uri()}"></video></section>
  <section class="card"><h2>滤镜版</h2><video controls src="{output.resolve().as_uri()}"></video></section>
</div>
</body>
</html>
"""
    path.write_text(html, encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Apply open-source portrait/cinematic filters to a talking-head video")
    parser.add_argument("--input-video", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--preset", choices=sorted(PRESETS), default="warm_cinema")
    parser.add_argument("--strength", choices=["soft", "medium", "strong"], default="medium")
    parser.add_argument("--slim-factor", type=float, default=None)
    parser.add_argument("--preview-only", action="store_true")
    parser.add_argument("--preview-start", type=float, default=22.0)
    parser.add_argument("--preview-duration", type=float, default=15.0)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    source = Path(args.input_video).expanduser().resolve()
    out_dir = Path(args.output_dir).expanduser().resolve()
    if not source.exists():
        raise SystemExit(f"input video not found: {source}")
    probe = ffprobe(source)
    width, height = video_size(probe)
    video_filter = build_filter(width, height, args.preset, args.strength, args.slim_factor)
    preset_data = PRESETS[args.preset]["filters"][args.strength]
    slim_factor = args.slim_factor if args.slim_factor is not None else preset_data["slim_factor"]

    final_dir = out_dir / "final"
    preview_dir = out_dir / "preview"
    suffix = f"{args.preset}_{args.strength}"
    preview = preview_dir / f"{source.stem}_{suffix}_preview.mp4"
    output = final_dir / f"{source.stem}_{suffix}.mp4"
    render_video(
        source,
        preview,
        video_filter,
        ss=args.preview_start,
        seconds=args.preview_duration,
        copy_audio=True,
    )
    frame(preview_dir / "source_frame.jpg", source, args.preview_start + min(3.0, args.preview_duration / 2))
    frame(preview_dir / "filtered_frame.jpg", preview, min(3.0, args.preview_duration / 2))
    if not args.preview_only:
        render_video(source, output, video_filter)
    else:
        output = preview

    report = {
        "stage": "video_open_filter",
        "status": "rendered",
        "created_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "source_video": str(source),
        "source_duration_sec": round(duration(probe), 3),
        "preset": args.preset,
        "preset_label": PRESETS[args.preset]["label"],
        "strength": args.strength,
        "slim_factor": round(float(slim_factor), 4),
        "video_filter": video_filter,
        "audio_filter": None if args.preview_only else AUDIO_ENHANCE_FILTER,
        "preview_video": str(preview),
        "output_video": str(output),
        "source_frame": str(preview_dir / "source_frame.jpg"),
        "filtered_frame": str(preview_dir / "filtered_frame.jpg"),
        "review_html": str(out_dir / "review.html"),
        "notes": [
            "基于 FFmpeg 开源滤镜：scale/pad、hqdn3d、bilateral、colorbalance、colorlevels、eq、gradfun、unsharp、vignette。",
            "当前素材是侧脸远景，局部 FaceMesh 拉瘦风险高；本版采用轻微整体横向瘦身，避免人物和字幕局部漂移。",
        ],
    }
    write_json(out_dir / "filter_manifest.json", report)
    write_review_html(out_dir / "review.html", source, output, preview, report)
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
