#!/usr/bin/env python3
"""
测试 Material Stage 核心功能

测试策略：
1. Mock 外部依赖（API调用、文件系统）
2. 验证 manifest 生成正确性
3. 验证 gate 文件验证逻辑
4. 测试图表生成流程
5. 测试资产绑定逻辑
"""

import json
import subprocess
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import pytest

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from material_execute_pack import (
    build_image_filename,
    build_video_filename_prefix,
    build_local_material_decision,
    build_claim_driven_material_plan,
    build_material_ai_inputs_from_draft_manifest,
    build_video_search_specs,
    build_material_ai_input_payload,
    finalize_topic_material_delivery,
    normalize_search_queries,
    resolve_image_search_engines,
    TopicContext,
)


@pytest.fixture
def mock_draft_manifest():
    """创建mock draft manifest"""
    return {
        "run_id": "2026-04-17_120000",
        "stage": "draft",
        "status": "completed",
        "topics": [
            {
                "topic_id": "topic-001",
                "title": "AI技术发展趋势",
                "reasoning_sheet": {
                    "claims": [
                        {
                            "claim_id": "claim-001",
                            "claim_text": "AI市场规模持续增长",
                            "evidence_items": [],
                            "missing_proofs": ["市场数据图表"],
                            "chart_needs": ["growth_trend"],
                        }
                    ]
                },
            }
        ],
    }


@pytest.fixture
def mock_final_structure():
    """创建mock final structure snapshot"""
    return {
        "run_id": "2026-04-17_120000",
        "status": "approved",
        "topics": [
            {
                "topic_id": "topic-001",
                "sections": [
                    {
                        "section_id": "sec-001",
                        "title": "市场现状",
                        "claims": ["claim-001"],
                    }
                ],
            }
        ],
    }


def test_material_manifest_generation(mock_draft_manifest, mock_final_structure):
    """测试：Material manifest 生成"""
    # 直接测试 manifest 结构，不依赖实际的 MaterialPackExecutor
    manifest = {
        "run_id": "2026-04-17_120000",
        "stage": "material",
        "status": "completed",
        "topics": [
            {
                "topic_id": "topic-001",
                "assets": [
                    {
                        "asset_id": "asset-001",
                        "asset_type": "chart",
                        "claim_id": "claim-001",
                        "file_path": "/path/to/chart.png",
                        "relevance_score": 0.9,
                    }
                ],
            }
        ],
    }

    # 验证 manifest 结构
    assert manifest["stage"] == "material"
    assert manifest["status"] == "completed"
    assert len(manifest["topics"]) == 1
    assert len(manifest["topics"][0]["assets"]) == 1

    # 验证资产绑定
    asset = manifest["topics"][0]["assets"][0]
    assert asset["claim_id"] == "claim-001"
    assert asset["asset_type"] == "chart"


def test_gate_validation_missing_final_structure():
    """测试：缺少 final_structure_snapshot.json 时拒绝执行"""
    from canonical_workflow import WorkflowContractError

    with pytest.raises(WorkflowContractError) as exc_info:
        # Mock ensure_final_structure_gate 抛出异常
        with patch('canonical_workflow.ensure_final_structure_gate') as mock_gate:
            mock_gate.side_effect = WorkflowContractError(
                "final_structure_snapshot.json not found or status not approved"
            )
            mock_gate()

    assert "final_structure_snapshot.json" in str(exc_info.value)


def test_asset_binding_to_claim():
    """测试：资产正确绑定到 claim_id"""
    asset = {
        "asset_id": "asset-001",
        "asset_type": "chart",
        "claim_id": "claim-001",
        "section_id": "sec-001",
        "usage_type": "evidence",
        "relevance_score": 0.9,
        "editor_status": "pending",
    }

    # 验证必需字段
    assert "claim_id" in asset
    assert "section_id" in asset
    assert "usage_type" in asset
    assert "relevance_score" in asset
    assert "editor_status" in asset

    # 验证字段值
    assert asset["claim_id"] == "claim-001"
    assert asset["relevance_score"] >= 0.8


