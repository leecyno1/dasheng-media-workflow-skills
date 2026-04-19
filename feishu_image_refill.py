#!/usr/bin/env python3
import requests
import json
import os
import re
from pathlib import Path

# Feishu 配置
APP_ID = "cli_a94d22306138dbc2"
APP_SECRET = "Zqi9eW7aaPt6ozcndlXHPeW4LDiA86hO"
TENANT_KEY = "148d64ebcd00d740"

# 文档配置
DOCS = [
    {
        "doc_id": "AN4wdjoG3oNsq9xLKajcRj9xnTb",
        "draft_file": "03_标准初稿_claude新模型引发华尔街紧急会议-ai对金融业的风险在哪.md",
        "topic_slug": "claude华尔街紧急会议",
        "title": "Claude新模型引发华尔街紧急会议"
    },
    {
        "doc_id": "VdDpdPZ6ToqIcoxFtPNceTTwnVg",
        "draft_file": "03_标准初稿_稳定币牌照落地-加密市场的-银行牌照时刻.md",
        "topic_slug": "稳定币牌照",
        "title": "稳定币牌照落地"
    },
    {
        "doc_id": "XnGudUQaho7Kg0xGTEkcxdcWn8b",
        "draft_file": "03_标准初稿_日本士兵闯使馆事件背后-个体极端行为还是系统性问题.md",
        "topic_slug": "日本士兵闯使馆",
        "title": "日本士兵闯使馆事件背后"
    }
]

MATERIAL_BASE = "产物/04_素材收集/2026-04-11_085602/pack_assets"

class FeishuRefill:
    def __init__(self):
        self.tenant_key = TENANT_KEY
        self.access_token = self._get_access_token()

    def _get_access_token(self):
        """获取飞书 access_token"""
        url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
        payload = {
            "app_id": APP_ID,
            "app_secret": APP_SECRET
        }
        resp = requests.post(url, json=payload)
        data = resp.json()
        if data.get("code") == 0:
            return data["tenant_access_token"]
        else:
            raise Exception(f"获取 token 失败: {data}")

    def _upload_image_to_feishu(self, doc_id, image_path):
        """上传图片到飞书并返回 image_token"""
        url = f"https://open.feishu.cn/open-apis/drive/v1/files/upload_all"

        headers = {
            "Authorization": f"Bearer {self.access_token}"
        }

        with open(image_path, 'rb') as f:
            files = {
                'file': (os.path.basename(image_path), f)
            }
            data = {
                'file_name': os.path.basename(image_path),
                'parent_type': 'doc',
                'parent_node': doc_id
            }
            resp = requests.post(url, headers=headers, files=files, data=data)
            result = resp.json()

        if result.get("code") == 0:
            file_token = result["data"]["file_token"]
            print(f"  ✓ 上传成功: {os.path.basename(image_path)} -> {file_token}")
            return file_token
        else:
            print(f"  ✗ 上传失败: {result}")
            return None

    def _extract_image_anchors(self, topic_slug):
        """从初稿中提取配图锚点"""
        draft_dir = Path("产物/05_初稿生成/2026-04-11_085602")
        anchors = []

        # 查找匹配的初稿文件
        for draft_file in draft_dir.glob(f"*{topic_slug}*.md"):
            if "03_标准初稿" in draft_file.name:
                with open(draft_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # 提取 {{image: 描述}} 格式
                    pattern = r'{{image: (.+?)}}'
                    matches = re.findall(pattern, content)
                    anchors.extend(matches)
                    print(f"  文件: {draft_file.name}")
                    print(f"  找到 {len(matches)} 个锚点")

        return anchors

    def _get_images_from_assets(self, topic_slug):
        """获取素材包中对应主题的图片"""
        assets_dir = Path(MATERIAL_BASE) / topic_slug
        images = []

        if (assets_dir / "infographic").exists():
            # 获取信息图
            for img in (assets_dir / "infographic").glob("*.png"):
                images.append(img)

        # 获取其他配图（jpg, png）
        for img in assets_dir.glob("*.jpg"):
            images.append(img)
        for img in assets_dir.glob("*.png"):
            if img.parent.name != "infographic":
                images.append(img)

        return sorted(images)[:10]  # 最多取10张

    def refill_doc(self, doc_info):
        """回填单个文档"""
        doc_id = doc_info["doc_id"]
        draft_file = doc_info["draft_file"]
        topic_slug = doc_info["topic_slug"]
        title = doc_info["title"]

        print(f"\n处理: {title}")
        print(f"Doc ID: {doc_id}")

        # 获取配图锚点
        anchors = self._extract_image_anchors(draft_file)
        print(f"  锚点数: {len(anchors)}")

        # 获取素材图片
        images = self._get_images_from_assets(topic_slug)
        print(f"  可用图片: {len(images)}")

        # 上传图片
        for idx, image_path in enumerate(images[:len(anchors)]):
            file_token = self._upload_image_to_feishu(doc_id, str(image_path))
            if file_token:
                print(f"    [{idx+1}/{len(anchors)}] {image_path.name}")

        print(f"  ✓ {title} 回填完成")

    def run(self):
        """执行所有文档回填"""
        print("="*50)
        print("飞书图片回填开始")
        print("="*50)

        for doc_info in DOCS:
            self.refill_doc(doc_info)

        print("\n" + "="*50)
        print("✓ 所有文档回填完成")
        print("="*50)

if __name__ == "__main__":
    try:
        refill = FeishuRefill()
        refill.run()
    except Exception as e:
        print(f"✗ 错误: {str(e)}")
