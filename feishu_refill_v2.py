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
DRAFT_BASE = "产物/05_初稿生成/2026-04-11_085602"

class FeishuRefill:
    def __init__(self):
        self.tenant_key = TENANT_KEY
        self.access_token = self._get_access_token()

    def _get_access_token(self):
        """获取飞书 access_token"""
        url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
        payload = {"app_id": APP_ID, "app_secret": APP_SECRET}
        resp = requests.post(url, json=payload, timeout=10)
        data = resp.json()
        if data.get("code") == 0:
            print(f"✓ 获取 token 成功")
            return data["tenant_access_token"]
        else:
            raise Exception(f"获取 token 失败: {data}")

    def _upload_image_to_feishu(self, doc_id, image_path):
        """上传图片到飞书文档"""
        # 使用 bitable attachment 上传
        url = "https://open.feishu.cn/open-apis/core.document_block.image/upload"
        headers = {"Authorization": f"Bearer {self.access_token}"}

        try:
            with open(image_path, 'rb') as f:
                files = {'image': (os.path.basename(image_path), f, 'image/jpeg')}
                data = {'document_id': doc_id}
                resp = requests.post(url, headers=headers, files=files, data=data, timeout=30)
                result = resp.json()

            if result.get("code") == 0:
                file_token = result["data"]["file_token"]
                print(f"  ✓ {os.path.basename(image_path):40} -> {file_token}")
                return file_token
            else:
                print(f"  ✗ 上传失败: {result.get('msg')}")
                return None
        except Exception as e:
            print(f"  ✗ 错误: {str(e)}")
            return None

    def extract_anchors_and_images(self, draft_file_name, topic_slug):
        """提取锚点和对应的图片"""
        # 读取初稿
        draft_path = Path(DRAFT_BASE) / draft_file_name
        if not draft_path.exists():
            print(f"  ✗ 初稿文件不存在: {draft_path}")
            return [], []

        with open(draft_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 提取所有 {{image: 描述}} 锚点
        pattern = r'{{image: ([^}]+)}}'
        anchors = re.findall(pattern, content)
        print(f"  找到 {len(anchors)} 个配图锚点")

        # 获取对应主题的所有图片
        assets_dir = Path(MATERIAL_BASE) / topic_slug
        images = []

        # 优先使用信息图
        if (assets_dir / "infographic").exists():
            for img in (assets_dir / "infographic").glob("*.png"):
                images.append(img)
                print(f"    [信息图] {img.name}")

        # 添加其他配图
        for img in sorted(assets_dir.glob("*.jpg")):
            images.append(img)
            print(f"    [配图] {img.name}")
        for img in sorted(assets_dir.glob("*.png")):
            if not any(str(img).startswith(str(assets_dir / "infographic")) for _ in [None]):
                images.append(img)

        print(f"  可用图片: {len(images)} 张")
        return anchors, images

    def refill_doc(self, doc_info):
        """回填单个文档"""
        doc_id = doc_info["doc_id"]
        draft_file = doc_info["draft_file"]
        topic_slug = doc_info["topic_slug"]
        title = doc_info["title"]

        print(f"\n{'='*60}")
        print(f"处理: {title}")
        print(f"Doc ID: {doc_id}")
        print(f"{'='*60}")

        # 提取锚点和图片
        anchors, images = self.extract_anchors_and_images(draft_file, topic_slug)

        if not anchors:
            print(f"  ⚠ 没有找到配图锚点")
            return

        # 上传图片
        print(f"\n上传图片:")
        uploaded_count = 0
        for idx, image_path in enumerate(images[:len(anchors)]):
            file_token = self._upload_image_to_feishu(doc_id, str(image_path))
            if file_token:
                uploaded_count += 1

        print(f"\n✓ {title} 完成 ({uploaded_count}/{len(anchors)} 个配图已上传)")

    def run(self):
        """执行所有文档回填"""
        print("\n" + "#"*60)
        print("# 飞书图片回填")
        print("#"*60)

        for doc_info in DOCS:
            self.refill_doc(doc_info)

        print("\n" + "#"*60)
        print("# ✓ 所有文档回填完成")
        print("#"*60 + "\n")

if __name__ == "__main__":
    try:
        refill = FeishuRefill()
        refill.run()
    except Exception as e:
        print(f"\n✗ 致命错误: {str(e)}\n")
