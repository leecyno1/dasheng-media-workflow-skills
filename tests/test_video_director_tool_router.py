import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from build_video_technical_site import build_html
from video_director_tool_router import (
    apply_routes_to_scene_plan,
    availability,
    build_stage_routes,
    load_unified_registry,
    route_capability,
)
from video_pipeline_governance import validate_artifact


def sample_scene_plan(lane="explainer_html_video"):
    return {
        "schema_version": "dasheng.video.scene_plan.v1",
        "lane": lane,
        "aspect": "1:1",
        "scenes": [
            {
                "id": "scene_001",
                "title": "估值数据图表开场",
                "start_sec": 0,
                "end_sec": 6,
                "duration_sec": 6,
                "beat_class": "evidence_data",
                "template_id": "frame-data-chart-nyt",
                "html_animation_behavior": "animated chart and kinetic title",
            }
        ],
    }


def test_unified_registry_covers_all_reserved_projects_and_installed_skills():
    registry = load_unified_registry()
    expected_installed = {
        "video-use", "freecut", "video-wrapper", "vox-director", "claude-shorts", "seedance2-skill",
        "remotion-video-skill", "remotion-video-toolkit", "cut-talking-head", "finish-talking-head",
        "gif-sticker-maker", "ian-xiaohei-illustrations", "video-frames", "reusable-footage-material",
        "remotion-best-practices", "animated-financial-display", "canvas-design", "algorithmic-art",
        "brand-guidelines", "animation-vocabulary", "apple-design", "emil-design-eng",
        "find-animation-opportunities", "improve-animations", "review-animations", "pick-ui-library",
        "brandkit", "high-end-visual-design", "image-to-code", "minimalist-ui", "design-taste-frontend",
        "web-animation-design", "guizang-social-card-skill",
    }
    reserved = json.loads((PROJECT_ROOT / "configs/external/reserved_projects.json").read_text(encoding="utf-8"))
    assert len(registry["projects"]) == len(reserved["projects"])
    assert len(registry["reserve_candidates"]) == 4
    assert len(registry["skills"]) >= 47
    assert len(registry["tools"]) >= 50
    assert expected_installed <= {skill["name"] for skill in registry["skills"]}
    assert len(registry["upstream_records"]) == 26
    assert all(project["capabilities"] for project in registry["projects"])
    assert all(skill["capabilities"] for skill in registry["skills"])


def test_explainer_scene_gets_primary_and_fallback_tool_stacks():
    routed, routing_plan = apply_routes_to_scene_plan(sample_scene_plan())
    route = routed["scenes"][0]["tool_routing"]

    assert "dynamic_chart" in route["required_capabilities"]
    assert "html_video" in route["required_capabilities"]
    assert route["primary_stack"]
    assert route["fallback_stack"]
    assert route["unresolved_capabilities"] == []
    assert routing_plan["registry_summary"]["tools"] == len(load_unified_registry()["tools"])
    assert routing_plan["registry_summary"]["skills"] == len(load_unified_registry()["skills"])
    assert routing_plan["registry_summary"]["projects"] == len(load_unified_registry()["projects"])
    assert routing_plan["registry_summary"]["reserve_candidates"] == 4
    assert routing_plan["registry_summary"]["rejected_projects"] == 13
    assert routing_plan["registry_summary"]["upstream_records"] == 26
    assert validate_artifact("scene_plan", routed) == []
    assert validate_artifact("tool_routing_plan", routing_plan) == []


def test_lane_stage_routes_do_not_force_talking_head_roughcut_on_explainer():
    registry = load_unified_registry()
    explainer = build_stage_routes(registry, lane="explainer_html_video")
    talking_head = build_stage_routes(registry, lane="talking_head_video")

    assert "roughcut" not in explainer
    assert "roughcut" in talking_head
    assert talking_head["roughcut"]["primary_stack"]


def test_api_key_and_reference_only_entries_cannot_be_primary(monkeypatch):
    monkeypatch.delenv("ATLASCLOUD_API_KEY", raising=False)
    registry = load_unified_registry()

    collage = route_capability(registry, "editorial_collage", lane="explainer_html_video")
    assert collage["primary"]
    assert collage["primary"]["name"] != "vox-director"
    assert any(item["name"] == "vox-director" for item in collage["blocked"])

    audio = route_capability(registry, "audio_mastering", lane="talking_head_video")
    assert audio["primary"]
    assert audio["primary"]["name"] == "dasheng_ffmpeg_toolkit"
    assert all(item["name"] != "talking-head-editor" for item in [audio["primary"], *audio["fallbacks"]])


def test_technical_site_contains_all_catalog_kinds_and_route_sections():
    registry = load_unified_registry()
    output = build_html(registry)

    assert "视频导演技术注册站" in output
    assert f"{len(registry['projects'])}</b>项目" in output
    assert 'data-kind="tool"' in output
    assert 'data-kind="skill"' in output
    assert 'data-kind="project"' in output
    assert 'data-kind="reserve"' in output
    assert "无头口播 / HTML 科普路由" in output
    assert "真人口播路由" in output


def test_project_capability_index_exactly_matches_project_registry():
    payload = json.loads((PROJECT_ROOT / "configs" / "external" / "reserved_projects.json").read_text(encoding="utf-8"))
    projects = {project["name"] for project in payload["projects"]}
    assert set(payload["project_capability_index"]) == projects


def test_reserve_candidates_are_visible_but_never_primary():
    registry = load_unified_registry()
    reserve_names = {item["name"] for item in registry["reserve_candidates"]}
    assert reserve_names == {"video-shotcraft", "gsap-skills", "impeccable", "video-autopilot-kit"}

    route = route_capability(registry, "gsap_motion", lane="explainer_html_video")
    assert route["primary"]
    assert route["primary"]["name"] != "gsap-skills"
    gsap_reserve = next(item for item in registry["reserve_candidates"] if item["name"] == "gsap-skills")
    assert availability(gsap_reserve)["state"] == "fallback"

    batch_route = route_capability(registry, "batch_video_production", lane="talking_head_video")
    assert any(item["name"] == "video-autopilot-kit" for item in batch_route["blocked"])
