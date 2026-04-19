#!/usr/bin/env python3
"""
飞书图片上传与回填
"""
import os
import sys
import json
import requests
from pathlib import Path

# Feishu 配置
APP_ID = "cli_a94d22306138dbc2"
APP_SECRET = "Zqi9eW7aaPt6ozcndlXHPeW4LDiA86hO"

DOCS = [
    {
        "doc_id": "Eih2dXqckoxGqEx8Nv0cqst2nob",
        "topic_slug": "claude华尔街紧急会议",
        "title": "Claude新模型引发华尔街紧急会议",
        "images": [
            "01_claude华尔街紧急会议_纽约联储大楼.jpg",
            "02_claude华尔街紧急会议_美联储财政部AI.jpg",
            "03_claude华尔街紧急会议_会议室场景.jpg",
            "04_claude华尔街紧急会议_风险传导链条.jpg",
            "05_claude华尔街紧急会议_AI与法律天平.jpg"
        ]
    }
]

MATERIAL_BASE = "产物/04_素材收集/2026-04-11_085602/pack_assets"

def get_token():
    """获取飞书 token"""
    url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
    resp = requests.post(url, json={"app_id": APP_ID, "app_secret": APP_SECRET}, timeout=10)
    result = resp.json()
    if result.get("code") != 0:
        raise Exception(f"获取 token 失败: {result}")
    return result["tenant_access_token"]

def upload_image(token, doc_id, image_path):
    """上传图片到飞书"""
    url = "https://open.feishu.cn/open-apis/drive/v1/files/upload_all"
    headers = {"Authorization": f"Bearer {token}"}

    try:
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
            print(f"  ✓ 上传成功: {os.path.basename(image_path)} -> {file_token[:20]}...")
            return file_token
        else:
            print(f"  ✗ 上传失败: {result.get('msg', result)}")
            return None
    except Exception as e:
        print(f"  ✗ 异常: {str(e)}")
        return None

def insert_image_block(token, doc_id, file_token):
    """在文档末尾插入图片块"""
    url = f"https://open.feishu.cn/open-apis/docx/v1/document_blocks/batch_create"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    payload = {
        "document_id": doc_id,
        "blocks": [{
            "paragraph": {
                "elements": [{
                    "file": {"file_token": file_token}
                }],
                "style": {"align": 1}  # 居中
            }
        }]
    }

    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=30)
        result = resp.json()

        if result.get("code") == 0:
            print(f"    ✓ 图片块已插入")
            return True
        else:
            print(f"    ✗ 插入失败: {result.get('msg', result)}")
            return False
    except Exception as e:
        print(f"    ✗ 异常: {str(e)}")
        return False

def main():
    print("\n" + "="*70)
    print("飞书图片上传与回填")
    print("="*70)

    token = get_token()
    print("✓ 认证成功\n")

    for doc_info in DOCS:
        doc_id = doc_info["doc_id"]
        topic_slug = doc_info["topic_slug"]
        title = doc_info["title"]
        images = doc_info["images"]

        print(f"\n处理: {title}")
        print(f"Doc ID: {doc_id}")
        print(f"\n上传图片:")

        assets_dir = Path(MATERIAL_BASE) / topic_slug
        uploaded_count = 0

        for img_file in images:
            img_path = assets_dir / img_file
            if not img_path.exists():
                print(f"  ✗ 文件不存在: {img_path}")
                continue

            print(f"  [{uploaded_count + 1}/{len(images)}] {img_file}")

            # 上传图片
            file_token = upload_image(token, doc_id, str(img_path))
            if file_token:
                # 插入图片块
                if insert_image_block(token, doc_id, file_token):
                    uploaded_count += 1

        print(f"\n✓ 完成: {uploaded_count}/{len(images)} 张图片已上传")

    print(f"\n" + "="*70)
    print(f"✓ 所有图片回填完成")
    print("="*70 + "\n")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n✗ 错误: {str(e)}\n")
        sys.exit(1)