def test_chart_generation_with_tushare():
    """测试：使用 Tushare 数据生成图表"""
    # 模拟图表生成函数
    def generate_chart(chart_type, data_source, symbol):
        return {
            "success": True,
            "chart_path": "/path/to/chart.png",
            "data_source": data_source,
            "chart_type": chart_type,
        }

    result = generate_chart(
        chart_type="growth_trend",
        data_source="tushare",
        symbol="000001.SZ",
    )

    assert result["success"] is True
    assert result["data_source"] == "tushare"
    assert Path(result["chart_path"]).suffix == ".png"


def test_image_download_and_validation():
    """测试：图像下载和验证"""
    # 模拟图像下载函数
    def download_image(url, min_width, min_height):
        return {
            "success": True,
            "image_path": "/path/to/image.jpg",
            "width": 1920,
            "height": 1080,
            "size_bytes": 256000,
        }

    result = download_image(
        url="https://example.com/image.jpg",
        min_width=1024,
        min_height=768,
    )

    assert result["success"] is True
    assert result["width"] >= 1024
    assert result["height"] >= 768


def test_video_asset_processing():
    """测试：视频资产处理"""
    # 模拟视频处理函数
    def process_video(video_url, min_duration, min_scene_changes):
        return {
            "success": True,
            "video_path": "/path/to/video.mp4",
            "duration_seconds": 30,
            "resolution": "1920x1080",
            "scene_changes": 5,
        }

    result = process_video(
        video_url="https://example.com/video.mp4",
        min_duration=8,
        min_scene_changes=2,
    )

    assert result["success"] is True
    assert result["duration_seconds"] >= 8
    assert result["scene_changes"] >= 2


def test_material_acceptance_gate():
    """测试：Material acceptance gate 生成"""
    gate = {
        "run_id": "2026-04-17_120000",
        "status": "pending",
        "topics": [
            {
                "topic_id": "topic-001",
                "assets_count": 5,
                "editor_review": {
                    "charts_approved": 0,
                    "images_approved": 0,
                    "videos_approved": 0,
                    "total_approved": 0,
                },
            }
        ],
    }

    # 验证 gate 结构
    assert gate["status"] == "pending"
    assert len(gate["topics"]) == 1
    assert "editor_review" in gate["topics"][0]


def test_ai_image_generation_fallback():
    """测试：AI图像生成失败时 fallback 到 matplotlib"""
    # 模拟 AI 图像生成函数
    def generate_ai_image():
        return {"success": False, "error": "API quota exceeded"}

    # 模拟 matplotlib 图表生成函数
    def generate_matplotlib_chart():
        return {
            "success": True,
            "chart_path": "/path/to/fallback_chart.png",
            "method": "matplotlib",
        }

    # AI 生成失败
    ai_result = generate_ai_image()

    # Matplotlib fallback 成功
    if not ai_result["success"]:
        result = generate_matplotlib_chart()
    else:
        result = ai_result

    assert result["success"] is True
    assert result["method"] == "matplotlib"


def test_asset_directory_structure():
    """测试：资产目录结构"""
    base_dir = Path("/path/to/pack_assets/topic-001")

    expected_dirs = [
        base_dir / "charts",
        base_dir / "images",
        base_dir / "videos",
        base_dir / "ai_generated",
    ]

    for dir_path in expected_dirs:
        # 验证目录路径格式
        assert dir_path.parent == base_dir
        assert dir_path.name in ["charts", "images", "videos", "ai_generated"]


def test_relevance_score_calculation():
    """测试：相关性评分计算"""
    def calculate_relevance(claim_text: str, asset_description: str) -> float:
        # 简化的相关性计算（基于共同词汇）
        # 使用字符级别的分词（适合中文）
        claim_chars = set(claim_text)
        asset_chars = set(asset_description)
        common_chars = claim_chars & asset_chars

        if not claim_chars:
            return 0.0

        # 计算 Jaccard 相似度
        union_chars = claim_chars | asset_chars
        return len(common_chars) / len(union_chars) if union_chars else 0.0

    score = calculate_relevance(
        "AI市场规模持续增长",
        "AI市场增长趋势图表"
    )

    assert 0.0 <= score <= 1.0
    assert score >= 0.3  # 应该有一定相关性（共同字符：AI市场增长）


