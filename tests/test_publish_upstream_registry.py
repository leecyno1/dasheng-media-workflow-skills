import json
import os
import subprocess
import sys
from pathlib import Path
from unittest.mock import Mock


PROJECT_ROOT = Path(__file__).parent.parent
PYTHON = sys.executable


def test_publish_upstream_registry_contains_bridge_dependencies():
    registry_path = PROJECT_ROOT / "configs" / "publish" / "upstream_repos.json"
    payload = json.loads(registry_path.read_text(encoding="utf-8"))
    repos = {row["name"]: row for row in payload["repositories"]}

    assert repos["all-in-one"]["repo"] == "https://github.com/cv-cat/All-IN-ONE.git"
    assert "dasheng-xhs-publish-bridge" in repos["all-in-one"]["used_by_skills"]
    assert repos["xhs-skills"]["repo"] == "https://github.com/cv-cat/XhsSkills.git"
    assert repos["spider-xhs"]["repo"] == "https://github.com/cv-cat/Spider_XHS.git"
    assert repos["xiaohongshu-mcp"]["repo"] == "https://github.com/xpzouying/xiaohongshu-mcp.git"
    assert repos["rednote-mcp"]["repo"] == "https://github.com/TimeCyber/mcp-xiaohongshu.git"
    assert repos["xhs-downloader"]["repo"] == "https://github.com/JoeanAmier/XHS-Downloader.git"
    assert repos["social-auto-upload"]["repo"] == "https://github.com/dreammis/social-auto-upload.git"
    assert "social-auto-upload-bridge" in repos["social-auto-upload"]["used_by_skills"]
    assert repos["biliup-rs"]["repo"] == "https://github.com/biliup/biliup-rs.git"
    assert "bilibili-upload-bridge" in repos["biliup-rs"]["used_by_skills"]

    for row in repos.values():
        assert row["version_locked"] is False


