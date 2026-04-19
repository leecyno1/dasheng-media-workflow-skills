#!/usr/bin/env python3
"""
隔离batch 3中的问题块
"""
import os
import sys
import json
import requests
from pathlib import Path

# Feishu 配置
APP_ID = "cli_a94d22306138dbc2"
APP_SECRET = "Zqi9eW7aaPt6ozcndlXHPeW4LDiA86hO"
CHAT_ID = "oc_975d43c5704bf8c755bb9e32bf7c3922"

DRAFT_BASE = "产物/05_初稿生成/2026-04-11_085602"

# 稳定币文档配置
DOC_INFO = {
    "doc_id": "VdDpdPZ6ToqIcoxFtPNceTTwnVg",
    "draft_file": "03_标准初稿_稳定币牌照落地-加密市场的-银行牌照时刻.md",
    "title": "稳定币牌照落地：加密市场的\"银行牌照时刻\"",
}

def get_token():
    """获取飞书 token"""
    url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
    resp = requests.post(url, json={"app_id": APP_ID, "app_secret": APP_SECRET}, timeout=10)
    result = resp.json()
    if result.get("code") != 0:
        raise Exception(f"获取 token 失败: {result}")
    return result["tenant_access_token"]

def convert_markdown(token, markdown):
    """Markdown 转 blocks"""
    url = "https://open.feishu.cn/open-apis/docx/v1/documents/blocks/convert"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    data = {"content_type": "markdown", "content": markdown}

    resp = requests.post(url, headers=headers, json=data, timeout=10)
    result = resp.json()
    if result.get("code") != 0:
        raise Exception(f"转换 markdown 失败: {result}")

    return result["data"].get("blocks", []), result["data"].get("first_level_block_ids", [])

def try_insert_single_block(token, doc_id, block, block_index):
    """尝试插入单个块"""
    url = f"https://open.feishu.cn/open-apis/docx/v1/documents/{doc_id}/blocks/{doc_id}/children"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    data = {"children": [block]}

    try:
        resp = requests.post(url, headers=headers, json=data, timeout=30)
        result = resp.json()

        if result.get("code") != 0:
            return False, result.get('msg', str(result))
        return True, None
    except Exception as e:
        return False, str(e)

def main():
    print("\n" + "="*70)
    print("隔离 Batch 3 中的问题块")
    print("="*70)

    token = get_token()
    print("✓ 认证成功\n")

    # 读取初稿
    draft_path = Path(DRAFT_BASE) / DOC_INFO["draft_file"]
    with open(draft_path, 'r', encoding='utf-8') as f:
        markdown = f.read()

    # 转换 blocks
    blocks, first_level_ids = convert_markdown(token, markdown)
    print(f"✓ 转换 blocks: {len(blocks)} 个\n")

    # 清理不支持的 block 类型
    UNSUPPORTED = {31, 32}
    cleaned_blocks = [b for b in blocks if b.get("block_type") not in UNSUPPORTED]

    # 排序
    block_map = {b.get("block_id"): b for b in cleaned_blocks}
    sorted_blocks = [block_map[bid] for bid in first_level_ids if bid in block_map]
    remaining = [b for b in cleaned_blocks if b.get("block_id") not in set(first_level_ids)]
    sorted_blocks.extend(remaining)

    # Batch 3 是从索引 50+25=75 开始的 25 个块
    batch3_start = 50 + 25  # 前两个批次各 50 和 25
    batch3_blocks = sorted_blocks[batch3_start:batch3_start + 25]

    print(f"检测 Batch 3 中的 {len(batch3_blocks)} 个块...\n")

    bad_blocks = []
    for i, block in enumerate(batch3_blocks):
        block_id = block.get("block_id", "unknown")
        block_type = block.get("block_type", "unknown")
        success, error = try_insert_single_block(token, DOC_INFO["doc_id"], block, batch3_start + i)

        if success:
            print(f"  ✓ Block {i+1}/{len(batch3_blocks)}: {block_type} (ID: {block_id[:20]}...)")
        else:
            print(f"  ✗ Block {i+1}/{len(batch3_blocks)}: {block_type} - {error[:60]}")
            bad_blocks.append({
                "index": i,
                "type": block_type,
                "id": block_id,
                "error": error
            })

    print(f"\n" + "="*70)
    print(f"结果: {len(batch3_blocks) - len(bad_blocks)}/{len(batch3_blocks)} 块成功插入")

    if bad_blocks:
        print(f"\n问题块:")
        for bb in bad_blocks:
            print(f"  - Block {bb['index']+1}: type={bb['type']}, error={bb['error'][:50]}")
    else:
        print(f"\n✓ 所有块都成功插入！")

    print("="*70 + "\n")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n✗ 错误: {str(e)}\n")
        sys.exit(1)