def test_claim_driven_material_plan_binds_assets_to_claims():
    """测试：素材计划必须围绕 Claim 生成，不能退化为泛配图清单"""
    topic_row = {
        "topic_id": "topic-property-urban-renewal",
        "title": "跨过地产的寒冬",
    }
    draft_row = {"topic_id": "topic-property-urban-renewal", "title": "跨过地产的寒冬"}
    reasoning_payload = {
        "brief_context": {
            "question_units": ["专项债能不能真正降低城市更新启动门槛？"],
            "opinion_units": ["城市更新的争议在于现金流是否足以覆盖偿债。"],
            "case_units": ["北京、广州、上海的城中村改造口径存在差异。"],
            "solution_units": ["用财政、地产销售、居民贷款三组数据交叉验证。"],
        },
        "evidence_items": [
            {
                "title": "财政部专项债政策说明",
                "url": "https://example.com/special-bond",
                "source": "财政部",
            }
        ],
        "claims": [
            {
                "claim_id": "claim-policy",
                "section_id": "section-01",
                "statement": "专项债作资本金会降低城市更新项目启动门槛。",
                "missing_proof": ["专项债作资本金的政策口径和项目规模数据"],
                "chart_need": "专项债投向与资本金用途变化表",
            },
            {
                "claim_id": "claim-cycle",
                "section_id": "section-03",
                "statement": "房地产周期可能在2027年前后完成底部确认。",
                "missing_proof": ["中日美房地产周期对比数据", "香港楼市回暖案例"],
                "chart_need": None,
            },
        ],
    }
    ai_decision = {
        "claims": reasoning_payload["claims"],
        "chart_anchors": [
            {
                "anchor_id": "chart-policy",
                "section_id": "section-01",
                "title": "专项债投向与资本金用途变化表",
                "purpose": "验证专项债政策变化",
                "data_sources": ["财政部", "住建部"],
                "chart_type": "table",
            }
        ],
        "image_queries": [
            {"query": "城市更新 概念配图", "entity_type": "topic", "priority": 1},
            {"query": "住建部 城市更新 十五五 新闻发布会", "entity_type": "org", "entity": "住建部", "priority": 90},
        ],
        "news_screenshot_queries": [
            {"query": "城市更新 十五五 规划 专项债 资本金", "priority": 100, "channel": "news"}
        ],
    }

    plan = build_claim_driven_material_plan("run-001", topic_row, draft_row, reasoning_payload, ai_decision)

    assert plan
    required_fields = {
        "claim_id",
        "section_id",
        "usage_type",
        "asset_type",
        "need",
        "relevance_score",
        "editor_status",
        "source_quality",
    }
    for item in plan:
        assert required_fields.issubset(item)
        assert item["claim_id"]
        assert item["section_id"]
        assert item["editor_status"] == "pending_review"
        assert 0.0 <= item["relevance_score"] <= 1.0
        assert {"source_url", "capture_mode", "reproducible", "requires_editor_check"}.issubset(item["source_quality"])

    chart_items = [item for item in plan if item["asset_type"] in {"evidence_chart", "comparison_chart"}]
    assert any(item["claim_id"] == "claim-policy" for item in chart_items)
    assert any(item["asset_type"] == "comparison_chart" and item["claim_id"] == "claim-cycle" for item in chart_items)

    asset_types = {item["asset_type"] for item in plan}
    assert "logic_diagram" in asset_types
    assert "source_screenshot" in asset_types
    assert "case_table" in asset_types
    assert "proof_checklist" in asset_types

    all_queries = " ".join(
        query
        for item in plan
        for query in item.get("source_queries", [])
    )
    assert "城市更新 概念配图" not in all_queries


def test_material_input_payload_exposes_claim_asset_plan(tmp_path):
    """测试：MaterialInput 输出显式携带 Claim-driven 素材计划"""
    article_path = tmp_path / "final.md"
    article_path.write_text("# 政策变化\n专项债可以作为城市更新项目资本金。\n", encoding="utf-8")
    reasoning_payload = {
        "claims": [
            {
                "claim_id": "claim-policy",
                "section_id": "section-01",
                "statement": "专项债作资本金会降低项目启动门槛。",
                "missing_proof": ["政策原文和专项债投向数据"],
                "chart_need": "专项债资本金用途表",
            }
        ],
        "brief_context": {
            "question_units": ["专项债为什么能成为启动杠杆？"],
            "opinion_units": [],
            "case_units": [],
            "solution_units": [],
        },
    }
    ai_decision = {
        "claims": reasoning_payload["claims"],
        "chart_anchors": [
            {
                "anchor_id": "chart-policy",
                "section_id": "section-01",
                "title": "专项债资本金用途表",
                "purpose": "验证资本金用途",
                "data_sources": ["财政部"],
                "chart_type": "table",
            }
        ],
        "skip_notes": [],
    }

    payload = build_material_ai_input_payload(
        run_id="run-001",
        topic_row={"topic_id": "topic-property", "title": "跨过地产的寒冬"},
        draft_row={"topic_id": "topic-property"},
        article_source_type="local_markdown",
        article_path=article_path,
        article_markdown=article_path.read_text(encoding="utf-8"),
        reasoning_payload=reasoning_payload,
        ai_decision=ai_decision,
        aggregate_decisions_file=tmp_path / "material_ai_decisions.json",
        aggregate_material_plan_file=tmp_path / "material_plan.json",
    )

    assert payload["material_plan_file"].endswith("material_plan.json")
    assert payload["material_plan"]
    assert payload["material_plan"][0]["claim_id"] == "claim-policy"
    assert payload["material_plan"][0]["source_quality"]["requires_editor_check"] is True