def test_check_publish_upstreams_lists_selected_repo_without_remote():
    proc = subprocess.run(
        [
            PYTHON,
            str(PROJECT_ROOT / "scripts" / "check_publish_upstreams.py"),
            "--name",
            "social-auto-upload",
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert proc.returncode == 0, proc.stderr
    payload = json.loads(proc.stdout)
    assert payload["check_remote"] is False
    assert payload["repositories"][0]["name"] == "social-auto-upload"
    assert payload["repositories"][0]["repo"] == "https://github.com/dreammis/social-auto-upload.git"


def write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def sample_xhs_execution_request(tmp: Path) -> Path:
    video = tmp / "video.mp4"
    video.write_bytes(b"fake mp4")
    request = {
        "schema_version": "1.0",
        "topic_id": "topic-demo",
        "title": "小红书执行准备测试",
        "channel": "xiaohongshu_video",
        "platform": "xiaohongshu",
        "status": "ready_for_user_confirmation",
        "executor_skill": "dasheng-xhs-publish-bridge",
        "execution_mode": "api_first_with_browser_fallback",
        "inputs": {
            "artifacts": {"video": str(video)},
            "publish_metadata": {"title": "小红书执行准备测试", "tags": ["AI"]},
            "browser_profile": {"open_command": "python3 scripts/open_publish_browser.py xiaohongshu_video"},
        },
        "route_priority": [
            {"route": "all-in-one", "type": "api_first_cli"},
            {"route": "xhs-skills-spider-xhs", "type": "api_first_skill"},
            {"route": "xiaohongshu-mcp", "type": "mcp_fallback"},
            {"route": "rednote-mcp", "type": "mcp_fallback"},
            {
                "route": "browser-profile",
                "type": "browser_confirm_fallback",
                "open_command": "python3 scripts/open_publish_browser.py xiaohongshu_video",
            },
        ],
    }
    request_path = tmp / "execution_request.json"
    write_json(request_path, request)
    return request_path


def test_prepare_xhs_publish_execution_falls_back_to_browser_profile(tmp_path):
    request_path = sample_xhs_execution_request(tmp_path)
    env = {
        **os.environ,
        "ALL_IN_ONE_ROOT": str(tmp_path / "missing-all-in-one"),
        "XHS_SKILLS_ROOT": str(tmp_path / "missing-xhs-skills"),
        "SPIDER_XHS_ROOT": str(tmp_path / "missing-spider-xhs"),
        "XIAOHONGSHU_MCP_ROOT": str(tmp_path / "missing-xiaohongshu-mcp"),
        "REDNOTE_MCP_ROOT": str(tmp_path / "missing-rednote-mcp"),
        "PATH": "/usr/bin:/bin",
    }
    proc = subprocess.run(
        [
            PYTHON,
            str(PROJECT_ROOT / "scripts" / "prepare_xhs_publish_execution.py"),
            "--execution-request",
            str(request_path),
        ],
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )

    assert proc.returncode == 0, proc.stderr
    payload = json.loads(proc.stdout)
    assert payload["status"] == "ready_for_user_confirmation"
    assert payload["selected_route"] == "browser-profile"
    assert payload["will_not_publish"] is True
    assert payload["requires_user_confirmation"] is True
    assert payload["route_checks"][0]["reason"] == "missing_all_in_one"
    assert payload["route_checks"][1]["reason"] == "missing_xhs_skills_or_spider_xhs"


def test_prepare_xhs_publish_execution_prefers_all_in_one_when_root_exists(tmp_path):
    request_path = sample_xhs_execution_request(tmp_path)
    all_in_one_root = tmp_path / "All-IN-ONE"
    all_in_one_root.mkdir()
    env = {
        **os.environ,
        "ALL_IN_ONE_ROOT": str(all_in_one_root),
        "PATH": "/usr/bin:/bin",
    }
    output_path = tmp_path / "xhs_execution_plan.json"
    proc = subprocess.run(
        [
            PYTHON,
            str(PROJECT_ROOT / "scripts" / "prepare_xhs_publish_execution.py"),
            "--execution-request",
            str(request_path),
            "--output",
            str(output_path),
        ],
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )

    assert proc.returncode == 0, proc.stderr
    payload = json.loads(proc.stdout)
    assert payload["selected_route"] == "all-in-one"
    assert payload["route_checks"][0]["reason"] == "upstream_root_found"
    assert any("aione xhs creator post-note" in command for command in payload["prepared_commands"])
    assert payload["confirmed_executor_command"] is None
    assert payload["confirm_execute_supported"] is False
    assert output_path.exists()


def sample_execution_request(tmp: Path, *, channel: str, platform: str, routes: list[dict]) -> Path:
    request = {
        "schema_version": "1.0",
        "topic_id": "topic-demo",
        "title": f"{channel} 执行准备测试",
        "channel": channel,
        "platform": platform,
        "status": "ready_for_user_confirmation",
        "executor_skill": routes[0]["route"],
        "execution_mode": routes[0].get("type"),
        "requires_user_confirmation": True,
        "channel_pack": str(tmp / "channel_pack.json"),
        "inputs": {
            "artifacts": {},
            "publish_metadata": {"title": f"{channel} 执行准备测试"},
            "browser_profile": {"open_command": f"python3 scripts/open_publish_browser.py {channel}"},
        },
        "route_priority": routes,
    }
    request_path = tmp / f"{channel}_execution_request.json"
    write_json(request_path, request)
    return request_path


def test_prepare_publish_execution_selects_local_wechat_skill(tmp_path):
    request_path = sample_execution_request(
        tmp_path,
        channel="wechat_article",
        platform="wechat",
        routes=[
            {"route": "baoyu-post-to-wechat", "type": "skill_draft_push"},
            {"route": "browser-profile", "type": "browser_confirm_fallback", "open_command": "python3 scripts/open_publish_browser.py wechat_article"},
        ],
    )
    proc = subprocess.run(
        [
            PYTHON,
            str(PROJECT_ROOT / "scripts" / "prepare_publish_execution.py"),
            "--execution-request",
            str(request_path),
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert proc.returncode == 0, proc.stderr
    payload = json.loads(proc.stdout)
    assert payload["platform"] == "wechat"
    assert payload["selected_route"] == "baoyu-post-to-wechat"
    assert payload["will_not_publish"] is True
    assert any("build_publish_payload.py" in command for command in payload["prepared_commands"])
    assert "execute_publish_request.py" in payload["safe_executor_command"]
    assert "--confirm-execute" not in payload["safe_executor_command"]
    assert "--confirm-execute" in payload["confirmed_executor_command"]


def test_prepare_publish_execution_douyin_falls_back_to_browser_when_skill_missing(tmp_path):
    request_path = sample_execution_request(
        tmp_path,
        channel="douyin_video",
        platform="douyin",
        routes=[
            {"route": "douyin-upload-skill", "type": "skill_or_api_upload"},
            {"route": "browser-profile", "type": "browser_confirm_fallback", "open_command": "python3 scripts/open_publish_browser.py douyin_video"},
        ],
    )
    proc = subprocess.run(
        [
            PYTHON,
            str(PROJECT_ROOT / "scripts" / "prepare_publish_execution.py"),
            "--execution-request",
            str(request_path),
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert proc.returncode == 0, proc.stderr
    payload = json.loads(proc.stdout)
    assert payload["platform"] == "douyin"
    assert payload["selected_route"] == "browser-profile"
    assert payload["requires_user_confirmation"] is True


def test_prepare_publish_execution_bilibili_falls_back_to_manual_package(tmp_path):
    channel_pack = tmp_path / "channel_pack.json"
    write_json(channel_pack, {"channel": "bilibili_video"})
    request_path = sample_execution_request(
        tmp_path,
        channel="bilibili_video",
        platform="bilibili",
        routes=[
            {"route": "biliup-rs", "type": "external_cli"},
            {"route": "manual-package", "type": "manual_package"},
        ],
    )
    proc = subprocess.run(
        [
            PYTHON,
            str(PROJECT_ROOT / "scripts" / "prepare_publish_execution.py"),
            "--execution-request",
            str(request_path),
        ],
        capture_output=True,
        text=True,
        check=False,
        env={**os.environ, "BILIUP_RS_ROOT": str(tmp_path / "missing-biliup"), "PATH": "/usr/bin:/bin"},
    )

    assert proc.returncode == 0, proc.stderr
    payload = json.loads(proc.stdout)
    assert payload["platform"] == "bilibili"
    assert payload["selected_route"] == "manual-package"
    assert payload["prepared_commands"] == ["open channel_pack directory and upload manually"]
    assert payload["confirmed_executor_command"] is None
    assert payload["confirm_execute_supported"] is False


def sample_video_channel_pack(tmp: Path, *, channel: str = "bilibili_video") -> Path:
    video = tmp / "final.mp4"
    subtitle = tmp / "final.srt"
    cover = tmp / "cover.jpg"
    video.write_bytes(b"fake mp4")
    subtitle.write_text("1\n00:00:00,000 --> 00:00:01,000\n测试\n", encoding="utf-8")
    cover.write_bytes(b"fake jpg")
    pack = {
        "topic_id": "topic-demo",
        "title": "视频上传包测试",
        "channel": channel,
        "status": "ready_for_execution",
        "artifact_hint": {"video": str(video), "video_srt": str(subtitle)},
        "publish_metadata": {
            "title": "视频上传包测试",
            "summary": "用于验证外部上传器配置生成。",
            "tags": ["AI", "财经"],
            "cover": str(cover),
        },
    }
    pack_path = tmp / "channel_pack.json"
    write_json(pack_path, pack)
    return pack_path


def test_build_video_upload_package_creates_bilibili_and_social_payloads(tmp_path):
    pack_path = sample_video_channel_pack(tmp_path, channel="bilibili_video")
    proc = subprocess.run(
        [
            PYTHON,
            str(PROJECT_ROOT / "scripts" / "build_video_upload_package.py"),
            "--channel-pack",
            str(pack_path),
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert proc.returncode == 0, proc.stderr
    payload = json.loads(proc.stdout)
    assert payload["status"] == "ready"
    social_path = Path(payload["outputs"]["social_auto_upload_request"])
    bili_path = Path(payload["outputs"]["bilibili_submission"])
    assert social_path.exists()
    assert bili_path.exists()

    social = json.loads(social_path.read_text(encoding="utf-8"))
    bili = json.loads(bili_path.read_text(encoding="utf-8"))
    assert social["platform"] == "bilibili"
    assert social["upload"]["auto_publish"] is False
    assert bili["submission"]["title"] == "视频上传包测试"
    assert bili["submission"]["video"].endswith("final.mp4")


def test_build_publish_payload_creates_wechat_executor_payload(tmp_path):
    html = tmp_path / "wechat.html"
    html.write_text("<html><body>正文</body></html>", encoding="utf-8")
    pack_path = tmp_path / "channel_pack.json"
    write_json(
        pack_path,
        {
            "topic_id": "topic-demo",
            "title": "公众号 payload 测试",
            "channel": "wechat_article",
            "executor_skill": "baoyu-post-to-wechat",
            "artifact_hint": {"wechat_html": str(html)},
            "publish_metadata": {"title": "公众号 payload 测试", "summary": "摘要"},
        },
    )
    proc = subprocess.run(
        [
            PYTHON,
            str(PROJECT_ROOT / "scripts" / "build_publish_payload.py"),
            "--channel-pack",
            str(pack_path),
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert proc.returncode == 0, proc.stderr
    report = json.loads(proc.stdout)
    payload_path = Path(report["publish_payload"])
    payload = json.loads(payload_path.read_text(encoding="utf-8"))
    assert report["status"] == "ready_for_executor"
    assert payload["will_not_publish"] is True
    assert payload["payload"]["skill"] == "baoyu-post-to-wechat"
    assert payload["payload"]["content_html"] == str(html.resolve())
    assert payload["payload"]["result_writeback"]["command"] == "python3 scripts/record_publish_result.py"


def test_build_publish_payload_creates_video_executor_payload(tmp_path):
    pack_path = sample_video_channel_pack(tmp_path, channel="douyin_video")
    proc = subprocess.run(
        [
            PYTHON,
            str(PROJECT_ROOT / "scripts" / "build_publish_payload.py"),
            "--channel-pack",
            str(pack_path),
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert proc.returncode == 0, proc.stderr
    report = json.loads(proc.stdout)
    payload = json.loads(Path(report["publish_payload"]).read_text(encoding="utf-8"))
    assert payload["status"] == "ready_for_executor"
    assert payload["payload"]["channel"] == "douyin_video"
    assert payload["payload"]["video"].endswith("final.mp4")
    assert payload["payload"]["auto_publish"] is False


def test_prepare_publish_execution_social_auto_upload_commands_include_converter(tmp_path):
    pack_path = sample_video_channel_pack(tmp_path, channel="douyin_video")
    social_root = tmp_path / "social-auto-upload"
    social_root.mkdir()
    request_path = sample_execution_request(
        tmp_path,
        channel="douyin_video",
        platform="douyin",
        routes=[
            {"route": "social-auto-upload", "type": "external_uploader_fallback"},
            {"route": "manual-package", "type": "manual_package"},
        ],
    )
    request = json.loads(request_path.read_text(encoding="utf-8"))
    request["channel_pack"] = str(pack_path)
    write_json(request_path, request)
    proc = subprocess.run(
        [
            PYTHON,
            str(PROJECT_ROOT / "scripts" / "prepare_publish_execution.py"),
            "--execution-request",
            str(request_path),
        ],
        capture_output=True,
        text=True,
        check=False,
        env={**os.environ, "SOCIAL_AUTO_UPLOAD_ROOT": str(social_root), "PATH": "/usr/bin:/bin"},
    )

    assert proc.returncode == 0, proc.stderr
    payload = json.loads(proc.stdout)
    assert payload["selected_route"] == "social-auto-upload"
    assert any("build_video_upload_package.py" in command for command in payload["prepared_commands"])
    assert payload["confirmed_executor_command"] is None
    assert payload["confirm_execute_supported"] is False


def test_publish_doctor_checks_selected_channels_without_publishing(tmp_path):
    output_json = tmp_path / "publish_doctor.json"
    output_md = tmp_path / "publish_doctor.md"
    proc = subprocess.run(
        [
            PYTHON,
            str(PROJECT_ROOT / "scripts" / "publish_doctor.py"),
            "--channel",
            "wechat_article,douyin_video",
            "--output-json",
            str(output_json),
            "--output-md",
            str(output_md),
        ],
        capture_output=True,
        text=True,
        check=False,
        env={**os.environ, "SOCIAL_AUTO_UPLOAD_ROOT": str(tmp_path / "missing-social-auto-upload"), "PATH": "/usr/bin:/bin"},
    )

    assert proc.returncode == 0, proc.stderr
    payload = json.loads(proc.stdout)
    assert payload["mode"] == "publish_doctor"
    assert payload["will_not_publish"] is True
    assert payload["safety"]["does_not_read_cookies"] is True
    assert payload["safety"]["does_not_open_browser"] is True
    assert {channel["channel"] for channel in payload["channels"]} == {"wechat_article", "douyin_video"}
    assert output_json.exists()
    assert output_md.exists()
    assert "不触发真实发布" in output_md.read_text(encoding="utf-8")


def test_publish_doctor_xhs_reports_api_first_missing_dependencies(tmp_path):
    proc = subprocess.run(
        [
            PYTHON,
            str(PROJECT_ROOT / "scripts" / "publish_doctor.py"),
            "--channel",
            "xiaohongshu_video",
        ],
        capture_output=True,
        text=True,
        check=False,
        env={
            **os.environ,
            "ALL_IN_ONE_ROOT": str(tmp_path / "missing-all-in-one"),
            "XHS_SKILLS_ROOT": str(tmp_path / "missing-xhs-skills"),
            "SPIDER_XHS_ROOT": str(tmp_path / "missing-spider-xhs"),
            "XIAOHONGSHU_MCP_ROOT": str(tmp_path / "missing-xiaohongshu-mcp"),
            "REDNOTE_MCP_ROOT": str(tmp_path / "missing-rednote-mcp"),
            "PATH": "/usr/bin:/bin",
        },
    )

    assert proc.returncode == 0, proc.stderr
    payload = json.loads(proc.stdout)
    route_reasons = {check["route"]: check["reason"] for check in payload["channels"][0]["route_checks"]}
    assert route_reasons["all-in-one"] == "missing_all_in_one"
    assert route_reasons["xhs-skills-spider-xhs"] == "missing_xhs_skills_or_spider_xhs"
    assert route_reasons["xiaohongshu-mcp"] == "missing_xiaohongshu_mcp_root"
    assert route_reasons["rednote-mcp"] == "missing_rednote_mcp_root"
    assert payload["channels"][0]["selected_route"] == "browser-profile"


def test_publish_doctor_lists_multiple_browser_profiles_for_platform(tmp_path):
    proc = subprocess.run(
        [
            PYTHON,
            str(PROJECT_ROOT / "scripts" / "publish_doctor.py"),
            "--channel",
            "xiaohongshu_video",
        ],
        capture_output=True,
        text=True,
        check=False,
        env={**os.environ, "PATH": "/usr/bin:/bin"},
    )

    assert proc.returncode == 0, proc.stderr
    payload = json.loads(proc.stdout)
    channel = payload["channels"][0]
    assert "xiaohongshu_video" in channel["available_browser_profiles"]
    assert "xiaohongshu_video_2" in channel["available_browser_profiles"]
    assert channel["browser_profile"]["profile_key"] == "xiaohongshu_video"


def test_mainline_doctor_publish_routes_to_publish_doctor(tmp_path):
    output_md = tmp_path / "publish_doctor.md"
    proc = subprocess.run(
        [
            PYTHON,
            str(PROJECT_ROOT / "scripts" / "run_mainline_stage.py"),
            "doctor",
            "--publish",
            "--channel",
            "bilibili_video",
            "--output-md",
            str(output_md),
        ],
        capture_output=True,
        text=True,
        check=False,
        env={**os.environ, "BILIUP_RS_ROOT": str(tmp_path / "missing-biliup-rs"), "PATH": "/usr/bin:/bin"},
    )

    assert proc.returncode == 0, proc.stderr
    payload = json.loads(proc.stdout)
    assert payload["mode"] == "publish_doctor"
    assert payload["channels"][0]["channel"] == "bilibili_video"
    assert payload["channels"][0]["will_not_publish"] is True
    assert output_md.exists()


def test_publish_contract_docs_include_guard_and_strict_postmortem_terms():
    stage_contract = (PROJECT_ROOT / "skills" / "dasheng-media-sop" / "references" / "stage-contract.md").read_text(encoding="utf-8")
    api_reference = (PROJECT_ROOT / "docs" / "API_REFERENCE.md").read_text(encoding="utf-8")

    for required in [
        "publish_guard_report.json",
        "publish_manifest.publish_guard",
        "draft_url",
        "platform_url",
        "--require-publish-guard",
    ]:
        assert required in stage_contract
        assert required in api_reference

    assert "--verification-status verified" in api_reference


def sample_publish_manifest_for_guard(tmp: Path, *, verified: bool = True) -> Path:
    publish_root = tmp / "publish_out"
    publish_root.mkdir(parents=True, exist_ok=True)
    wechat_result_file = publish_root / "channel_packs" / "topic-demo" / "wechat_article" / "publish_result.json"
    xhs_result_file = publish_root / "channel_packs" / "topic-demo" / "xiaohongshu_video" / "publish_result.json"
    wechat_pack = {
        "topic_id": "topic-demo",
        "title": "批次验收测试",
        "channel": "wechat_article",
        "platform": "wechat",
        "status": "ready_for_execution",
    }
    xhs_pack = {
        "topic_id": "topic-demo",
        "title": "批次验收测试",
        "channel": "xiaohongshu_video",
        "platform": "xiaohongshu",
        "status": "ready_for_execution",
    }
    results = [
        {
            "topic_id": "topic-demo",
            "title": "批次验收测试",
            "channel": "wechat_article",
            "platform": "wechat",
            "success": True,
            "status": "draft",
            "draft_id": "draft_guard_001",
            "draft_url": "https://mp.weixin.qq.com/cgi-bin/appmsg?t=media/appmsg_edit&appmsgid=draft_guard_001",
            "verification_status": "verified",
            "result_file": str(wechat_result_file),
        },
        {
            "topic_id": "topic-demo",
            "title": "批次验收测试",
            "channel": "xiaohongshu_video",
            "platform": "xiaohongshu",
            "success": True,
            "status": "published",
            "platform_url": "https://www.xiaohongshu.com/explore/guard001",
            "verification_status": "verified" if verified else "needs_manual_verification",
            "result_file": str(xhs_result_file),
        },
    ]
    manifest = {
        "run_id": "run-publish-guard",
        "stage": "publish",
        "status": "completed_with_mixed_status" if verified else "needs_manual_verification",
        "channel_packs": [wechat_pack, xhs_pack],
        "publish_results": results,
        "publish_summary": {
            "status": "completed_with_mixed_status" if verified else "needs_manual_verification",
            "total_channels": 2,
            "recorded_count": 2,
            "pending_count": 0,
            "failed_count": 0,
            "draft_count": 1,
            "published_count": 1 if verified else 0,
            "verified_count": 2 if verified else 1,
            "needs_manual_verification_count": 0 if verified else 1,
            "pending_channels": [],
        },
    }
    verification_report = {
        "run_id": "run-publish-guard",
        "stage": "publish",
        "status": manifest["status"],
        "records": results,
        "publish_summary": manifest["publish_summary"],
        "published_links": [
            {
                "topic_id": "topic-demo",
                "channel": "xiaohongshu_video",
                "platform": "xiaohongshu",
                "url": "https://www.xiaohongshu.com/explore/guard001",
                "status": "published",
            }
        ]
        if verified
        else [],
        "draft_records": [
            {
                "topic_id": "topic-demo",
                "channel": "wechat_article",
                "platform": "wechat",
                "draft_id": "draft_guard_001",
                "draft_url": "https://mp.weixin.qq.com/cgi-bin/appmsg?t=media/appmsg_edit&appmsgid=draft_guard_001",
                "status": "draft",
            }
        ],
    }
    wechat_result_file.parent.mkdir(parents=True, exist_ok=True)
    xhs_result_file.parent.mkdir(parents=True, exist_ok=True)
    write_json(
        wechat_result_file,
        {
            "topic_id": "topic-demo",
            "title": "批次验收测试",
            "channel": "wechat_article",
            "platform": "wechat",
            "status": "draft",
            "success": True,
            "draft_id": "draft_guard_001",
            "draft_url": "https://mp.weixin.qq.com/cgi-bin/appmsg?t=media/appmsg_edit&appmsgid=draft_guard_001",
            "verification_status": "verified",
        },
    )
    write_json(
        xhs_result_file,
        {
            "topic_id": "topic-demo",
            "title": "批次验收测试",
            "channel": "xiaohongshu_video",
            "platform": "xiaohongshu",
            "status": "published",
            "success": True,
            "platform_url": "https://www.xiaohongshu.com/explore/guard001",
            "verification_status": "verified" if verified else "needs_manual_verification",
        },
    )
    write_json(publish_root / "publish_manifest.json", manifest)
    write_json(publish_root / "publish_verification_report.json", verification_report)
    return publish_root / "publish_manifest.json"


def test_publish_guard_passes_verified_mixed_batch(tmp_path):
    manifest_path = sample_publish_manifest_for_guard(tmp_path)
    output_md = tmp_path / "publish_guard.md"
    proc = subprocess.run(
        [
            PYTHON,
            str(PROJECT_ROOT / "scripts" / "publish_guard.py"),
            "--publish-manifest",
            str(manifest_path),
            "--output-md",
            str(output_md),
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert proc.returncode == 0, proc.stderr
    payload = json.loads(proc.stdout)
    assert payload["mode"] == "publish_guard"
    assert payload["will_not_publish"] is True
    assert payload["passed"] is True
    assert payload["status"] == "passed"
    assert payload["summary"]["published_count"] == 1
    assert payload["summary"]["draft_count"] == 1
    assert Path(payload["guard_report_json"]).exists()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["publish_guard"]["status"] == "passed"
    assert manifest["publish_guard"]["passed"] is True
    assert Path(manifest["publish_guard"]["report_json"]).exists()
    assert output_md.exists()


def test_publish_guard_fails_unverified_published_link(tmp_path):
    manifest_path = sample_publish_manifest_for_guard(tmp_path, verified=False)
    proc = subprocess.run(
        [
            PYTHON,
            str(PROJECT_ROOT / "scripts" / "publish_guard.py"),
            "--publish-manifest",
            str(manifest_path),
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert proc.returncode == 0, proc.stderr
    payload = json.loads(proc.stdout)
    assert payload["passed"] is False
    assert payload["status"] == "failed"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["publish_guard"]["status"] == "failed"
    xhs_check = next(item for item in payload["channel_checks"] if item["channel"] == "xiaohongshu_video")
    assert "published_not_verified" in xhs_check["issues"]
    assert payload["expected_published_links"] == []


def test_publish_guard_fail_on_error_exits_non_zero(tmp_path):
    manifest_path = sample_publish_manifest_for_guard(tmp_path, verified=False)
    proc = subprocess.run(
        [
            PYTHON,
            str(PROJECT_ROOT / "scripts" / "publish_guard.py"),
            "--publish-manifest",
            str(manifest_path),
            "--fail-on-error",
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert proc.returncode == 1
    payload = json.loads(proc.stdout)
    assert payload["passed"] is False
    assert payload["status"] == "failed"


def test_publish_guard_reports_pending_when_result_missing(tmp_path):
    publish_root = tmp_path / "publish_out"
    publish_root.mkdir(parents=True, exist_ok=True)
    manifest = {
        "run_id": "run-publish-guard-pending",
        "stage": "publish",
        "status": "pending_execution",
        "channel_packs": [
            {
                "topic_id": "topic-demo",
                "title": "待回填测试",
                "channel": "wechat_article",
                "platform": "wechat",
                "status": "ready_for_execution",
            }
        ],
        "publish_results": [],
        "publish_summary": {
            "status": "pending_execution",
            "total_channels": 1,
            "recorded_count": 0,
            "pending_count": 1,
            "failed_count": 0,
            "draft_count": 0,
            "published_count": 0,
            "verified_count": 0,
            "needs_manual_verification_count": 0,
            "pending_channels": [{"topic_id": "topic-demo", "channel": "wechat_article"}],
        },
    }
    write_json(publish_root / "publish_manifest.json", manifest)
    write_json(
        publish_root / "publish_verification_report.json",
        {
            "run_id": "run-publish-guard-pending",
            "stage": "publish",
            "status": "pending_execution",
            "records": [],
            "published_links": [],
            "draft_records": [],
            "publish_summary": manifest["publish_summary"],
        },
    )

    proc = subprocess.run(
        [
            PYTHON,
            str(PROJECT_ROOT / "scripts" / "publish_guard.py"),
            "--publish-manifest",
            str(publish_root / "publish_manifest.json"),
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert proc.returncode == 0, proc.stderr
    payload = json.loads(proc.stdout)
    assert payload["status"] == "pending_execution"
    assert payload["passed"] is False
    assert payload["summary"]["pending_guard_count"] == 1
    assert payload["summary"]["blocking_issue_count"] == 0
    assert payload["summary"]["guard_issue_count"] == 1


def test_publish_guard_fails_when_verification_report_missing(tmp_path):
    manifest_path = sample_publish_manifest_for_guard(tmp_path)
    verification_path = manifest_path.parent / "publish_verification_report.json"
    verification_path.unlink()

    proc = subprocess.run(
        [
            PYTHON,
            str(PROJECT_ROOT / "scripts" / "publish_guard.py"),
            "--publish-manifest",
            str(manifest_path),
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert proc.returncode == 0, proc.stderr
    payload = json.loads(proc.stdout)
    assert payload["passed"] is False
    assert payload["status"] == "failed"
    assert payload["publish_verification_report_exists"] is False
    assert "missing_publish_verification_report" in payload["summary"]["consistency_issues"]
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["publish_guard"]["status"] == "failed"


def test_publish_guard_fails_when_result_file_missing(tmp_path):
    manifest_path = sample_publish_manifest_for_guard(tmp_path)
    verification_path = manifest_path.parent / "publish_verification_report.json"
    verification = json.loads(verification_path.read_text(encoding="utf-8"))
    result_file = Path(verification["records"][0]["result_file"])
    result_file.unlink()

    proc = subprocess.run(
        [
            PYTHON,
            str(PROJECT_ROOT / "scripts" / "publish_guard.py"),
            "--publish-manifest",
            str(manifest_path),
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert proc.returncode == 0, proc.stderr
    payload = json.loads(proc.stdout)
    assert payload["passed"] is False
    assert payload["status"] == "failed"
    assert any("missing_result_file" in issue for issue in payload["channel_checks"][0]["issues"])


def test_publish_guard_fails_when_result_file_content_mismatch(tmp_path):
    manifest_path = sample_publish_manifest_for_guard(tmp_path)
    verification_path = manifest_path.parent / "publish_verification_report.json"
    verification = json.loads(verification_path.read_text(encoding="utf-8"))
    result_file = Path(verification["records"][1]["result_file"])
    result_payload = json.loads(result_file.read_text(encoding="utf-8"))
    result_payload["platform_url"] = "https://www.xiaohongshu.com/explore/tampered"
    write_json(result_file, result_payload)

    proc = subprocess.run(
        [
            PYTHON,
            str(PROJECT_ROOT / "scripts" / "publish_guard.py"),
            "--publish-manifest",
            str(manifest_path),
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert proc.returncode == 0, proc.stderr
    payload = json.loads(proc.stdout)
    assert payload["passed"] is False
    assert payload["status"] == "failed"
    xhs_check = next(item for item in payload["channel_checks"] if item["channel"] == "xiaohongshu_video")
    assert "result_file_content_mismatch" in xhs_check["issues"]


def test_publish_guard_fails_summary_mismatch(tmp_path):
    manifest_path = sample_publish_manifest_for_guard(tmp_path)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["publish_summary"]["published_count"] = 99
    write_json(manifest_path, manifest)

    proc = subprocess.run(
        [
            PYTHON,
            str(PROJECT_ROOT / "scripts" / "publish_guard.py"),
            "--publish-manifest",
            str(manifest_path),
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert proc.returncode == 0, proc.stderr
    payload = json.loads(proc.stdout)
    assert payload["passed"] is False
    assert payload["status"] == "failed"
    assert "publish_summary_mismatch" in payload["summary"]["consistency_issues"]


def test_publish_guard_fails_when_manifest_and_verification_records_diverge(tmp_path):
    manifest_path = sample_publish_manifest_for_guard(tmp_path)
    verification_path = manifest_path.parent / "publish_verification_report.json"
    verification = json.loads(verification_path.read_text(encoding="utf-8"))
    verification["records"][1]["platform_url"] = "https://www.xiaohongshu.com/explore/different"
    write_json(verification_path, verification)

    proc = subprocess.run(
        [
            PYTHON,
            str(PROJECT_ROOT / "scripts" / "publish_guard.py"),
            "--publish-manifest",
            str(manifest_path),
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert proc.returncode == 0, proc.stderr
    payload = json.loads(proc.stdout)
    assert payload["passed"] is False
    assert payload["status"] == "failed"
    assert "manifest_verification_records_mismatch" in payload["summary"]["consistency_issues"]


def test_publish_guard_fails_when_verification_summary_mismatch(tmp_path):
    manifest_path = sample_publish_manifest_for_guard(tmp_path)
    verification_path = manifest_path.parent / "publish_verification_report.json"
    verification = json.loads(verification_path.read_text(encoding="utf-8"))
    verification["publish_summary"]["published_count"] = 99
    write_json(verification_path, verification)

    proc = subprocess.run(
        [
            PYTHON,
            str(PROJECT_ROOT / "scripts" / "publish_guard.py"),
            "--publish-manifest",
            str(manifest_path),
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert proc.returncode == 0, proc.stderr
    payload = json.loads(proc.stdout)
    assert payload["passed"] is False
    assert payload["status"] == "failed"
    assert "verification_publish_summary_mismatch" in payload["summary"]["consistency_issues"]
    assert "manifest_verification_summary_mismatch" in payload["summary"]["consistency_issues"]


def test_mainline_doctor_publish_manifest_routes_to_publish_guard(tmp_path):
    manifest_path = sample_publish_manifest_for_guard(tmp_path)
    output_json = tmp_path / "publish_guard.json"
    proc = subprocess.run(
        [
            PYTHON,
            str(PROJECT_ROOT / "scripts" / "run_mainline_stage.py"),
            "doctor",
            "--publish-manifest",
            str(manifest_path),
            "--output-json",
            str(output_json),
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert proc.returncode == 0, proc.stderr
    payload = json.loads(proc.stdout)
    assert payload["mode"] == "publish_guard"
    assert payload["passed"] is True
    assert output_json.exists()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["publish_guard"]["report_json"] == str(output_json.resolve())


def test_mainline_doctor_publish_manifest_fail_on_error_routes_to_publish_guard(tmp_path):
    manifest_path = sample_publish_manifest_for_guard(tmp_path, verified=False)
    proc = subprocess.run(
        [
            PYTHON,
            str(PROJECT_ROOT / "scripts" / "run_mainline_stage.py"),
            "doctor",
            "--publish-manifest",
            str(manifest_path),
            "--fail-on-error",
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert proc.returncode == 1
    payload = json.loads(proc.stdout)
    assert payload["mode"] == "publish_guard"
    assert payload["passed"] is False


def test_publish_guard_then_strict_postmortem_end_to_end(tmp_path):
    manifest_path = sample_publish_manifest_for_guard(tmp_path)
    guard_proc = subprocess.run(
        [
            PYTHON,
            str(PROJECT_ROOT / "scripts" / "publish_guard.py"),
            "--publish-manifest",
            str(manifest_path),
            "--fail-on-error",
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert guard_proc.returncode == 0, guard_proc.stderr
    guard_payload = json.loads(guard_proc.stdout)
    assert guard_payload["passed"] is True
    assert Path(guard_payload["guard_report_json"]).exists()
    assert Path(guard_payload["guard_report_markdown"]).exists()

    postmortem_dir = tmp_path / "postmortem_out"
    postmortem_proc = subprocess.run(
        [
            PYTHON,
            str(PROJECT_ROOT / "scripts" / "postmortem_writeback.py"),
            "--publish-manifest",
            str(manifest_path),
            "--require-publish-guard",
            "--output-dir",
            str(postmortem_dir),
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert postmortem_proc.returncode == 0, postmortem_proc.stderr
    postmortem = json.loads((postmortem_dir / "postmortem_manifest.json").read_text(encoding="utf-8"))
    assert postmortem["publish_guard"]["passed"] is True
    assert postmortem["publish_guard"]["report_json"] == guard_payload["guard_report_json"]
    assert postmortem["writeback"]["topic_pattern_library"]["published_topics"] == 1
    assert postmortem["writeback"]["topic_pattern_library"]["drafted_topics"] == 1


def sample_wechat_channel_pack_with_execution_request(tmp: Path) -> Path:
    html = tmp / "wechat.html"
    html.write_text("<html><body>正文</body></html>", encoding="utf-8")
    pack_dir = tmp / "publish_out" / "channel_packs" / "topic-demo" / "wechat_article"
    pack_dir.mkdir(parents=True)
    pack_path = pack_dir / "channel_pack.json"
    request_path = pack_dir / "execution_request.json"
    verification_path = pack_dir / "verification_request.json"
    write_json(
        pack_path,
        {
            "topic_id": "topic-demo",
            "title": "执行入口测试",
            "channel": "wechat_article",
            "status": "ready_for_execution",
            "executor_skill": "baoyu-post-to-wechat",
            "execution_mode": "draft_push_or_browser_confirm",
            "artifact_hint": {"wechat_html": str(html)},
            "publish_metadata": {"title": "执行入口测试", "summary": "摘要"},
            "pack_manifest": str(pack_path),
            "execution_request": str(request_path),
            "verification_request": str(verification_path),
        },
    )
    write_json(
        request_path,
        {
            "schema_version": "1.0",
            "topic_id": "topic-demo",
            "title": "执行入口测试",
            "channel": "wechat_article",
            "platform": "wechat",
            "status": "ready_for_user_confirmation",
            "executor_skill": "baoyu-post-to-wechat",
            "execution_mode": "draft_push_or_browser_confirm",
            "requires_user_confirmation": True,
            "channel_pack": str(pack_path),
            "inputs": {"artifacts": {"wechat_html": str(html)}, "publish_metadata": {"title": "执行入口测试"}},
            "route_priority": [
                {"route": "baoyu-post-to-wechat", "type": "skill_draft_push"},
                {"route": "browser-profile", "type": "browser_confirm_fallback", "open_command": "python3 scripts/open_publish_browser.py wechat_article"},
            ],
        },
    )
    write_json(tmp / "publish_out" / "publish_manifest.json", {"run_id": "run-execute-test", "stage": "publish", "channel_packs": [json.loads(pack_path.read_text(encoding="utf-8"))]})
    write_json(tmp / "publish_out" / "channel_execution_manifest.json", {"run_id": "run-execute-test", "stage": "publish", "executions": [{"topic_id": "topic-demo", "channel": "wechat_article", "status": "pending_user_confirmation"}]})
    write_json(tmp / "publish_out" / "publish_verification_report.json", {"run_id": "run-execute-test", "stage": "publish", "status": "pending_execution", "published_links": []})
    return request_path


def test_execute_publish_request_defaults_to_dry_run(tmp_path):
    request_path = sample_wechat_channel_pack_with_execution_request(tmp_path)
    proc = subprocess.run(
        [
            PYTHON,
            str(PROJECT_ROOT / "scripts" / "execute_publish_request.py"),
            "--execution-request",
            str(request_path),
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert proc.returncode == 0, proc.stderr
    payload = json.loads(proc.stdout)
    assert payload["mode"] == "dry_run"
    assert payload["will_not_publish"] is True
    assert payload["selected_route"] == "baoyu-post-to-wechat"
    assert Path(payload["publish_payload"]).exists()
    assert not (request_path.parent / "publish_result.json").exists()


def test_execute_publish_request_confirm_invokes_skill_and_records_result(tmp_path):
    request_path = sample_wechat_channel_pack_with_execution_request(tmp_path)
    scripts_dir = str(PROJECT_ROOT / "scripts")
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
    module = __import__("execute_publish_request")
    invoker = Mock()
    invoker.invoke.return_value = {
        "success": True,
        "platform": "wechat",
        "status": "draft",
        "url": "https://mp.weixin.qq.com/draft/abc",
        "msg_id": "draft_abc",
        "verification_status": "verified",
    }
    result = module.execute_request(request_path, confirm_execute=True, invoker=invoker)

    assert result["status"] == "executed_and_recorded"
    invoker.invoke.assert_called_once()
    assert invoker.invoke.call_args[0][0] == "baoyu-post-to-wechat"
    assert (request_path.parent / "publish_result.json").exists()
    verification = json.loads((tmp_path / "publish_out" / "publish_verification_report.json").read_text(encoding="utf-8"))
    assert verification["published_links"] == []
    assert verification["draft_records"][0]["draft_id"] == "draft_abc"


def test_execute_publish_request_confirm_does_not_auto_verify_skill_result(tmp_path):
    request_path = sample_wechat_channel_pack_with_execution_request(tmp_path)
    scripts_dir = str(PROJECT_ROOT / "scripts")
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
    module = __import__("execute_publish_request")
    invoker = Mock()
    invoker.invoke.return_value = {
        "success": True,
        "platform": "wechat",
        "status": "draft",
        "url": "https://mp.weixin.qq.com/draft/not-verified",
        "msg_id": "draft_not_verified_by_skill",
    }

    result = module.execute_request(request_path, confirm_execute=True, invoker=invoker)

    assert result["status"] == "executed_and_recorded"
    verification = json.loads((tmp_path / "publish_out" / "publish_verification_report.json").read_text(encoding="utf-8"))
    assert verification["status"] == "needs_manual_verification"
    assert verification["draft_records"] == []
    assert verification["publish_summary"]["draft_count"] == 0
    assert verification["publish_summary"]["needs_manual_verification_count"] == 1


def test_execute_publish_request_blocks_external_cli_even_with_confirm(tmp_path, monkeypatch):
    pack_path = sample_video_channel_pack(tmp_path, channel="xiaohongshu_video")
    all_in_one_root = tmp_path / "All-IN-ONE"
    all_in_one_root.mkdir()
    monkeypatch.setenv("ALL_IN_ONE_ROOT", str(all_in_one_root))
    monkeypatch.setenv("PATH", "/usr/bin:/bin")
    request_path = sample_execution_request(
        tmp_path,
        channel="xiaohongshu_video",
        platform="xiaohongshu",
        routes=[
            {"route": "all-in-one", "type": "api_first_cli"},
            {"route": "browser-profile", "type": "browser_confirm_fallback", "open_command": "python3 scripts/open_publish_browser.py xiaohongshu_video"},
        ],
    )
    request = json.loads(request_path.read_text(encoding="utf-8"))
    request["channel_pack"] = str(pack_path)
    write_json(request_path, request)
    scripts_dir = str(PROJECT_ROOT / "scripts")
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
    module = __import__("execute_publish_request")
    invoker = Mock()

    result = module.execute_request(request_path, confirm_execute=True, invoker=invoker)

    assert result["status"] == "blocked_manual_or_external_route"
    assert result["selected_route"] == "all-in-one"
    assert result["selected_route_type"] == "api_first_cli"
    assert result["will_not_publish"] is True
    invoker.invoke.assert_not_called()
    assert not (request_path.parent / "publish_result.json").exists()
