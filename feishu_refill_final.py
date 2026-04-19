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

    def _upload_image_and_get_token(self, doc_id, image_path):
        """上传图片到飞书，获取 image_key"""
        url = "https://open.feishu.cn/open-apis/drive/v1/files/upload_all"
        headers = {"Authorization": f"Bearer {self.access_token}"}

        try:
            # 上传文件到云存储
            with open(image_path, 'rb') as f:
                files = {'file': (os.path.basename(image_path), f)}
                data = {
                    'file_name': os.path.basename(image_path),
                    'parent_type': 'docx',
                    'parent_node': doc_id
                }
                resp = requests.post(url, headers=headers, files=files, data=data, timeout=30)
                result = resp.json()

            if result.get("code") == 0:
                file_token = result["data"]["file_token"]
                print(f"  ✓ {os.path.basename(image_path):40} -> {file_token[:20]}...")
                return file_token
            else:
                print(f"  ✗ 上传失败: {result.get('msg', result)}")
                return None
        except Exception as e:
            print(f"  ✗ 错误: {str(e)}")
            return None

    def insert_image_to_doc(self, doc_id, image_token, anchor_text):
        """在飞书文档中插入图片"""
        url = f"https://open.feishu.cn/open-apis/docx/v1/document_blocks/batch_create"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }

        # 使用图片块插入
        payload = {
            "document_id": doc_id,
            "blocks": [{
                "paragraph": {
                    "elements": [{
                        "file": {"file_token": image_token}
                    }],
                    "style": {"align": 1}  # 居中
                }
            }]
        }

        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=30)
            result = resp.json()

            if result.get("code") == 0:
                print(f"    ✓ 图片已插入文档")
                return True
            else:
                print(f"    ✗ 插入失败: {result.get('msg', result)}")
                return False
        except Exception as e:
            print(f"    ✗ 错误: {str(e)}")
            return False

    def refill_doc(self, doc_info):
        """回填单个文档"""
        doc_id = doc_info["doc_id"]
        draft_file = doc_info["draft_file"]
        topic_slug = doc_info["topic_slug"]
        title = doc_info["title"]

        print(f"\n{'='*70}")
        print(f"处理: {title}")
        print(f"Doc ID: {doc_id}")
        print(f"{'='*70}")

        # 读取初稿
        draft_path = Path(DRAFT_BASE) / draft_file
        if not draft_path.exists():
            print(f"  ✗ 初稿文件不存在: {draft_path}")
            return

        with open(draft_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 提取所有 {{image: 描述}} 锚点
        pattern = r'{{image: ([^}]+)}}'
        anchors = re.findall(pattern, content)
        print(f"  找到 {len(anchors)} 个配图锚点")

        if not anchors:
            print(f"  ⚠ 没有配图锚点，跳过")
            return

        # 获取对应主题的图片
        assets_dir = Path(MATERIAL_BASE) / topic_slug
        images = []

        # 收集所有图片
        for img in sorted(assets_dir.glob("*.jpg")):
            images.append(img)
        for img in sorted(assets_dir.glob("*.png")):
            images.append(img)

        print(f"  可用图片: {len(images)} 张\n")

        if not images:
            print(f"  ✗ 没有找到素材图片")
            return

        # 上传和插入图片
        print(f"上传图片:")
        inserted_count = 0
        for idx, image_path in enumerate(images[:len(anchors)]):
            anchor_text = anchors[idx]
            print(f"  [{idx+1}/{len(anchors)}] {anchor_text[:40]}...")

            # 上传图片
            file_token = self._upload_image_and_get_token(doc_id, str(image_path))
            if file_token:
                # 插入到文档
                if self.insert_image_to_doc(doc_id, file_token, anchor_text):
                    inserted_count += 1

        print(f"\n✓ {title} 完成 ({inserted_count}/{len(anchors)} 个配图已插入)")

    def run(self):
        """执行所有文档回填"""
        print("\n" + "#"*70)
        print("# 飞书图片回填")
        print("#"*70)

        for doc_info in DOCS:
            self.refill_doc(doc_info)

        print("\n" + "#"*70)
        print("# ✓ 所有文档回填完成")
        print("#"*70 + "\n")

if __name__ == "__main__":
    try:
        refill = FeishuRefill()
        refill.run()
    except Exception as e:
        print(f"\n✗ 致命错误: {str(e)}\n")