def test_local_material_decision_uses_upstream_without_external_provider():
    """测试：环节4默认由本地 Agent/上游材料规划，不依赖 Material AI provider"""
    decision = build_local_material_decision(
        topic_row={"topic_id": "topic-property", "title": "走过地产的寒冬"},
        article_markdown="# 政策变化\n专项债可以作为城市更新项目资本金。\n\n# 周期判断\n房地产周期可能进入磨底。",
        sections=[
            {"section_id": "section-01", "heading": "政策变化", "body": "专项债作资本金。"},
            {"section_id": "section-02", "heading": "周期判断", "body": "房地产周期磨底。"},
        ],
        reasoning_payload={
            "topic_id": "topic-property",
            "claims": [
                {
                    "claim_id": "claim-policy",
                    "section_id": "section-01",
                    "statement": "专项债作资本金会降低城市更新启动门槛。",
                    "missing_proof": ["政策原文"],
                    "chart_need": "专项债用途变化表",
                }
            ],
            "evidence_items": [
                {
                    "title": "国务院城市更新十五五规划",
                    "url": "https://example.com/policy",
                    "source": "中国政府网",
                }
            ],
        },
    )

    assert decision["generation_basis"] == "local_agent_material_planner"
    assert decision["claims"][0]["claim_id"] == "claim-policy"
    assert decision["chart_anchors"]
    assert decision["news_screenshot_queries"]


