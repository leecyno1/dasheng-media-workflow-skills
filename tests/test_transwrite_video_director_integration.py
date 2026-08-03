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


def test_transwrite_video_lane_builds_explainer_director_package(tmp_path):
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
    lane = manifest["topics"][0]["lanes"]["talking_head_video"]
    director = lane["director_package"]
    assert lane["status"] == "pending_director_review"
    assert director["mode"] == "explainer_html_video"
    assert Path(director["scene_plan"]).exists()
    assert Path(director["review_html"]).exists()
    assert Path(director["checkpoint"]).exists()
    assert lane["final_artifacts"]["scene_plan"] == director["scene_plan"]


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
