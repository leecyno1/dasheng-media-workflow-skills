#!/usr/bin/env python3
import requests
import json
import os
from datetime import datetime

API_KEY = "sk-ItG7HCeFmOjiHTKaeA6pPZoEh6y8KWpneIOhYG8lJpEtbtaK"
API_URL = "https://api.viviai.cc/v1/chat/completions"
BASE_OUTPUT = "产物/04_素材收集/2026-04-11_085602/pack_assets"

topics = [
    {
        "slug": "claude华尔街紧急会议",
        "title": "Claude新模型引发华尔街紧急会议：AI对金融业的风险在哪",
        "prompt": "为《Claude新模型引发华尔街紧急会议：AI对金融业的风险在哪》生成专业信息图。内容应包含：1.AI模型风险传导链条(AI->交易->市场波动)、2.金融监管方框架、3.风险等级分布。风格：企业风格、蓝色/灰色配色、清晰的流程图。返回生成的信息图URL或base64图像。"
    },
    {
        "slug": "稳定币牌照",
        "title": "稳定币牌照落地：加密市场的银行牌照时刻",
        "prompt": "为《稳定币牌照落地：加密市场的银行牌照时刻》生成专业信息图。内容应包含：1.稳定币市场份额对比(USDT/USDC/其他)、2.传统金融机构布局时间线、3.监管框架演进。风格：现代简约、绿色/蓝色配色、数据驱动。返回生成的信息图URL或base64图像。"
    },
    {
        "slug": "日本士兵闯使馆",
        "title": "日本士兵闯使馆事件背后：个体极端行为还是系统性问题？",
        "prompt": "为《日本士兵闯使馆事件背后：个体极端行为还是系统性问题？》生成专业信息图。内容应包含：1.自卫队历年纪律事故趋势、2.右翼势力对军队的渗透路径、3.事件关键时间线。风格：新闻风格、中性配色、层次清晰。返回生成的信息图URL或base64图像。"
    }
]

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

def generate_infographic(topic_data):
    """使用生图API生成信息图"""
    payload = {
        "model": "gemini-3.1-flash-image-preview",
        "messages": [
            {
                "role": "user",
                "content": topic_data["prompt"]
            }
        ],
        "max_tokens": 2000,
        "temperature": 0.7
    }

    try:
        print(f"\n生成信息图: {topic_data['slug']}...")
        response = requests.post(API_URL, json=payload, headers=headers, timeout=60)

        if response.status_code == 200:
            result = response.json()
            print(f"✓ 成功生成 {topic_data['slug']}")
            return result
        else:
            print(f"✗ 失败 [{response.status_code}]: {response.text}")
            return None
    except Exception as e:
        print(f"✗ 错误: {str(e)}")
        return None

def save_results():
    """生成所有信息图"""
    results = []

    for topic in topics:
        result = generate_infographic(topic)
        if result:
            results.append({
                "slug": topic["slug"],
                "title": topic["title"],
                "status": "success",
                "response": result
            })
        else:
            results.append({
                "slug": topic["slug"],
                "title": topic["title"],
                "status": "failed"
            })

    # 保存结果
    output_file = f"{BASE_OUTPUT}/../infographic_results.json"
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            "generated_at": datetime.now().isoformat(),
            "total": len(topics),
            "success": sum(1 for r in results if r["status"] == "success"),
            "results": results
        }, f, ensure_ascii=False, indent=2)

    print(f"\n结果已保存到: {output_file}")
    return results

if __name__ == "__main__":
    save_results()