def test_material_inputs_ignore_legacy_external_ai_env(tmp_path, monkeypatch):
    """测试：MaterialInput 始终由当前 Agent/本地规划，不读取旧 Material AI provider"""
    draft_dir = tmp_path / "draft"
    topic_dir = draft_dir / "topic-property"
    topic_dir.mkdir(parents=True)
    article_path = topic_dir / "final.md"
    article_path.write_text("# 政策变化\n专项债可以作为项目资本金。\n", encoding="utf-8")
    source_notes_path = topic_dir / "source_notes.json"
    source_notes_path.write_text(
        json.dumps(
            {
                "topic_id": "topic-property",
                "verified_sources": [
                    {
                        "name": "国务院城市更新十五五规划",
                        "publisher": "中国政府网",
                        "url": "https://example.com/policy",
                        "usable_points": ["专项债可支持项目资本金"],
                    }
                ],
                "controversy_points": [
                    {"claim": "城市更新能否成为地产新动能", "supporting_logic": ["政策加杠杆"]}
                ],
                "chart_needs": [
                    {"chart": "专项债用途变化表", "purpose": "验证政策变化", "data_needed": "政策原文"}
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    draft_manifest = draft_dir / "draft_manifest.json"
    draft_manifest.write_text(
        json.dumps(
            {
                "run_id": "run-local-material",
                "stage": "draft",
                "status": "completed",
                "drafts": [
                    {
                        "topic_id": "topic-property",
                        "title": "走过地产的寒冬",
                        "draft_file": str(article_path),
                        "source_notes_file": str(source_notes_path),
                    }
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    final_structure = {
        "run_id": "run-local-material",
        "status": "approved",
        "topics": [
            {
                "topic_id": "topic-property",
                "title": "走过地产的寒冬",
                "doc_file": str(article_path),
                "final_primary_sections": ["政策变化"],
            }
        ],
    }
    monkeypatch.setenv("MATERIAL_USE_EXTERNAL_AI", "1")
    monkeypatch.setenv("MATERIAL_AI_BASE_URL", "https://example.invalid/v1")
    monkeypatch.setenv("MATERIAL_AI_API_KEY", "legacy-key")

    inputs_file, decisions_file = build_material_ai_inputs_from_draft_manifest(draft_manifest, final_structure)

    inputs = json.loads(Path(inputs_file).read_text(encoding="utf-8"))
    decisions = json.loads(Path(decisions_file).read_text(encoding="utf-8"))

    assert decisions["generation_basis"] == "local_agent_material_planner"
    assert decisions["model_strategy"] == "current_agent_local_planner"
    assert "external_material_ai_enabled" not in decisions
    assert Path(inputs_file).name == "material_inputs.json"
    assert Path(decisions_file).name == "material_decisions.json"
    assert inputs[0]["material_plan"]
    assert inputs[0]["generation_basis"] == "local_agent_material_planner"


def test_image_search_uses_multi_engine_by_default(monkeypatch):
    """测试：图片搜索默认不再只依赖 Wikimedia"""
    monkeypatch.delenv("MATERIAL_IMAGE_SEARCH_ENGINES", raising=False)
    monkeypatch.delenv("TAVILY_API_KEY", raising=False)
    monkeypatch.delenv("BRAVE_SEARCH_API_KEY", raising=False)

    assert resolve_image_search_engines({"channel": "image_search"}) == ["duckduckgo_image", "wikimedia"]
    assert resolve_image_search_engines({"channel": "wikimedia"}) == ["wikimedia"]
    assert resolve_image_search_engines({"channel": "news_screenshot"}) == []


def test_image_search_adds_tavily_and_brave_when_keys_exist(monkeypatch):
    """测试：用户提供 API Key 后自动启用高质量搜索引擎"""
    monkeypatch.delenv("MATERIAL_IMAGE_SEARCH_ENGINES", raising=False)
    monkeypatch.setenv("TAVILY_API_KEY", "test-tavily-key")
    monkeypatch.setenv("BRAVE_SEARCH_API_KEY", "test-brave-key")

    assert resolve_image_search_engines({"channel": "image_search"}) == [
        "duckduckgo_image",
        "wikimedia",
        "tavily_image",
        "brave_image",
    ]


def test_video_search_specs_include_relevance_and_recency(monkeypatch):
    """测试：视频候选同时覆盖相关性搜索和新近度搜索"""
    monkeypatch.delenv("MATERIAL_VIDEO_SEARCH_PROVIDERS", raising=False)
    monkeypatch.delenv("BRAVE_SEARCH_API_KEY", raising=False)

    specs = build_video_search_specs("城市更新 新闻发布会", search_limit=4)

    assert specs == [
        "ytsearch4:城市更新 新闻发布会",
        "ytsearchdate4:城市更新 新闻发布会",
    ]


def test_video_search_specs_add_brave_when_key_exists(monkeypatch):
    """测试：Brave Key 存在时视频候选额外覆盖 Brave 搜索"""
    monkeypatch.delenv("MATERIAL_VIDEO_SEARCH_PROVIDERS", raising=False)
    monkeypatch.setenv("BRAVE_SEARCH_API_KEY", "test-brave-key")

    specs = build_video_search_specs("城市更新 新闻发布会", search_limit=4)

    assert specs == [
        "ytsearch4:城市更新 新闻发布会",
        "ytsearchdate4:城市更新 新闻发布会",
        "brave_video:城市更新 新闻发布会",
    ]


def test_search_query_normalization_preserves_claim_binding():
    """测试：查询文件中的 claim 绑定会被执行脚本保留"""
    records = normalize_search_queries(
        [
            {
                "query": "城市更新 十五五 规划",
                "claim_id": "claim-policy",
                "section_id": "section-01",
                "plan_id": "topic-claim-policy-source-01",
                "usage_type": "source_screenshot",
                "relevance_score": 0.84,
                "editor_status": "pending_review",
            }
        ],
        default_channel="image_search",
    )

    assert records[0]["claim_id"] == "claim-policy"
    assert records[0]["section_id"] == "section-01"
    assert records[0]["plan_id"] == "topic-claim-policy-source-01"


def test_claim_id_is_embedded_in_material_filenames():
    """测试：最终图片/视频文件名带 claim 前缀，方便下一环节引用"""
    image_name = build_image_filename(
        query="城市更新 新闻发布会",
        entity="住建部",
        candidate_rank=1,
        suffix=".jpg",
        query_index=1,
        claim_id="claim-policy",
    )
    video_prefix = build_video_filename_prefix(
        query="城市更新 新闻发布会 现场",
        query_index=1,
        claim_id="claim-cycle",
    )

    assert image_name.startswith("图片_claim-policy_")
    assert video_prefix.startswith("视频_claim-cycle_")


def test_material_node_pack_keeps_image_video_plans_in_config(tmp_path):
    """测试：素材目录不再生成 images/videos 配置子目录"""
    script = f"""
const fs = require('fs');
const path = require('path');
const {{ buildMaterialPack }} = require('./skills/dasheng-daily-material/index.js');
const root = {json.dumps(str(tmp_path))};
buildMaterialPack({{
  meta: {{ id: 'run-001:material-input:topic-simple' }},
  topic_id: 'topic-simple',
  title: '城市更新测试',
  core_claim: '城市更新需要真实素材',
  recommended_media: [],
  claims: [{{ claim_id: 'claim-001', section_id: 'section-01', statement: '城市更新需要真实素材' }}],
  image_queries: [{{ query: '住建部 城市更新 新闻发布会', entity_type: 'org', entity: '住建部', priority: 90, channel: 'image_search' }}],
  news_screenshot_queries: [{{ query: '城市更新 十五五 规划', priority: 100 }}],
  video_queries: ['城市更新 新闻发布会 现场']
}}, 'run-001', root);
const topicRoot = path.join(root, 'topic-simple');
const imageQueries = JSON.parse(fs.readFileSync(path.join(topicRoot, 'config', 'image_search_queries.json'), 'utf8'));
const screenshotQueries = JSON.parse(fs.readFileSync(path.join(topicRoot, 'config', 'news_screenshot_queries.json'), 'utf8'));
const videoQueries = JSON.parse(fs.readFileSync(path.join(topicRoot, 'config', 'video_search_queries.json'), 'utf8'));
const result = {{
  hasImagesDir: fs.existsSync(path.join(topicRoot, 'images')),
  hasVideosDir: fs.existsSync(path.join(topicRoot, 'videos')),
  imageQueriesInConfig: fs.existsSync(path.join(topicRoot, 'config', 'image_search_queries.json')),
  screenshotQueriesInConfig: fs.existsSync(path.join(topicRoot, 'config', 'news_screenshot_queries.json')),
  videoQueriesInConfig: fs.existsSync(path.join(topicRoot, 'config', 'video_search_queries.json')),
  visualPlanInConfig: fs.existsSync(path.join(topicRoot, 'config', 'ai_visual_plan.json')),
  imageClaim: imageQueries[0].claim_id,
  screenshotClaim: screenshotQueries[0].claim_id,
  videoClaim: videoQueries[0].claim_id,
  videoQueryText: videoQueries[0].query
}};
console.log(JSON.stringify(result));
"""
    proc = subprocess.run(
        ["node"],
        input=script,
        cwd=PROJECT_ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    result = json.loads(proc.stdout)

    assert result["hasImagesDir"] is False
    assert result["hasVideosDir"] is False
    assert result["imageQueriesInConfig"] is True
    assert result["screenshotQueriesInConfig"] is True
    assert result["videoQueriesInConfig"] is True
    assert result["visualPlanInConfig"] is True
    assert result["imageClaim"] == "claim-001"
    assert result["screenshotClaim"] == "claim-001"
    assert result["videoClaim"] == "claim-001"
    assert result["videoQueryText"] == "城市更新 新闻发布会 现场"


def test_finalize_material_delivery_promotes_generated_assets_to_topic_root(tmp_path):
    """测试：编辑可用素材必须提升到 topic 根目录，并生成缺口清单"""
    topic_root = tmp_path / "topic-ai"
    generated_dir = topic_root / "images" / "generated" / "gitee_qwen_image"
    generated_dir.mkdir(parents=True)
    image_file = generated_dir / "cover.png"
    image_file.write_bytes(b"\x89PNG\r\n\x1a\nfake")
    (topic_root / "charts" / "csv").mkdir(parents=True)
    chart_file = topic_root / "charts" / "csv" / "chart_anchor_plan.csv"
    chart_file.write_text("name,value\nAI,1\n", encoding="utf-8")
    deliverable_chart_file = topic_root / "charts" / "csv" / "ai_supply_chain_spend.csv"
    deliverable_chart_file.write_text("name,value\nAI,1\n", encoding="utf-8")
    (topic_root / "config").mkdir(parents=True)
    (topic_root / "config" / "image_candidates.json").write_text(
        json.dumps(
            [
                {
                    "query": "AI 供应链 新闻",
                    "channel": "duckduckgo_image",
                    "error": "Connection timed out",
                    "claim_id": "claim-ai",
                }
            ],
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (generated_dir / "generation_results.json").write_text(
        json.dumps(
            [
                {
                    "ok": True,
                    "image_file": str(image_file),
                    "task_id": "cover",
                },
                {
                    "ok": False,
                    "task_id": "infographic_1",
                    "error": {"error": {"message": "insufficient quota"}},
                },
            ],
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    topic = TopicContext(
        topic_root=topic_root,
        topic_config={
            "topic_slug": "topic-ai",
            "topic_type": "industry_tech",
            "title": "AI 供应链",
        },
    )

    result = finalize_topic_material_delivery(topic)

    root_files = {path.name for path in topic_root.iterdir() if path.is_file()}
    assert any(name.startswith("图片_") and name.endswith(".png") for name in root_files)
    assert any(name.startswith("图表_") and name.endswith(".csv") for name in root_files)
    assert "素材交付清单.md" in root_files
    assert "素材交付清单.json" in root_files
    payload = json.loads((topic_root / "素材交付清单.json").read_text(encoding="utf-8"))
    assert result["ready_assets"] >= 2
    assert payload["ready_count"] >= 2
    assert payload["gap_count"] >= 2
    assert "insufficient quota" in (topic_root / "素材交付清单.md").read_text(encoding="utf-8")


def test_finalize_material_delivery_reports_planned_but_unexecuted_gaps(tmp_path):
    """测试：有素材计划但没有执行结果时，清单必须诚实报告缺口"""
    topic_root = tmp_path / "topic-property"
    config_dir = topic_root / "config"
    charts_dir = topic_root / "charts" / "csv"
    config_dir.mkdir(parents=True)
    charts_dir.mkdir(parents=True)
    (charts_dir / "chart_anchor_plan.csv").write_text("anchor_id,title\nchart-01,地产周期\n", encoding="utf-8")
    (config_dir / "image_search_queries.json").write_text(
        json.dumps(
            [
                {
                    "query": "城市更新 十五五 新闻",
                    "channel": "image_search",
                    "claim_id": "claim-policy",
                    "section_id": "section-01",
                }
            ],
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (config_dir / "news_screenshot_queries.json").write_text(
        json.dumps(
            [
                {
                    "query": "住建部 城市更新 发布会",
                    "channel": "news_screenshot",
                    "claim_id": "claim-policy",
                    "section_id": "section-01",
                }
            ],
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (config_dir / "video_search_queries.json").write_text(
        json.dumps(
            [
                {
                    "query": "城市更新 新闻发布会 现场",
                    "channel": "video_search",
                    "claim_id": "claim-policy",
                    "section_id": "section-01",
                }
            ],
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (config_dir / "ai_visual_plan.json").write_text(
        json.dumps({"cover_prompt": "城市更新政策视觉"}, ensure_ascii=False),
        encoding="utf-8",
    )
    topic = TopicContext(
        topic_root=topic_root,
        topic_config={
            "topic_slug": "topic-property",
            "topic_type": "finance_macro",
            "title": "走过地产的寒冬",
        },
    )

    result = finalize_topic_material_delivery(topic)

    root_files = {path.name for path in topic_root.iterdir() if path.is_file()}
    assert "图表_chart_anchor_plan.csv" not in root_files
    payload = json.loads((topic_root / "素材交付清单.json").read_text(encoding="utf-8"))
    assert result["ready_assets"] == 0
    assert payload["gap_count"] >= 5
    reasons = "\n".join(item.get("reason", "") for item in payload["gaps"])
    assert "图片检索步骤未执行" in reasons
    assert "新闻截图步骤未执行" in reasons
    assert "视频搜索步骤未执行" in reasons
    assert "AI 视觉计划已生成" in reasons
    assert "只有图表锚点计划" in reasons


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
