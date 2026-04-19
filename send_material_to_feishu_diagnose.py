#!/usr/bin/env python3
"""
诊断问题块的内容
"""
import os
import sys
import json
import requests
from pathlib import Path

# Feishu 配置
APP_ID = "cli_a94d22306138dbc2"
APP_SECRET = "Zqi9eW7aaPt6ozcndlXHPeW4LDiA86hO"

DRAFT_BASE = "产物/05_初稿生成/2026-04-11_085602"

DOC_INFO = {
    "draft_file": "03_标准初稿_稳定币牌照落地-加密市场的-银行牌照时刻.md",
}

def get_token():
    url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
    resp = requests.post(url, json={"app_id": APP_ID, "app_secret": APP_SECRET}, timeout=10)
    return resp.json()["tenant_access_token"]

def convert_markdown(token, markdown):
    url = "https://open.feishu.cn/open-apis/docx/v1/documents/blocks/convert"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    data = {"content_type": "markdown", "content": markdown}
    resp = requests.post(url, headers=headers, json=data, timeout=10)
    result = resp.json()
    return result["data"].get("blocks", []), result["data"].get("first_level_block_ids", [])

def main():
    print("\n诊断问题块...\n")

    token = get_token()

    # 读取初稿
    draft_path = Path(DRAFT_BASE) / DOC_INFO["draft_file"]
    with open(draft_path, 'r', encoding='utf-8') as f:
        markdown = f.read()

    # 转换 blocks
    blocks, first_level_ids = convert_markdown(token, markdown)

    # 清理
    UNSUPPORTED = {31, 32}
    cleaned_blocks = [b for b in blocks if b.get("block_type") not in UNSUPPORTED]

    # 排序
    block_map = {b.get("block_id"): b for b in cleaned_blocks}
    sorted_blocks = [block_map[bid] for bid in first_level_ids if bid in block_map]
    remaining = [b for b in cleaned_blocks if b.get("block_id") not in set(first_level_ids)]
    sorted_blocks.extend(remaining)

    # Batch 3 索引
    batch3_start = 50 + 25
    batch3_blocks = sorted_blocks[batch3_start:batch3_start + 25]

    # 检查问题块
    problem_indices = [5, 6, 7]  # 0-indexed: blocks 6, 7, 8

    for idx in problem_indices:
        block = batch3_blocks[idx]
        print(f"\n{'='*70}")
        print(f"Problem Block {idx + 1}/25")
        print(f"{'='*70}")
        print(f"Block Type: {block.get('block_type')}")
        print(f"Block ID: {block.get('block_id')}")
        print(f"\nBlock Content (first 500 chars):")
        print(json.dumps(block, indent=2, ensure_ascii=False)[:500])
        print("\n")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n✗ 错误: {str(e)}\n")
        sys.exit(1)
