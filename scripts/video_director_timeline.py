#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
import re
import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from video_driver_rules import (
    audio_for_beat,
    classify_beat,
    load_driver_rules,
    score_driver,
    talking_head_shot_for_beat,
    transition_for_beat,
    weighted_driver_score,
)

SRT_TIME_RE = re.compile(
    r"(?P<h>\d{2}):(?P<m>\d{2}):(?P<s>\d{2}),(?P<ms>\d{3})"
)
SENTENCE_END_RE = re.compile(r"[。！？!?；;]$")
DATA_RE = re.compile(r"[\d０-９]+|%|％|万亿|亿美元|人民币|指数|利率|IPO|Capex|GDP", re.I)


@dataclass
class Caption:
    start: float
    end: float
    text: str

    @property
    def duration(self) -> float:
        return max(0.0, self.end - self.start)


def run_ffprobe_duration(path: Path) -> float | None:
    if not path.exists():
        return None
    proc = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=nk=1:nw=1",
            str(path),
        ],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if proc.returncode != 0:
        return None
    try:
        return float(proc.stdout.strip())
    except ValueError:
        return None


def parse_srt_time(value: str) -> float:
    match = SRT_TIME_RE.fullmatch(value.strip())
    if not match:
        raise ValueError(f"invalid SRT time: {value}")
    return (
        int(match.group("h")) * 3600
        + int(match.group("m")) * 60
        + int(match.group("s"))
        + int(match.group("ms")) / 1000
    )


def load_srt(path: Path) -> list[Caption]:
    blocks = re.split(r"\n\s*\n", path.read_text(encoding="utf-8").strip())
    captions: list[Caption] = []
    for block in blocks:
        lines = [line.strip() for line in block.splitlines() if line.strip()]
        if len(lines) < 2 or "-->" not in lines[1]:
            continue
        start_raw, end_raw = [item.strip() for item in lines[1].split("-->", 1)]
        text = "".join(lines[2:]).strip()
        if text:
            captions.append(Caption(parse_srt_time(start_raw), parse_srt_time(end_raw), text))
    return captions


def load_captions_json(path: Path) -> list[Caption]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError("captions JSON must be a list")
    captions = []
    for item in payload:
        if not isinstance(item, dict):
            continue
        text = str(item.get("text") or "").strip()
        if not text:
            continue
        captions.append(Caption(float(item["start"]), float(item["end"]), text))
    return captions


