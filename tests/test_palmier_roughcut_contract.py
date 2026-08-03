import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from palmier_roughcut_contract import removed_frame_count, validate_plan, validate_result


def test_production_default_is_jianying_replay_and_palmier_is_disabled():
    config = json.loads(
        (PROJECT_ROOT / "skills" / "dasheng-video-roughcut" / "config.json").read_text(encoding="utf-8")
    )
    assert config["routes"]["default"] == "jianying_replay"
    assert config["routes"]["jianying"]["status"] == "production_default"
    assert config["routes"]["palmier_mcp"]["enabled"] is False


def _plan(tmp_name: str = "pilot.mp4"):
    return {
        "fps": 30,
        "output_path": str(Path.home() / "Desktop" / "自媒体创作" / "tests" / tmp_name),
        "delete_ranges": [
            {"start_seconds": 1.0, "end_seconds": 2.5, "reason": "restart", "reviewed": True},
            {"start_seconds": 4.0, "end_seconds": 5.0, "reason": "filler", "reviewed": True},
        ],
        "operations": [
            {"tool": "create_project"},
            {"tool": "import_media"},
            {"tool": "create_timeline"},
            {"tool": "ripple_delete_ranges"},
            {"tool": "apply_color"},
            {"tool": "export_video"},
        ],
    }


def test_removed_frame_count_is_exact_for_non_overlapping_ranges():
    assert removed_frame_count(_plan()["delete_ranges"], 30) == 75


def test_plan_blocks_unreliable_palmier_operations():
    plan = _plan()
    plan["operations"].append({"tool": "remove_words"})
    report = validate_plan(plan)
    assert report["valid"] is False
    assert any("remove_words" in item for item in report["errors"])


def test_result_requires_frame_and_audio_continuity_checks():
    plan = _plan()
    result = {
        "actual_removed_frames": 75,
        "output_path": plan["output_path"],
        "output_exists": True,
        "video_stream_ok": True,
        "audio_stream_ok": True,
        "audio_continuity_ok": True,
        "export_timeout": False,
        "project_reopen_ok": False,
    }
    report = validate_result(plan, result)
    assert report["route_status"] == "experimental_pass"
    assert report["editable_project_ready"] is False
    assert report["warnings"]

    result["audio_continuity_ok"] = False
    assert validate_result(plan, result)["route_status"] == "blocked"


def test_export_timeout_blocks_delivery():
    plan = _plan()
    result = {
        "actual_removed_frames": 75,
        "output_path": plan["output_path"],
        "output_exists": True,
        "video_stream_ok": True,
        "audio_stream_ok": True,
        "audio_continuity_ok": True,
        "export_timeout": True,
        "project_reopen_ok": True,
    }
    report = validate_result(plan, result)
    assert report["route_status"] == "blocked"
    assert any("timed out" in item for item in report["errors"])
