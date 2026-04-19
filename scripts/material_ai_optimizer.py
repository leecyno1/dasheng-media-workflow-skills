#!/usr/bin/env python3
"""
Material 环节的 AI 优化模块
包括动态图表门控和智能素材检索
"""

import json
from typing import Dict, List, Any


def ai_decide_chart_generation_prompt(data_point: Dict, context: str) -> str:
    """
    生成 AI 图表决策的 prompt

    Args:
        data_point: 数据点信息（包含数据、类型等）
        context: 上下文信息（文章段落、论证目标等）

    Returns:
        AI prompt 字符串
    """
    prompt = f"""判断以下数据是否需要可视化为图表：

【数据信息】
{json.dumps(data_point, ensure_ascii=False, indent=2)}

【上下文】
{context}

【判断标准】
1. 数据复杂度：
   - 是否有多个维度（时间序列、分类对比、相关性等）
   - 是否有大量数值需要对比
   - 文字描述是否难以清晰表达

2. 对论证的重要性：
   - 是否是核心证据
   - 是否是关键论点的支撑
   - 读者是否需要直观理解

3. 读者理解难度：
   - 纯文字描述是否足够清晰
   - 图表是否能显著提升理解效率
   - 是否有助于记忆和传播

【输出格式】
请输出 JSON 格式：
{{
  "should_generate": true/false,
  "chart_type": "折线图/柱状图/饼图/散点图/热力图/表格",
  "reason": "判断理由...",
  "priority": "high/medium/low",
  "alternative": "如果不生成图表，建议的文字表达方式"
}}

【图表类型选择指南】
- 折线图：时间序列、趋势变化
- 柱状图：分类对比、排名
- 饼图：占比、构成（不超过 5 个分类）
- 散点图：相关性、分布
- 热力图：多维度对比、矩阵数据
- 表格：精确数值、多属性对比

【决策原则】
- 优先考虑读者价值，不为了图表而图表
- 简单数据（1-3 个数值）用文字更清晰
- 复杂数据（5+ 个数值或多维度）用图表更直观
- 如果数据质量不足（缺失值多、噪音大），建议用表格而非图表
"""

    return prompt


def ai_optimize_search_query_prompt(paragraph: str, search_type: str = "image") -> str:
    """
    生成 AI 搜索关键词优化的 prompt

    Args:
        paragraph: 需要配图/配视频的段落
        search_type: 搜索类型（image/video）

    Returns:
        AI prompt 字符串
    """
    search_type_cn = "图片" if search_type == "image" else "视频"

    prompt = f"""为以下段落生成最佳{search_type_cn}搜索关键词：

【段落内容】
{paragraph}

【搜索类型】
{search_type_cn}搜索

【关键词要求】
1. 数量：3-5 个关键词
2. 语言：中英文结合（优先英文，因为素材库更丰富）
3. 精准度：能准确匹配段落主题
4. 多样性：包含同义词和相关词，提高命中率

【关键词类型】
- 核心概念：段落的主要主题
- 视觉元素：具体的物体、场景、人物
- 情绪/氛围：如果需要特定风格
- 行业术语：专业领域的标准用词

【输出格式】
请输出 JSON 格式：
{{
  "primary_keywords": ["主关键词1", "主关键词2"],
  "secondary_keywords": ["次要关键词1", "次要关键词2", "次要关键词3"],
  "english_keywords": ["English keyword 1", "English keyword 2"],
  "search_strategy": "搜索策略说明",
  "expected_results": "预期找到的素材类型"
}}

【示例】
段落：中东冲突导致霍尔木兹海峡封锁，全球能源供应链面临重大风险。

输出：
{{
  "primary_keywords": ["霍尔木兹海峡", "能源供应链"],
  "secondary_keywords": ["石油运输", "海峡封锁", "油轮"],
  "english_keywords": ["Strait of Hormuz", "oil tanker", "energy supply chain", "maritime chokepoint"],
  "search_strategy": "优先使用英文关键词搜索国际新闻图片，中文关键词搜索本地媒体素材",
  "expected_results": "海峡地图、油轮照片、供应链示意图"
}}

【注意事项】
- 避免过于宽泛的词（如"经济"、"市场"）
- 避免过于具体的词（如具体日期、人名，除非是知名人物）
- 考虑版权问题，优先搜索可商用的素材来源
- 如果是敏感话题，使用中性词汇
"""

    return prompt


