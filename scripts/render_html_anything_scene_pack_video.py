#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont


WIDTH = 1080
HEIGHT = 1920
FPS = 30
DEFAULT_MMX_VOICE = "Chinese (Mandarin)_Radio_Host"
DEFAULT_MMX_MODEL = "speech-2.8-hd"
EVIDENCE_PARTS = {"data_chart", "financial_chart", "data_table", "article_image", "news_or_document", "source_citation"}
FORBIDDEN_VISIBLE_TERMS = [
    "content_part:",
    "template_id:",
    "template:",
    "slot:",
    "position:",
    "workflow:",
    "developer:",
    "data-director-policy",
    "data-motion-policy",
]


class RenderError(RuntimeError):
    pass


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def run(cmd: list[str]) -> None:
    proc = subprocess.run(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    if proc.returncode != 0:
        raise RenderError(proc.stderr or proc.stdout or "command failed")


def run_capture(cmd: list[str]) -> str:
    proc = subprocess.run(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    if proc.returncode != 0:
        raise RenderError(proc.stderr or proc.stdout or "command failed")
    return proc.stdout.strip()


def run_capture_combined(cmd: list[str]) -> str:
    proc = subprocess.run(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    if proc.returncode != 0:
        raise RenderError(proc.stderr or proc.stdout or "command failed")
    return "\n".join(part for part in [proc.stdout.strip(), proc.stderr.strip()] if part)


def find_chrome() -> str:
    candidates = [
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/Applications/Chromium.app/Contents/MacOS/Chromium",
        shutil.which("google-chrome"),
        shutil.which("chromium"),
        shutil.which("chromium-browser"),
    ]
    for item in candidates:
        if item and Path(item).exists():
            return str(item)
    raise RenderError("Chrome/Chromium not found; cannot screenshot HTML scenes.")


def file_url(path: Path) -> str:
    return path.resolve().as_uri()


def capture_scene(chrome: str, html_path: Path, output_png: Path) -> None:
    output_png.parent.mkdir(parents=True, exist_ok=True)
    run(
        [
            chrome,
            "--headless=new",
            "--disable-gpu",
            "--hide-scrollbars",
            "--no-first-run",
            "--no-default-browser-check",
            f"--window-size={WIDTH},{HEIGHT}",
            f"--screenshot={output_png}",
            file_url(html_path),
        ]
    )


def make_contact_sheet(manifest: dict[str, Any], png_dir: Path, output: Path, cols: int = 4) -> None:
    scenes = manifest.get("scenes") or []
    thumb_w = 270
    thumb_h = 480
    label_h = 72
    rows = (len(scenes) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * thumb_w, rows * (thumb_h + label_h)), (13, 17, 24))
    draw = ImageDraw.Draw(sheet)
    try:
        font = ImageFont.truetype("/System/Library/Fonts/STHeiti Medium.ttc", 18)
        small = ImageFont.truetype("/System/Library/Fonts/STHeiti Light.ttc", 14)
    except Exception:
        font = ImageFont.load_default()
        small = ImageFont.load_default()
    for idx, scene in enumerate(scenes):
        png = png_dir / f"{idx + 1:03d}.png"
        if not png.exists():
            continue
        thumb = Image.open(png).convert("RGB").resize((thumb_w, thumb_h))
        x = (idx % cols) * thumb_w
        y = (idx // cols) * (thumb_h + label_h)
        sheet.paste(thumb, (x, y))
        draw.rectangle((x, y + thumb_h, x + thumb_w, y + thumb_h + label_h), fill=(23, 29, 40))
        draw.text((x + 10, y + thumb_h + 8), f"{idx + 1:02d} {scene.get('content_part')}", fill=(245, 242, 233), font=font)
        draw.text((x + 10, y + thumb_h + 36), str(scene.get("template_id")), fill=(216, 170, 85), font=small)
    output.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(output, quality=92)


def make_concat_file(manifest: dict[str, Any], png_dir: Path, output: Path) -> None:
    lines: list[str] = []
    scenes = manifest.get("scenes") or []
    for idx, scene in enumerate(scenes, 1):
        png = png_dir / f"{idx:03d}.png"
        duration = float(scene.get("duration_sec") or 3)
        lines.append(f"file '{png}'")
        lines.append(f"duration {max(0.4, duration):.3f}")
    if scenes:
        lines.append(f"file '{png_dir / f'{len(scenes):03d}.png'}'")
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")


def render_silent_video(concat_file: Path, output_mp4: Path) -> None:
    output_mp4.parent.mkdir(parents=True, exist_ok=True)
    run(
        [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(concat_file),
            "-vf",
            f"fps={FPS},format=yuv420p",
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-crf",
            "20",
            "-movflags",
            "+faststart",
            str(output_mp4),
        ]
    )


def ffprobe_duration(path: Path) -> float:
    output = run_capture(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=nk=1:nw=1",
            str(path),
        ]
    )
    return float(output)


def ffmpeg_mean_volume(path: Path) -> float | None:
    try:
        output = run_capture_combined(
            [
                "ffmpeg",
                "-hide_banner",
                "-nostats",
                "-i",
                str(path),
                "-af",
                "volumedetect",
                "-f",
                "null",
                "-",
            ]
        )
    except RenderError:
        return None
    match = re.search(r"mean_volume:\s*(-?\d+(?:\.\d+)?)\s*dB", output)
    return float(match.group(1)) if match else None


def visible_text_from_html(path: Path) -> str:
    text = path.read_text(encoding="utf-8", errors="ignore")
    text = re.sub(r"<!--.*?-->", " ", text, flags=re.S)
    text = re.sub(r"<script\b.*?</script>", " ", text, flags=re.S | re.I)
    text = re.sub(r"<style\b.*?</style>", " ", text, flags=re.S | re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def scene_has_real_evidence(scene: dict[str, Any]) -> bool:
    part = str(scene.get("content_part") or "")
    if part not in EVIDENCE_PARTS and not str(scene.get("beat_class") or "").startswith("evidence"):
        return True
    variables = scene.get("variables") or {}
    if variables.get("table") or variables.get("rows") or variables.get("src") or variables.get("metrics"):
        return True
    text = " ".join(str(scene.get(key) or "") for key in ["title", "narration"])
    return bool(re.search(r"\d|%|万亿|亿美元|bp|IPO|VIX|纳指|美债|半导体|比特币", text, re.I))


def build_qc_report(
    manifest: dict[str, Any],
    *,
    output_dir: Path,
    silent_result: dict[str, Any],
    voice_result: dict[str, Any] | None,
) -> dict[str, Any]:
    scenes = manifest.get("scenes") or []
    failures: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []

    last_evidence_end = 0.0
    evidence_seen = False
    for scene in scenes:
        scene_id = scene.get("id")
        start = float(scene.get("start_sec") or 0)
        end = float(scene.get("end_sec") or start + float(scene.get("duration_sec") or 0))
        duration = float(scene.get("duration_sec") or max(0.0, end - start))
        part = str(scene.get("content_part") or "")
        beat = str(scene.get("beat_class") or "")
        motion = scene.get("motion_policy") or {}
        is_evidence = part in EVIDENCE_PARTS or beat.startswith("evidence")

        if is_evidence:
            evidence_seen = True
            if start - last_evidence_end > 40:
                failures.append(
                    {
                        "code": "evidence_gap_too_long",
                        "scene_id": scene_id,
                        "gap_sec": round(start - last_evidence_end, 3),
                        "message": "无真人科普线超过 40 秒没有证据/数据/资料画面。",
                    }
                )
            last_evidence_end = end
            if not scene_has_real_evidence(scene):
                failures.append(
                    {
                        "code": "evidence_without_real_data",
                        "scene_id": scene_id,
                        "content_part": part,
                        "message": "证据场景缺少来自文章表格、图片或明确数字的支撑。",
                    }
                )

        if duration > 12 and not motion:
            failures.append(
                {
                    "code": "long_scene_without_motion",
                    "scene_id": scene_id,
                    "duration_sec": round(duration, 3),
                    "message": "超过 12 秒的场景没有声明运动策略。",
                }
            )

        html_path = Path(str(scene.get("html") or ""))
        if html_path.exists():
            visible_text = visible_text_from_html(html_path).lower()
            for term in FORBIDDEN_VISIBLE_TERMS:
                if term.lower() in visible_text:
                    failures.append(
                        {
                            "code": "visible_workflow_label",
                            "scene_id": scene_id,
                            "term": term,
                            "message": "最终画面可见开发/流程标签。",
                        }
                    )
                    break

    transition_cards = [scene for scene in scenes if str(scene.get("content_part") or "") == "transition"]
    if len(transition_cards) > max(2, len(scenes) // 12):
        warnings.append(
            {
                "code": "too_many_standalone_transition_cards",
                "transition_count": len(transition_cards),
                "scene_count": len(scenes),
                "message": "独立转场卡偏多，建议改为场景间运动/声音转场，减少黑底空卡。",
            }
        )

    if not evidence_seen:
        warnings.append({"code": "no_evidence_scene", "message": "时间线没有识别到证据/数据/资料场景。"})

    audio_report = None
    final_video = Path((voice_result or silent_result).get("final_video") or silent_result.get("final_video"))
    if final_video.exists():
        try:
            measured_duration = ffprobe_duration(final_video)
        except RenderError:
            measured_duration = None
        mean_volume = ffmpeg_mean_volume(final_video) if voice_result else None
        audio_report = {
            "video": str(final_video.resolve()),
            "duration_sec": round(measured_duration, 3) if measured_duration is not None else None,
            "mean_volume_db": mean_volume,
            "target_lufs": -16 if voice_result else None,
        }
        if voice_result and mean_volume is not None and mean_volume < -28:
            warnings.append(
                {
                    "code": "voice_mean_volume_low",
                    "mean_volume_db": mean_volume,
                    "message": "音频平均音量偏低，建议检查 TTS 源或响度标准化。",
                }
            )
    if voice_result:
        planned_duration = float(silent_result.get("duration_sec") or 0)
        voiced_duration = float(voice_result.get("duration_sec") or (audio_report or {}).get("duration_sec") or 0)
        if planned_duration > 0 and voiced_duration / planned_duration > 1.25:
            warnings.append(
                {
                    "code": "voiceover_stretches_visual_timeline",
                    "planned_duration_sec": round(planned_duration, 3),
                    "voiceover_duration_sec": round(voiced_duration, 3),
                    "ratio": round(voiced_duration / planned_duration, 3),
                    "message": "逐场景 TTS 明显拉长视觉时间线，建议改为整段旁白主时间轴或提高语速并压缩长段。",
                }
            )

    report = {
        "schema_version": "dasheng.video_qc_report.v1",
        "status": "pass" if not failures else "fail",
        "scene_count": len(scenes),
        "failure_count": len(failures),
        "warning_count": len(warnings),
        "checks": {
            "visible_workflow_labels": "fail_on_visible_text",
            "fake_or_unsourced_evidence": "fail",
            "explainer_evidence_gap_sec": 40,
            "long_static_scene_sec": 12,
            "audio_volume": "warn_if_mean_volume_below_-28db",
            "voiceover_timeline_ratio": "warn_if_voiceover_exceeds_visual_by_25_percent",
        },
        "audio": audio_report,
        "failures": failures,
        "warnings": warnings,
    }
    (output_dir / "video_qc_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return report


def canonicalize_wav(source: Path, output: Path) -> None:
    run(
        [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-i",
            str(source),
            "-ac",
            "1",
            "-ar",
            "44100",
            str(output),
        ]
    )


def build_mmx_speech_command(
    text_file: Path,
    output: Path,
    *,
    model: str,
    voice: str,
    speed: float,
    language: str,
) -> list[str]:
    return [
        "mmx",
        "speech",
        "synthesize",
        "--text-file",
        str(text_file),
        "--out",
        str(output),
        "--model",
        model,
        "--voice",
        voice,
        "--speed",
        f"{speed:g}",
        "--format",
        "wav",
        "--sample-rate",
        "44100",
        "--channels",
        "1",
        "--language",
        language,
        "--quiet",
        "--non-interactive",
    ]


def synthesize_audio_with_mmx(
    text: str,
    output: Path,
    *,
    model: str,
    voice: str,
    speed: float,
    language: str,
) -> float:
    output.parent.mkdir(parents=True, exist_ok=True)
    text_file = output.with_suffix(".txt")
    raw = output.with_name(f"{output.stem}.mmx.raw.wav")
    text_file.write_text(text.strip() or "。", encoding="utf-8")
    run(build_mmx_speech_command(text_file, raw, model=model, voice=voice, speed=speed, language=language))
    canonicalize_wav(raw, output)
    raw.unlink(missing_ok=True)
    return ffprobe_duration(output)


def synthesize_audio_with_say(text: str, output: Path, *, voice: str, rate: int) -> float:
    output.parent.mkdir(parents=True, exist_ok=True)
    aiff = output.with_suffix(".aiff")
    run(["say", "-v", voice, "-r", str(rate), "-o", str(aiff), text])
    canonicalize_wav(aiff, output)
    aiff.unlink(missing_ok=True)
    return ffprobe_duration(output)


def synthesize_audio(
    text: str,
    output: Path,
    *,
    provider: str,
    voice: str,
    rate: int,
    mmx_model: str,
    mmx_speed: float,
    mmx_language: str,
) -> float:
    if provider == "mmx":
        return synthesize_audio_with_mmx(
            text,
            output,
            model=mmx_model,
            voice=voice,
            speed=mmx_speed,
            language=mmx_language,
        )
    if provider == "say":
        return synthesize_audio_with_say(text, output, voice=voice, rate=rate)
    raise RenderError(f"Unsupported voice provider: {provider}")


def render_voiced_segment(image: Path, audio: Path, duration: float, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    frames = max(1, int(duration * FPS))
    run(
        [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-loop",
            "1",
            "-i",
            str(image),
            "-i",
            str(audio),
            "-t",
            f"{duration:.3f}",
            "-vf",
            f"zoompan=z='min(zoom+0.00022,1.035)':d={frames}:s={WIDTH}x{HEIGHT}:fps={FPS},format=yuv420p",
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-crf",
            "20",
            "-c:a",
            "aac",
            "-b:a",
            "160k",
            "-shortest",
            str(output),
        ]
    )


def visual_filter_for_scene(scene: dict[str, Any], *, with_audio: bool, duration: float) -> str:
    frames = max(1, int(duration * FPS))
    state = str(scene.get("director_state") or "")
    transition = str(scene.get("transition_to_next") or "")
    beat = str(scene.get("beat_class") or "")
    if state == "evidence_scene" or beat.startswith("evidence"):
        zoom = "min(zoom+0.00012,1.018)"
    elif state == "logic_animation" or transition == "path_highlight":
        zoom = "min(zoom+0.00018,1.026)"
    elif state == "chapter_card" or transition in {"chapter_hit", "impact_cut"}:
        zoom = "min(zoom+0.00032,1.045)"
    elif state in {"recap_card", "outro"}:
        zoom = "min(zoom+0.0001,1.015)"
    else:
        zoom = "min(zoom+0.00022,1.032)"
    return f"zoompan=z='{zoom}':d={frames}:s={WIDTH}x{HEIGHT}:fps={FPS},format=yuv420p"


def render_segment_video(image: Path, output: Path, duration: float, scene: dict[str, Any], audio: Path | None = None) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "error",
        "-y",
        "-loop",
        "1",
        "-i",
        str(image),
    ]
    if audio:
        cmd.extend(["-i", str(audio)])
    cmd.extend(
        [
            "-t",
            f"{duration:.3f}",
            "-vf",
            visual_filter_for_scene(scene, with_audio=bool(audio), duration=duration),
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-crf",
            "20",
        ]
    )
    if audio:
        cmd.extend(["-c:a", "aac", "-b:a", "160k", "-shortest"])
    else:
        cmd.extend(["-an"])
    cmd.append(str(output))
    run(cmd)


def render_silent_segment(image: Path, duration: float, output: Path, scene: dict[str, Any]) -> None:
    render_segment_video(image, output, duration, scene)


def render_silent_video_from_scenes(manifest: dict[str, Any], png_dir: Path, output_mp4: Path, output_dir: Path) -> dict[str, Any]:
    segment_dir = output_dir / "silent_segments"
    videos: list[Path] = []
    scene_reports: list[dict[str, Any]] = []
    for idx, scene in enumerate(manifest.get("scenes") or [], 1):
        png = png_dir / f"{idx:03d}.png"
        duration = max(0.4, float(scene.get("duration_sec") or 3))
        mp4 = segment_dir / f"{idx:03d}.mp4"
        render_silent_segment(png, duration, mp4, scene)
        videos.append(mp4)
        scene_reports.append(
            {
                "id": scene.get("id"),
                "content_part": scene.get("content_part"),
                "beat_class": scene.get("beat_class"),
                "director_state": scene.get("director_state"),
                "transition_to_next": scene.get("transition_to_next"),
                "duration_sec": round(duration, 3),
                "video": str(mp4.resolve()),
            }
        )
    concat_videos(videos, output_mp4)
    return {
        "duration_sec": round(sum(item["duration_sec"] for item in scene_reports), 3),
        "final_video": str(output_mp4.resolve()),
        "scenes": scene_reports,
    }


def make_video_concat_file(videos: list[Path], output: Path) -> None:
    lines = ["ffconcat version 1.0"]
    for video in videos:
        escaped = str(video.resolve()).replace("'", "'\\''")
        lines.append(f"file '{escaped}'")
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")


def concat_videos(videos: list[Path], output: Path) -> None:
    concat_file = output.parent / "video_concat.ffconcat"
    make_video_concat_file(videos, concat_file)
    run(
        [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-safe",
            "0",
            "-f",
            "concat",
            "-i",
            str(concat_file),
            "-c",
            "copy",
            str(output),
        ]
    )


def normalize_audio_video(source: Path, output: Path) -> None:
    run(
        [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-i",
            str(source),
            "-c:v",
            "copy",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-af",
            "highpass=f=80,afftdn=nf=-25,dynaudnorm=f=150:g=15:p=0.95,loudnorm=I=-16:LRA=8:TP=-1.0,alimiter=limit=0.95",
            "-movflags",
            "+faststart",
            str(output),
        ]
    )


def format_srt_time(seconds: float) -> str:
    ms = int(round((seconds - math.floor(seconds)) * 1000))
    total = int(math.floor(seconds))
    if ms == 1000:
        total += 1
        ms = 0
    return f"{total // 3600:02d}:{(total % 3600) // 60:02d}:{total % 60:02d},{ms:03d}"


def write_srt(path: Path, scenes: list[dict[str, Any]], durations: list[float]) -> None:
    rows: list[str] = []
    cursor = 0.0
    for idx, (scene, duration) in enumerate(zip(scenes, durations), 1):
        start = cursor
        end = cursor + duration
        cursor = end
        text = str(scene.get("narration") or scene.get("title") or "").strip()
        rows.extend([str(idx), f"{format_srt_time(start)} --> {format_srt_time(end)}", text, ""])
    path.write_text("\n".join(rows), encoding="utf-8")


def scene_narration(scene: dict[str, Any]) -> str:
    return str(scene.get("narration") or scene.get("title") or "").strip()


def combined_narration_text(scenes: list[dict[str, Any]]) -> str:
    lines: list[str] = []
    for scene in scenes:
        text = scene_narration(scene)
        if not text:
            continue
        if text[-1] not in "。！？!?":
            text += "。"
        lines.append(text)
    return "\n".join(lines).strip() or "。"


def allocate_voice_durations(scenes: list[dict[str, Any]], total_duration: float, *, min_sec: float = 1.2) -> list[float]:
    if not scenes:
        return []
    weights = [max(6, len(scene_narration(scene))) for scene in scenes]
    total_weight = sum(weights) or len(scenes)
    raw = [total_duration * weight / total_weight for weight in weights]
    durations = [max(min_sec, item) for item in raw]
    overflow = sum(durations) - total_duration
    if overflow > 0:
        adjustable = [idx for idx, item in enumerate(durations) if item > min_sec]
        while overflow > 0.001 and adjustable:
            share = overflow / len(adjustable)
            next_adjustable = []
            for idx in adjustable:
                reduce_by = min(share, durations[idx] - min_sec)
                durations[idx] -= reduce_by
                overflow -= reduce_by
                if durations[idx] > min_sec + 0.001:
                    next_adjustable.append(idx)
            if len(next_adjustable) == len(adjustable):
                break
            adjustable = next_adjustable
    rounded = [round(max(0.4, item), 3) for item in durations]
    rounded[-1] = round(max(0.4, rounded[-1] + (round(total_duration, 3) - sum(rounded))), 3)
    return rounded


def mux_video_with_audio(video: Path, audio: Path, output: Path) -> None:
    run(
        [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-i",
            str(video),
            "-i",
            str(audio),
            "-map",
            "0:v:0",
            "-map",
            "1:a:0",
            "-c:v",
            "copy",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-shortest",
            "-movflags",
            "+faststart",
            str(output),
        ]
    )


def render_single_voice_video(
    manifest: dict[str, Any],
    png_dir: Path,
    output_dir: Path,
    *,
    voice_provider: str,
    voice: str,
    rate: int,
    mmx_model: str,
    mmx_speed: float,
    mmx_language: str,
) -> dict[str, Any]:
    if voice_provider == "mmx" and not shutil.which("mmx"):
        raise RenderError("MiniMax CLI `mmx` is required for production voiceover.")
    if voice_provider == "say" and not shutil.which("say"):
        raise RenderError("macOS say is required for fallback preview voiceover.")
    scenes = manifest.get("scenes") or []
    audio_dir = output_dir / "voice_audio"
    segment_dir = output_dir / "single_voice_segments"
    narration = combined_narration_text(scenes)
    voice_wav = audio_dir / "voiceover_single.wav"
    voice_duration = synthesize_audio(
        narration,
        voice_wav,
        provider=voice_provider,
        voice=voice,
        rate=rate,
        mmx_model=mmx_model,
        mmx_speed=mmx_speed,
        mmx_language=mmx_language,
    )
    durations = allocate_voice_durations(scenes, voice_duration)
    videos: list[Path] = []
    scene_reports: list[dict[str, Any]] = []
    for idx, (scene, duration) in enumerate(zip(scenes, durations), 1):
        png = png_dir / f"{idx:03d}.png"
        mp4 = segment_dir / f"{idx:03d}.mp4"
        render_segment_video(png, mp4, duration, scene)
        videos.append(mp4)
        scene_reports.append(
            {
                "id": scene.get("id"),
                "content_part": scene.get("content_part"),
                "beat_class": scene.get("beat_class"),
                "director_state": scene.get("director_state"),
                "template_id": scene.get("template_id"),
                "transition_to_next": scene.get("transition_to_next"),
                "audio_policy": scene.get("audio"),
                "duration_sec": round(duration, 3),
                "video": str(mp4.resolve()),
            }
        )
    raw_visual = output_dir / "talking_video_single_voice.visual.mp4"
    raw_muxed = output_dir / "talking_video_single_voice.raw.mp4"
    final_video = output_dir / "talking_video_single_voice.mp4"
    concat_videos(videos, raw_visual)
    mux_video_with_audio(raw_visual, voice_wav, raw_muxed)
    normalize_audio_video(raw_muxed, final_video)
    srt = output_dir / "talking_video_single_voice.srt"
    write_srt(srt, scenes, durations)
    script_path = output_dir / "voiceover_single_script.txt"
    script_path.write_text(narration + "\n", encoding="utf-8")
    return {
        "mode": "single",
        "provider": voice_provider,
        "voice": voice,
        "rate": rate if voice_provider == "say" else None,
        "mmx_model": mmx_model if voice_provider == "mmx" else None,
        "mmx_speed": mmx_speed if voice_provider == "mmx" else None,
        "mmx_language": mmx_language if voice_provider == "mmx" else None,
        "duration_sec": round(sum(durations), 3),
        "audio_duration_sec": round(voice_duration, 3),
        "raw_video": str(raw_muxed.resolve()),
        "final_video": str(final_video.resolve()),
        "subtitle_srt": str(srt.resolve()),
        "voiceover_audio": str(voice_wav.resolve()),
        "voiceover_script": str(script_path.resolve()),
        "scenes": scene_reports,
    }


def render_voiced_video(
    manifest: dict[str, Any],
    png_dir: Path,
    output_dir: Path,
    *,
    voice_provider: str,
    voice: str,
    rate: int,
    mmx_model: str,
    mmx_speed: float,
    mmx_language: str,
) -> dict[str, Any]:
    if voice_provider == "mmx" and not shutil.which("mmx"):
        raise RenderError("MiniMax CLI `mmx` is required for production voiceover.")
    if voice_provider == "say" and not shutil.which("say"):
        raise RenderError("macOS say is required for fallback preview voiceover.")
    scenes = manifest.get("scenes") or []
    audio_dir = output_dir / "voice_audio"
    segment_dir = output_dir / "voiced_segments"
    videos: list[Path] = []
    durations: list[float] = []
    scene_reports: list[dict[str, Any]] = []
    for idx, scene in enumerate(scenes, 1):
        png = png_dir / f"{idx:03d}.png"
        wav = audio_dir / f"{idx:03d}.wav"
        mp4 = segment_dir / f"{idx:03d}.mp4"
        text = str(scene.get("narration") or scene.get("title") or "")
        audio_duration = synthesize_audio(
            text,
            wav,
            provider=voice_provider,
            voice=voice,
            rate=rate,
            mmx_model=mmx_model,
            mmx_speed=mmx_speed,
            mmx_language=mmx_language,
        )
        duration = max(audio_duration + 0.25, 1.2)
        render_segment_video(png, mp4, duration, scene, audio=wav)
        videos.append(mp4)
        durations.append(duration)
        scene_reports.append(
            {
                "id": scene.get("id"),
                "content_part": scene.get("content_part"),
                "beat_class": scene.get("beat_class"),
                "director_state": scene.get("director_state"),
                "template_id": scene.get("template_id"),
                "transition_to_next": scene.get("transition_to_next"),
                "audio_policy": scene.get("audio"),
                "duration_sec": round(duration, 3),
                "audio": str(wav.resolve()),
                "video": str(mp4.resolve()),
            }
        )
    raw_video = output_dir / "talking_video_tts.raw.mp4"
    final_video = output_dir / "talking_video_tts.mp4"
    concat_videos(videos, raw_video)
    normalize_audio_video(raw_video, final_video)
    srt = output_dir / "talking_video_tts.srt"
    write_srt(srt, scenes, durations)
    return {
        "mode": "per_scene",
        "provider": voice_provider,
        "voice": voice,
        "rate": rate if voice_provider == "say" else None,
        "mmx_model": mmx_model if voice_provider == "mmx" else None,
        "mmx_speed": mmx_speed if voice_provider == "mmx" else None,
        "mmx_language": mmx_language if voice_provider == "mmx" else None,
        "duration_sec": round(sum(durations), 3),
        "raw_video": str(raw_video.resolve()),
        "final_video": str(final_video.resolve()),
        "subtitle_srt": str(srt.resolve()),
        "scenes": scene_reports,
    }


def render_pack(
    manifest_path: Path,
    output_dir: Path,
    *,
    limit: int | None = None,
    with_voice: bool = False,
    voice_provider: str = "mmx",
    voice: str = DEFAULT_MMX_VOICE,
    rate: int = 215,
    mmx_model: str = DEFAULT_MMX_MODEL,
    mmx_speed: float = 1.08,
    mmx_language: str = "Chinese",
    voice_mode: str = "per-scene",
) -> dict[str, Any]:
    manifest = load_json(manifest_path)
    scenes = manifest.get("scenes") or []
    if limit:
        scenes = scenes[:limit]
        manifest = {**manifest, "scenes": scenes, "scene_count": len(scenes)}
    chrome = find_chrome()
    output_dir.mkdir(parents=True, exist_ok=True)
    png_dir = output_dir / "frames_png"
    for idx, scene in enumerate(scenes, 1):
        capture_scene(chrome, Path(scene["html"]).expanduser().resolve(), png_dir / f"{idx:03d}.png")
    contact_sheet = output_dir / "contact_sheet.jpg"
    make_contact_sheet(manifest, png_dir, contact_sheet)
    video = output_dir / "visual_timeline_silent.mp4"
    silent_result = render_silent_video_from_scenes(manifest, png_dir, video, output_dir)
    voice_result = None
    if with_voice:
        if voice_mode == "single":
            voice_result = render_single_voice_video(
                manifest,
                png_dir,
                output_dir,
                voice_provider=voice_provider,
                voice=voice,
                rate=rate,
                mmx_model=mmx_model,
                mmx_speed=mmx_speed,
                mmx_language=mmx_language,
            )
        else:
            voice_result = render_voiced_video(
                manifest,
                png_dir,
                output_dir,
                voice_provider=voice_provider,
                voice=voice,
                rate=rate,
                mmx_model=mmx_model,
                mmx_speed=mmx_speed,
                mmx_language=mmx_language,
            )
    qc_report = build_qc_report(
        manifest,
        output_dir=output_dir,
        silent_result=silent_result,
        voice_result=voice_result,
    )
    result = {
        "schema_version": "dasheng.html_anything_scene_pack_render.v1",
        "source_manifest": str(manifest_path.resolve()),
        "scene_count": len(scenes),
        "frames_dir": str(png_dir.resolve()),
        "contact_sheet": str(contact_sheet.resolve()),
        "silent_video": str(video.resolve()),
        "silent_render": silent_result,
        "voiceover": voice_result,
        "qc_report": str((output_dir / "video_qc_report.json").resolve()),
        "qc_status": qc_report["status"],
        "director_usage": manifest.get("director_usage"),
        "beat_usage": manifest.get("beat_usage"),
        "transition_usage": manifest.get("transition_usage"),
        "note": "Silent visual timing preview unless --with-voice is set. Production voice defaults to MiniMax CLI.",
    }
    (output_dir / "render_report.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Screenshot HTML scene pack and stitch a silent visual timeline video.")
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--limit", type=int)
    parser.add_argument("--with-voice", action="store_true")
    parser.add_argument("--voice-mode", choices=["per-scene", "single"], default="per-scene")
    parser.add_argument("--voice-provider", choices=["mmx", "say"], default="mmx")
    parser.add_argument("--voice", default=DEFAULT_MMX_VOICE, help="MiniMax voice_id by default; macOS voice name when --voice-provider say.")
    parser.add_argument("--rate", type=int, default=215)
    parser.add_argument("--mmx-model", default=DEFAULT_MMX_MODEL)
    parser.add_argument("--mmx-speed", type=float, default=1.08)
    parser.add_argument("--mmx-language", default="Chinese")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    result = render_pack(
        Path(args.manifest).expanduser().resolve(),
        Path(args.output_dir).expanduser().resolve(),
        limit=args.limit,
        with_voice=args.with_voice,
        voice_provider=args.voice_provider,
        voice=args.voice,
        rate=args.rate,
        mmx_model=args.mmx_model,
        mmx_speed=args.mmx_speed,
        mmx_language=args.mmx_language,
        voice_mode=args.voice_mode,
    )
    print(json.dumps({"status": "ok", **result}, ensure_ascii=False))


if __name__ == "__main__":
    main()
