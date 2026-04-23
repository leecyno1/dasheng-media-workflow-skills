#!/usr/bin/env python3
"""
测试 Material Skill Adapter

测试策略：
1. Mock skill_invoker 返回值
2. 验证adapter正确构建payload
3. 验证adapter正确解析返回
4. 测试各种失败场景的graceful处理
"""

import json
import sys
from pathlib import Path
from unittest.mock import Mock, patch
import pytest

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from material_skill_adapter import MaterialSkillAdapter


@pytest.fixture
def mock_invoker():
    """创建mock invoker"""
    invoker = Mock()
    return invoker


def test_generate_infographic_success(mock_invoker):
    """测试：信息图生成成功"""
    # Mock返回值
    mock_invoker.invoke.return_value = {
        "success": True,
        "image_path": "/path/to/infographic.png",
        "description": "AI市场规模增长趋势图",
        "relevance_score": 0.9,
    }

    adapter = MaterialSkillAdapter(mock_invoker)
    result = adapter.generate_infographic(
        claim_text="AI市场规模持续增长",
        data_points=[{"year": 2023, "value": 100}],
        layout="linear-progression",
        style="technical-schematic",
    )

    # 验证调用参数
    mock_invoker.invoke.assert_called_once()
    call_args = mock_invoker.invoke.call_args
    assert call_args[0][0] == "baoyu-infographic"
    assert call_args[0][1]["content"] == "AI市场规模持续增长"
    assert call_args[0][1]["layout"] == "linear-progression"
    assert call_args[0][1]["style"] == "technical-schematic"

    # 验证返回值
    assert result["success"] is True
    assert result["image_path"] == "/path/to/infographic.png"
    assert result["relevance_score"] == 0.9


def test_generate_infographic_failure(mock_invoker):
    """测试：信息图生成失败"""
    mock_invoker.invoke.return_value = {
        "success": False,
        "error": "API quota exceeded",
    }

    adapter = MaterialSkillAdapter(mock_invoker)
    result = adapter.generate_infographic(
        claim_text="测试",
        data_points=[],
    )

    assert result["success"] is False
    assert "error" in result


def test_illustrate_section_success(mock_invoker):
    """测试：段落配图生成成功"""
    mock_invoker.invoke.return_value = {
        "success": True,
        "image_path": "/path/to/illustration.png",
        "alt_text": "AI技术架构示意图",
        "placement": "inline",
    }

    adapter = MaterialSkillAdapter(mock_invoker)
    result = adapter.illustrate_section(
        section_text="AI技术架构包括...",
        section_id="section-001",
        image_type="framework",
        style="notion",
    )

    # 验证调用参数
    call_args = mock_invoker.invoke.call_args
    assert call_args[0][0] == "baoyu-article-illustrator"
    assert call_args[0][1]["section_id"] == "section-001"
    assert call_args[0][1]["type"] == "framework"

    # 验证返回值
    assert result["success"] is True
    assert result["image_path"] == "/path/to/illustration.png"
    assert result["alt_text"] == "AI技术架构示意图"


def test_generate_cover_wechat(mock_invoker):
    """测试：微信封面生成"""
    mock_invoker.invoke.return_value = {
        "success": True,
        "image_path": "/path/to/cover.png",
        "design_notes": "使用warm色调，hero类型",
    }

    adapter = MaterialSkillAdapter(mock_invoker)
    result = adapter.generate_cover(
        article_title="AI技术发展趋势",
        article_summary="探讨AI技术的最新发展",
        platform="wechat",
        cover_type="hero",
        palette="warm",
    )

    # 验证调用参数
    call_args = mock_invoker.invoke.call_args
    assert call_args[0][0] == "baoyu-cover-image"
    assert call_args[0][1]["aspect"] == "16:9"  # 微信默认16:9
    assert call_args[0][1]["type"] == "hero"
    assert call_args[0][1]["palette"] == "warm"

    # 验证返回值
    assert result["success"] is True
    assert result["image_path"] == "/path/to/cover.png"


def test_generate_cover_xhs(mock_invoker):
    """测试：小红书封面生成（3:4宽高比）"""
    mock_invoker.invoke.return_value = {
        "success": True,
        "image_path": "/path/to/xhs_cover.png",
        "design_notes": "小红书竖版封面",
    }

    adapter = MaterialSkillAdapter(mock_invoker)
    result = adapter.generate_cover(
        article_title="测试标题",
        article_summary="测试摘要",
        platform="xhs",
    )

    # 验证宽高比
    call_args = mock_invoker.invoke.call_args
    assert call_args[0][1]["aspect"] == "3:4"  # 小红书3:4


def test_generate_xhs_images_success(mock_invoker):
    """测试：小红书图片系列生成成功"""
    mock_invoker.invoke.return_value = {
        "success": True,
        "images": [
            {"image_path": "/path/to/xhs_1.png", "caption": "第1张"},
            {"image_path": "/path/to/xhs_2.png", "caption": "第2张"},
            {"image_path": "/path/to/xhs_3.png", "caption": "第3张"},
        ],
    }

    adapter = MaterialSkillAdapter(mock_invoker)
    result = adapter.generate_xhs_images(
        content_sections=[
            {"title": "标题1", "content": "内容1"},
            {"title": "标题2", "content": "内容2"},
        ],
        style="notion",
        layout="balanced",
    )

    # 验证调用参数
    call_args = mock_invoker.invoke.call_args
    assert call_args[0][0] == "baoyu-xhs-images"
    assert call_args[0][1]["style"] == "notion"
    assert call_args[0][1]["layout"] == "balanced"

    # 验证返回值
    assert len(result) == 3
    assert result[0]["success"] is True
    assert result[0]["image_path"] == "/path/to/xhs_1.png"


def test_generate_xhs_images_failure(mock_invoker):
    """测试：小红书图片系列生成失败"""
    mock_invoker.invoke.return_value = {
        "success": False,
        "error": "Content too short",
    }

    adapter = MaterialSkillAdapter(mock_invoker)
    result = adapter.generate_xhs_images(
        content_sections=[],
    )

    assert len(result) == 1
    assert result[0]["success"] is False
    assert "error" in result[0]


def test_exception_handling(mock_invoker):
    """测试：异常处理"""
    mock_invoker.invoke.side_effect = Exception("Network error")

    adapter = MaterialSkillAdapter(mock_invoker)
    result = adapter.generate_infographic(
        claim_text="测试",
        data_points=[],
    )

    assert result["success"] is False
    assert "Network error" in result["error"]


def test_default_parameters(mock_invoker):
    """测试：默认参数"""
    mock_invoker.invoke.return_value = {"success": True}

    adapter = MaterialSkillAdapter(mock_invoker)

    # 测试信息图默认参数
    adapter.generate_infographic("测试", [])
    call_args = mock_invoker.invoke.call_args
    assert call_args[0][1]["layout"] == "bento-grid"
    assert call_args[0][1]["style"] == "craft-handmade"
    assert call_args[0][1]["aspect"] == "landscape"

    # 测试配图默认参数
    adapter.illustrate_section("测试", "sec-1")
    call_args = mock_invoker.invoke.call_args
    assert call_args[0][1]["type"] == "infographic"
    assert call_args[0][1]["style"] == "notion"

    # 测试封面默认参数
    adapter.generate_cover("标题", "摘要")
    call_args = mock_invoker.invoke.call_args
    assert call_args[0][1]["type"] == "hero"
    assert call_args[0][1]["palette"] == "warm"
    assert call_args[0][1]["rendering"] == "flat-vector"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
