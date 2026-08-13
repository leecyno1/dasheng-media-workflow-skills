import json
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).parent.parent
PYTHON = sys.executable


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_base_draft(tmp_path: Path, *, topic_id: str = "topic-demo") -> tuple[Path, Path, Path]:
    draft = tmp_path / "draft.md"
    html = tmp_path / "draft.html"
    draft_manifest = tmp_path / "draft_manifest.json"
    draft.write_text("# 视频测试\n\n## 第一部分\n\n这是用于视频转写的正文，有数据、有判断。", encoding="utf-8")
    html.write_text(
        """
        <html><head><title>视频测试</title></head><body>
        <h1>视频测试</h1>
        <h2>01 第一部分</h2>
        <p>这是用于视频转写的正文，有数据、有判断。</p>
        <table><tr><th>指标</th><th>数值</th></tr><tr><td>变化</td><td>20%</td></tr></table>
        </body></html>
        """,
        encoding="utf-8",
    )
    write_json(
        draft_manifest,
        {
            "run_id": "run-video-director",
            "stage": "draft",
            "drafts": [
                {
                    "topic_id": topic_id,
                    "title": "视频测试",
                    "draft_file": str(draft),
                    "html_file": str(html),
                }
            ],
        },
    )
    write_json(
        tmp_path / "final_structure_snapshot.json",
        {
            "run_id": "run-video-director",
            "gate": "Final Structure Gate",
            "status": "approved",
            "topics": [{"topic_id": topic_id}],
        },
    )
    return draft_manifest, draft, html