def normalize_space(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def group_captions(captions: list[Caption], min_sec: float = 3.0, max_sec: float = 7.0) -> list[Caption]:
    groups: list[Caption] = []
    buf: list[Caption] = []

    def flush() -> None:
        nonlocal buf
        if not buf:
            return
        groups.append(
            Caption(
                start=buf[0].start,
                end=buf[-1].end,
                text=normalize_space("".join(item.text for item in buf)),
            )
        )
        buf = []

    for caption in captions:
        if not buf:
            buf.append(caption)
            continue
        projected = caption.end - buf[0].start
        current_text = "".join(item.text for item in buf)
        if projected > max_sec:
            flush()
        buf.append(caption)
        current_duration = buf[-1].end - buf[0].start
        current_text = "".join(item.text for item in buf)
        if current_duration >= min_sec and SENTENCE_END_RE.search(current_text):
            flush()
    flush()
    return coalesce_short_groups([item for item in groups if item.duration >= 0.25], min_sec=min(2.0, min_sec))


def coalesce_short_groups(groups: list[Caption], min_sec: float = 2.0) -> list[Caption]:
    if not groups:
        return []
    out: list[Caption] = []
    for group in groups:
        if out and group.duration < min_sec:
            prev = out.pop()
            out.append(Caption(prev.start, group.end, normalize_space(prev.text + group.text)))
        else:
            out.append(group)
    if len(out) >= 2 and out[-1].duration < min_sec:
        tail = out.pop()
        prev = out.pop()
        out.append(Caption(prev.start, tail.end, normalize_space(prev.text + tail.text)))
    return out


def has_data_signal(text: str) -> bool:
    return bool(DATA_RE.search(text))


def choose_shot(index: int, beat: Caption, seconds_since_anchor: float) -> str:
    beat_class = classify_beat(beat.text, index=index)
    scores = score_driver(
        beat.text,
        beat_class=beat_class,
        duration=beat.duration,
        seconds_since_speaker=seconds_since_anchor,
        index=index,
        lane="talking_head",
    )
    return talking_head_shot_for_beat(
        beat_class,
        scores,
        seconds_since_speaker=seconds_since_anchor,
        index=index,
    )


def camera_for_shot(shot: str, index: int) -> dict[str, float]:
    if shot in {"talking_head_full", "speaker_full", "speaker_anchor", "speaker_return"}:
        return {"scale": 1.0, "x": 0.0, "y": 0.0}
    if shot in {"talking_head_punch_in", "claim_closeup"}:
        return {"scale": 1.06 + (index % 2) * 0.02, "x": -0.02, "y": 0.0}
    if shot == "broll_with_pip":
        return {"scale": 1.0, "x": 0.0, "y": 0.0}
    return {"scale": 1.02, "x": 0.0, "y": 0.0}


def overlay_for_shot(shot: str, beat: Caption) -> dict[str, Any]:
    if shot in {"chart_or_data_card", "chart_card"}:
        return {
            "type": "real_data_chart_or_table",
            "required": True,
            "position": "right_top_safe_area",
            "source_hint": beat.text[:80],
        }
    if shot in {"document_or_news_zoom", "document_zoom"}:
        return {
            "type": "source_document_or_news_card",
            "required": True,
            "position": "right_side_safe_area",
            "source_hint": beat.text[:80],
        }
    if shot == "html_logic_overlay":
        return {
            "type": "logic_chain_overlay",
            "required": True,
            "position": "right_side_safe_area",
            "source_hint": beat.text[:80],
        }
    if shot == "broll_with_pip":
        return {
            "type": "broll_or_html_sticker",
            "required": True,
            "position": "main_area_with_speaker_pip",
            "source_hint": beat.text[:80],
        }
    return {
        "type": "outline_progress",
        "required": False,
        "position": "left_top_safe_area",
    }


def build_talking_head_timeline(
    captions: list[Caption],
    *,
    title: str,
    source_video: str | None = None,
    duration: float | None = None,
) -> dict[str, Any]:
    rules = load_driver_rules()
    beats = group_captions(captions)
    duration = duration or (max((caption.end for caption in captions), default=0.0))
    segments: list[dict[str, Any]] = []
    last_anchor_at = 0.0
    last_evidence_at = 0.0
    for index, beat in enumerate(beats, 1):
        seconds_since_speaker = beat.start - last_anchor_at
        seconds_since_evidence = beat.start - last_evidence_at
        beat_class = classify_beat(beat.text, index=index)
        driver_scores = score_driver(
            beat.text,
            beat_class=beat_class,
            duration=beat.duration,
            seconds_since_speaker=seconds_since_speaker,
            seconds_since_evidence=seconds_since_evidence,
            index=index,
            lane="talking_head",
        )
        shot = talking_head_shot_for_beat(
            beat_class,
            driver_scores,
            seconds_since_speaker=seconds_since_speaker,
            index=index,
        )
        if shot in {"speaker_anchor", "speaker_full", "speaker_return", "claim_closeup", "talking_head_full", "talking_head_punch_in"}:
            last_anchor_at = beat.start
        if beat_class in {"evidence_data", "evidence_document"} or shot in {"chart_card", "document_zoom", "html_logic_overlay"}:
            last_evidence_at = beat.start
        segments.append(
            {
                "id": f"beat_{index:03d}",
                "start": round(beat.start, 3),
                "end": round(beat.end, 3),
                "duration": round(beat.duration, 3),
                "caption": beat.text,
                "beat_class": beat_class,
                "driver_scores": driver_scores,
                "driver_score": weighted_driver_score(driver_scores, rules),
                "shot": shot,
                "camera": camera_for_shot(shot, index),
                "overlay": overlay_for_shot(shot, beat),
                "subtitle": {
                    "mode": "agent_proofread_srt",
                    "max_lines": 2,
                    "max_chars_per_line": 24,
                    "position": "near_source_video_bottom",
                },
                "transition": transition_for_beat(beat_class, lane="talking_head", duration=beat.duration),
                "audio": audio_for_beat(beat_class),
            }
        )
    return {
        "schema_version": "dasheng.talking_head_timeline.v1",
        "lane": "talking_head_video",
        "created_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "title": title,
        "source_video": source_video,
        "duration_sec": round(duration or 0.0, 3),
        "aspect": "9:16",
        "style_reference": {
            "target": "side-facing speaker plus evidence-first broll",
            "median_segment_sec": "2.5-4.0",
            "broll_or_evidence_ratio": "45%-65%",
            "speaker_return_interval_sec": "8-20",
        },
        "driver_rules_schema": rules.get("schema_version"),
        "director_state_machine": [
            "speaker_anchor",
            "claim_closeup",
            "evidence_fullscreen",
            "broll_with_pip",
            "document_zoom",
            "chart_card",
            "speaker_return",
        ],
        "safe_areas": {
            "speaker_crop": "bottom_half_or_side_anchor",
            "left_top": "outline_progress",
            "right_top": "charts_tables_documents",
            "bottom": "subtitle_only",
        },
        "segments": segments,
        "qc_targets": {
            "audio_lufs": -16,
            "subtitle_overlap": "forbidden",
            "developer_labels_in_final": "forbidden",
            "fake_data_charts": "forbidden",
        },
    }


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a Dasheng talking-head director timeline.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--captions-json")
    group.add_argument("--srt")
    parser.add_argument("--source-video")
    parser.add_argument("--duration", type=float)
    parser.add_argument("--title", default="未命名口播视频")
    parser.add_argument("--output", required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.captions_json:
        captions = load_captions_json(Path(args.captions_json).expanduser().resolve())
    else:
        captions = load_srt(Path(args.srt).expanduser().resolve())
    source_video = str(Path(args.source_video).expanduser().resolve()) if args.source_video else None
    duration = args.duration
    if duration is None and source_video:
        duration = run_ffprobe_duration(Path(source_video))
    timeline = build_talking_head_timeline(
        captions,
        title=args.title,
        source_video=source_video,
        duration=duration,
    )
    write_json(Path(args.output).expanduser().resolve(), timeline)
    print(json.dumps({"status": "ok", "output": str(Path(args.output).expanduser().resolve()), "segments": len(timeline["segments"])}, ensure_ascii=False))


if __name__ == "__main__":
    main()
