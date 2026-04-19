#!/usr/bin/env python3
"""
Material Skill Adapter - 素材生成技能适配层

将 baoyu-* 图像生成 skills 集成到 Material 阶段。
通过 skill_invoker 调用 OpenClaw skills 生成高质量视觉素材。
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from skill_invoker import SkillInvoker


class MaterialSkillAdapter:
    """素材生成技能适配器"""

    def __init__(self, invoker: SkillInvoker | None = None):
        self.invoker = invoker or SkillInvoker()

    def generate_infographic(
        self,
        claim_text: str,
        data_points: list[dict[str, Any]],
        layout: str = "bento-grid",
        style: str = "craft-handmade",
        aspect: str = "landscape",
    ) -> dict[str, Any]:
        """
        生成信息图（Infographic）

        Args:
            claim_text: 论断文本
            data_points: 数据点列表
            layout: 布局类型（21种可选）
            style: 视觉风格（20种可选）
            aspect: 宽高比（landscape/portrait/square）

        Returns:
            {
                "success": bool,
                "image_path": str,
                "description": str,
                "relevance_score": float
            }
        """
        payload = {
            "content": claim_text,
            "data_points": data_points,
            "layout": layout,
            "style": style,
            "aspect": aspect,
        }

        try:
            result = self.invoker.invoke("baoyu-infographic", payload)
            if result.get("success"):
                return {
                    "success": True,
                    "image_path": result.get("image_path", ""),
                    "description": result.get("description", ""),
                    "relevance_score": result.get("relevance_score", 0.8),
                }
            else:
                return {
                    "success": False,
                    "error": result.get("error", "Unknown error"),
                }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def illustrate_section(
        self,
        section_text: str,
        section_id: str,
        image_type: str = "infographic",
        style: str = "notion",
    ) -> dict[str, Any]:
        """
        为文章段落生成配图

        Args:
            section_text: 段落文本
            section_id: 段落ID
            image_type: 图像类型（infographic/scene/flowchart/comparison/framework/timeline）
            style: 视觉风格

        Returns:
            {
                "success": bool,
                "image_path": str,
                "alt_text": str,
                "placement": str
            }
        """
        payload = {
            "content": section_text,
            "section_id": section_id,
            "type": image_type,
            "style": style,
        }

        try:
            result = self.invoker.invoke("baoyu-article-illustrator", payload)
            if result.get("success"):
                return {
                    "success": True,
                    "image_path": result.get("image_path", ""),
                    "alt_text": result.get("alt_text", ""),
                    "placement": result.get("placement", "inline"),
                }
            else:
                return {
                    "success": False,
                    "error": result.get("error", "Unknown error"),
                }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def generate_cover(
        self,
        article_title: str,
        article_summary: str,
        platform: str = "wechat",
        cover_type: str = "hero",
        palette: str = "warm",
        rendering: str = "flat-vector",
    ) -> dict[str, Any]:
        """
        生成文章封面

        Args:
            article_title: 文章标题
            article_summary: 文章摘要
            platform: 平台（wechat/xhs）
            cover_type: 封面类型（hero/conceptual/typography/metaphor/scene/minimal）
            palette: 色彩方案（warm/elegant/cool/dark/earth/vivid/pastel/mono/retro）
            rendering: 渲染风格（flat-vector/hand-drawn/painterly/digital/pixel/chalk）

        Returns:
            {
                "success": bool,
                "image_path": str,
                "design_notes": str
            }
        """
        # 根据平台调整宽高比
        aspect_map = {
            "wechat": "16:9",
            "xhs": "3:4",
            "douyin": "9:16",
        }
        aspect = aspect_map.get(platform, "16:9")

        payload = {
            "title": article_title,
            "summary": article_summary,
            "type": cover_type,
            "palette": palette,
            "rendering": rendering,
            "aspect": aspect,
            "text": "title-subtitle",
        }

        try:
            result = self.invoker.invoke("baoyu-cover-image", payload)
            if result.get("success"):
                return {
                    "success": True,
                    "image_path": result.get("image_path", ""),
                    "design_notes": result.get("design_notes", ""),
                }
            else:
                return {
                    "success": False,
                    "error": result.get("error", "Unknown error"),
                }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def generate_xhs_images(
        self,
        content_sections: list[dict[str, str]],
        style: str = "notion",
        layout: str = "balanced",
    ) -> list[dict[str, Any]]:
        """
        生成小红书图片系列（1-10张）

        Args:
            content_sections: 内容段落列表 [{"title": "...", "content": "..."}]
            style: 视觉风格（cute/fresh/warm/bold/minimal/retro/pop/notion/chalkboard/study-notes）
            layout: 布局类型（sparse/balanced/dense/list/comparison/flow/mindmap/quadrant）

        Returns:
            [
                {
                    "success": bool,
                    "image_path": str,
                    "caption": str
                }
            ]
        """
        payload = {
            "content_sections": content_sections,
            "style": style,
            "layout": layout,
        }

        try:
            result = self.invoker.invoke("baoyu-xhs-images", payload)
            if result.get("success"):
                images = result.get("images", [])
                return [
                    {
                        "success": True,
                        "image_path": img.get("image_path", ""),
                        "caption": img.get("caption", ""),
                    }
                    for img in images
                ]
            else:
                return [{"success": False, "error": result.get("error", "Unknown error")}]
        except Exception as e:
            return [{"success": False, "error": str(e)}]


# ─── 便捷函数 ──────────────────────────────────────────────────────────────────

def create_adapter() -> MaterialSkillAdapter:
    """创建默认适配器实例"""
    return MaterialSkillAdapter()


if __name__ == "__main__":
    # 测试用例
    adapter = create_adapter()

    # 测试信息图生成
    print("测试信息图生成...")
    result = adapter.generate_infographic(
        claim_text="AI市场规模持续增长",
        data_points=[
            {"year": 2023, "value": 100},
            {"year": 2024, "value": 150},
            {"year": 2025, "value": 220},
        ],
        layout="linear-progression",
        style="technical-schematic",
    )
    print(f"结果: {result}")

    # 测试封面生成
    print("\n测试封面生成...")
    result = adapter.generate_cover(
        article_title="AI技术发展趋势",
        article_summary="探讨人工智能技术的最新发展和未来方向",
        platform="wechat",
        cover_type="hero",
        palette="warm",
    )
    print(f"结果: {result}")