def validate_chart_decision(decision: Dict) -> bool:
    """
    验证 AI 图表决策的合理性

    Args:
        decision: AI 返回的决策结果

    Returns:
        是否合理
    """
    required_fields = ['should_generate', 'chart_type', 'reason', 'priority']

    # 检查必需字段
    for field in required_fields:
        if field not in decision:
            return False

    # 检查图表类型
    valid_chart_types = ['折线图', '柱状图', '饼图', '散点图', '热力图', '表格']
    if decision['should_generate'] and decision['chart_type'] not in valid_chart_types:
        return False

    # 检查优先级
    if decision['priority'] not in ['high', 'medium', 'low']:
        return False

    # 检查理由长度
    if len(decision['reason']) < 10:
        return False

    return True


def validate_search_keywords(keywords: Dict) -> bool:
    """
    验证 AI 搜索关键词的合理性

    Args:
        keywords: AI 返回的关键词结果

    Returns:
        是否合理
    """
    required_fields = ['primary_keywords', 'secondary_keywords', 'english_keywords']

    # 检查必需字段
    for field in required_fields:
        if field not in keywords:
            return False
        if not isinstance(keywords[field], list):
            return False

    # 检查关键词数量
    total_keywords = len(keywords['primary_keywords']) + len(keywords['secondary_keywords'])
    if total_keywords < 3 or total_keywords > 8:
        return False

    # 检查是否有英文关键词
    if len(keywords['english_keywords']) < 1:
        return False

    return True


def merge_search_results(results_list: List[Dict]) -> List[Dict]:
    """
    合并多个搜索结果，去重并排序

    Args:
        results_list: 多个搜索结果列表

    Returns:
        合并后的结果
    """
    # 使用 URL 作为去重键
    seen_urls = set()
    merged = []

    for results in results_list:
        for item in results:
            url = item.get('url')
            if url and url not in seen_urls:
                seen_urls.add(url)
                merged.append(item)

    # 按相关性或质量排序（如果有评分）
    if merged and 'score' in merged[0]:
        merged.sort(key=lambda x: x.get('score', 0), reverse=True)

    return merged


def generate_chart_quality_report(decisions: List[Dict]) -> Dict:
    """
    生成图表决策质量报告

    Args:
        decisions: 所有图表决策列表

    Returns:
        质量报告
    """
    total = len(decisions)
    generated = sum(1 for d in decisions if d.get('should_generate'))
    high_priority = sum(1 for d in decisions if d.get('priority') == 'high')

    chart_types = {}
    for d in decisions:
        if d.get('should_generate'):
            chart_type = d.get('chart_type', 'unknown')
            chart_types[chart_type] = chart_types.get(chart_type, 0) + 1

    return {
        'total_data_points': total,
        'charts_to_generate': generated,
        'high_priority_charts': high_priority,
        'chart_type_distribution': chart_types,
        'generation_rate': f"{generated/total*100:.1f}%" if total > 0 else "0%"
    }


def generate_search_quality_report(search_results: List[Dict]) -> Dict:
    """
    生成素材搜索质量报告

    Args:
        search_results: 所有搜索结果

    Returns:
        质量报告
    """
    total_queries = len(search_results)
    total_results = sum(len(r.get('results', [])) for r in search_results)

    avg_results = total_results / total_queries if total_queries > 0 else 0

    return {
        'total_queries': total_queries,
        'total_results': total_results,
        'avg_results_per_query': f"{avg_results:.1f}",
        'queries_with_results': sum(1 for r in search_results if len(r.get('results', [])) > 0),
        'success_rate': f"{sum(1 for r in search_results if len(r.get('results', [])) > 0)/total_queries*100:.1f}%" if total_queries > 0 else "0%"
    }


if __name__ == "__main__":
    # 测试图表决策 prompt
    print("=== 图表决策 Prompt 示例 ===")
    data_point = {
        'type': 'time_series',
        'data': [
            {'date': '2026-01', 'value': 100},
            {'date': '2026-02', 'value': 120},
            {'date': '2026-03', 'value': 150}
        ],
        'description': '过去三个月的油价变化'
    }
    context = "文章段落：中东冲突爆发后，国际油价持续上涨。数据显示..."

    prompt = ai_decide_chart_generation_prompt(data_point, context)
    print(prompt)

    print("\n\n=== 搜索关键词优化 Prompt 示例 ===")
    paragraph = "霍尔木兹海峡是全球最重要的能源通道之一，每天有大量油轮通过。"

    prompt = ai_optimize_search_query_prompt(paragraph, "image")
    print(prompt)