def test_transwrite_explainer_lane_defaults_to_horizontal_remotion_master(tmp_path):
    draft_manifest, _, _ = write_base_draft(tmp_path)
    decision = tmp_path / "transwrite_decision.json"
    output_dir = tmp_path / "transwrite_out"
    write_json(
        decision,
        {
            "run_id": "run-video-director",
            "gate": "Transwrite Gate",
            "status": "approved",
            "topics": [
                {
                    "topic_id": "topic-demo",
                    "lanes": ["explainer_html_video"],
                    "explainer_html_video": {"audio": {"mode": "synthetic_audio"}},
                }
            ],
        },
    )

    proc = subprocess.run(
        [
            PYTHON,
            str(PROJECT_ROOT / "scripts/build_stage4_transwrite.py"),
            "--draft-manifest",
            str(draft_manifest),
            "--transwrite-decision",
            str(decision),
            "--output-dir",
            str(output_dir),
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert proc.returncode == 0, proc.stderr
    manifest = json.loads((output_dir / "transwrite_manifest.json").read_text(encoding="utf-8"))
    lane = manifest["topics"][0]["lanes"]["explainer_html_video"]
    director = lane["director_package"]
    assert lane["status"] == "pending_director_review"
    assert director["mode"] == "explainer_html_video"
    assert Path(director["scene_plan"]).exists()
    assert Path(director["review_html"]).exists()
    assert Path(director["checkpoint"]).exists()
    assert lane["final_artifacts"]["scene_plan"] == director["scene_plan"]
    assert lane["renderer"]["default"] == "remotion"
    assert lane["renderer"]["scene_renderer"] == "html-video"
    assert lane["renderer"]["aspect"] == "16:9"
    assert Path(lane["production_contract"]).exists()
    assert Path(lane["final_delivery_manifest_template"]).exists()
    assert "claim_evidence_gate" in lane["final_artifacts"]
    assert "final_delivery_manifest" in lane["final_artifacts"]


def test_legacy_no_human_talking_head_decision_migrates_to_explainer_lane(tmp_path):
    draft_manifest, _, _ = write_base_draft(tmp_path)
    decision = tmp_path / "transwrite_decision.json"
    output_dir = tmp_path / "transwrite_out"
    write_json(
        decision,
        {
            "run_id": "run-video-director",
            "gate": "Transwrite Gate",
            "status": "approved",
            "topics": [
                {
                    "topic_id": "topic-demo",
                    "lanes": ["talking_head_video"],
                    "talking_head_video": {"audio": {"mode": "synthetic_audio"}},
                }
            ],
        },
    )

    proc = subprocess.run(
        [
            PYTHON,
            str(PROJECT_ROOT / "scripts/build_stage4_transwrite.py"),
            "--draft-manifest",
            str(draft_manifest),
            "--transwrite-decision",
            str(decision),
            "--output-dir",
            str(output_dir),
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert proc.returncode == 0, proc.stderr
    manifest = json.loads((output_dir / "transwrite_manifest.json").read_text(encoding="utf-8"))
    lanes = manifest["topics"][0]["lanes"]
    assert "talking_head_video" not in lanes
    assert lanes["explainer_html_video"]["requested_lane"] == "talking_head_video"


def test_transwrite_vox_lane_stays_independent_and_horizontal(tmp_path):
    draft_manifest, _, _ = write_base_draft(tmp_path)
    decision = tmp_path / "transwrite_decision.json"
    output_dir = tmp_path / "transwrite_out"
    write_json(
        decision,
        {
            "run_id": "run-video-director",
            "gate": "Transwrite Gate",
            "status": "approved",
            "topics": [
                {
                    "topic_id": "topic-demo",
                    "lanes": ["vox_explainer_video"],
                    "vox_explainer_video": {
                        "central_question": "这组数据为什么变化？",
                        "audio": {"mode": "synthetic_audio"},
                    },
                }
            ],
        },
    )

    proc = subprocess.run(
        [
            PYTHON,
            str(PROJECT_ROOT / "scripts/build_stage4_transwrite.py"),
            "--draft-manifest",
            str(draft_manifest),
            "--transwrite-decision",
            str(decision),
            "--output-dir",
            str(output_dir),
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert proc.returncode == 0, proc.stderr
    manifest = json.loads((output_dir / "transwrite_manifest.json").read_text(encoding="utf-8"))
    lanes = manifest["topics"][0]["lanes"]
    assert set(lanes) == {"vox_explainer_video"}
    lane = lanes["vox_explainer_video"]
    scene_plan = json.loads(Path(lane["director_package"]["scene_plan"]).read_text(encoding="utf-8"))
    assert lane["requested_lane"] == "vox_explainer_video"
    assert lane["renderer"]["aspect"] == "16:9"
    assert lane["director_package"]["mode"] == "vox_explainer_video"
    assert scene_plan["lane"] == "vox_explainer_video"
    assert scene_plan["central_question"] == "这组数据为什么变化？"
    assert any(item["skill"] == "dasheng-video-vox" for item in lane["skill_invocations"])


def test_transwrite_video_lane_uses_talking_head_director_when_srt_exists(tmp_path):
    draft_manifest, _, _ = write_base_draft(tmp_path)
    srt = tmp_path / "proofread.srt"
    srt.write_text(
        """1
00:00:00,000 --> 00:00:02,000
开头先讲一个问题。

2
00:00:02,000 --> 00:00:05,000
这里有20%的变化，需要用图表解释。
""",
        encoding="utf-8",
    )
    decision = tmp_path / "transwrite_decision.json"
    output_dir = tmp_path / "transwrite_out"
    write_json(
        decision,
        {
            "run_id": "run-video-director",
            "gate": "Transwrite Gate",
            "status": "approved",
            "topics": [
                {
                    "topic_id": "topic-demo",
                    "lanes": ["talking_head_video"],
                    "talking_head_video": {
                        "srt": str(srt),
                        "audio": {"mode": "human_audio"},
                    },
                }
            ],
        },
    )

    proc = subprocess.run(
        [
            PYTHON,
            str(PROJECT_ROOT / "scripts/build_stage4_transwrite.py"),
            "--draft-manifest",
            str(draft_manifest),
            "--transwrite-decision",
            str(decision),
            "--output-dir",
            str(output_dir),
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert proc.returncode == 0, proc.stderr
    manifest = json.loads((output_dir / "transwrite_manifest.json").read_text(encoding="utf-8"))
    director = manifest["topics"][0]["lanes"]["talking_head_video"]["director_package"]
    scene_plan = json.loads(Path(director["scene_plan"]).read_text(encoding="utf-8"))
    assert director["mode"] == "talking_head_video"
    assert scene_plan["lane"] == "talking_head_video"
    assert scene_plan["scenes"][0]["speaker_state"]


def test_transwrite_builds_digital_human_presenter_source_package(tmp_path):
    draft_manifest, _, _ = write_base_draft(tmp_path)
    portrait = tmp_path / "portrait.png"
    audio = tmp_path / "minimax.wav"
    srt = tmp_path / "captions.srt"
    from PIL import Image

    Image.new("RGB", (768, 1024), (180, 160, 140)).save(portrait)
    subprocess.run(
        [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-f",
            "lavfi",
            "-i",
            "anullsrc=r=24000:cl=mono",
            "-t",
            "3",
            str(audio),
        ],
        check=True,
    )
    srt.write_text("1\n00:00:00,000 --> 00:00:03,000\n这是数字人口播。\n", encoding="utf-8")
    decision = tmp_path / "transwrite_decision.json"
    output_dir = tmp_path / "transwrite_out"
    write_json(
        decision,
        {
            "run_id": "run-video-director",
            "gate": "Transwrite Gate",
            "status": "approved",
            "topics": [
                {
                    "topic_id": "topic-demo",
                    "lanes": ["talking_head_video"],
                    "talking_head_video": {
                        "presenter_source": {
                            "kind": "digital_human",
                            "portrait": str(portrait),
                            "consent_status": "confirmed",
                        },
                        "audio": {"mode": "synthetic_audio", "file": str(audio)},
                        "srt": str(srt),
                    },
                }
            ],
        },
    )
    proc = subprocess.run(
        [
            PYTHON,
            str(PROJECT_ROOT / "scripts/build_stage4_transwrite.py"),
            "--draft-manifest",
            str(draft_manifest),
            "--transwrite-decision",
            str(decision),
            "--output-dir",
            str(output_dir),
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
    manifest = json.loads((output_dir / "transwrite_manifest.json").read_text(encoding="utf-8"))
    lane = manifest["topics"][0]["lanes"]["talking_head_video"]
    assert lane["status"] == "pending_presenter_source_review"
    assert lane["presenter_source"]["kind"] == "digital_human"
    assert Path(lane["presenter_source"]["job"]).is_file()
    assert Path(lane["presenter_source"]["manifest"]).is_file()
    assert lane["workflow_modes"]["audio_mode"] == "synthetic_audio"
    render_plan = json.loads(Path(lane["render_plan"]).read_text(encoding="utf-8"))
    assert render_plan["composition"]["presenter_video_audio_policy"] == "silent_visual_layer"
    assert any(item["skill"] == "dasheng-digital-human-talking-head" for item in lane["skill_invocations"])
    scene_plan = json.loads(Path(lane["director_package"]["scene_plan"]).read_text(encoding="utf-8"))
    assert scene_plan["presenter_source"]["kind"] == "digital_human"


def test_transwrite_blocks_digital_human_without_consent(tmp_path):
    draft_manifest, _, _ = write_base_draft(tmp_path)
    portrait = tmp_path / "portrait.png"
    audio = tmp_path / "minimax.wav"
    from PIL import Image

    Image.new("RGB", (768, 1024), (180, 160, 140)).save(portrait)
    subprocess.run(
        [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-f",
            "lavfi",
            "-i",
            "anullsrc=r=24000:cl=mono",
            "-t",
            "2",
            str(audio),
        ],
        check=True,
    )
    decision = tmp_path / "transwrite_decision.json"
    output_dir = tmp_path / "transwrite_out"
    write_json(
        decision,
        {
            "run_id": "run-video-director",
            "gate": "Transwrite Gate",
            "status": "approved",
            "topics": [
                {
                    "topic_id": "topic-demo",
                    "lanes": ["talking_head_video"],
                    "talking_head_video": {
                        "presenter_source": {"kind": "digital_human", "portrait": str(portrait)},
                        "audio": {"file": str(audio)},
                    },
                }
            ],
        },
    )
    proc = subprocess.run(
        [
            PYTHON,
            str(PROJECT_ROOT / "scripts/build_stage4_transwrite.py"),
            "--draft-manifest",
            str(draft_manifest),
            "--transwrite-decision",
            str(decision),
            "--output-dir",
            str(output_dir),
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
    manifest = json.loads((output_dir / "transwrite_manifest.json").read_text(encoding="utf-8"))
    lane = manifest["topics"][0]["lanes"]["talking_head_video"]
    assert lane["status"] == "blocked_missing_consent"
    assert lane["presenter_source"]["job"] is None
