#!/usr/bin/env python3
"""
最终修复：跳过问题块，完成稳定币文档填充
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

DOC_INFO = {
    "doc_id": "VdDpdPZ6ToqIcoxFtPNceTTwnVg",
    "draft_file": "03_标准初稿_稳定币牌照落地-加密市场的-银行牌照时刻.md",
    "title": "稳定币牌照落地：加密市场的\"银行牌照时刻\"",
}

# 已知的问题块ID（从诊断中识别）
PROBLEM_BLOCK_IDS = {
    "94289957-d289-44f1-b9ca-209986157b0e",  # Block 6
    "bae2fd56-a814-413b-a01b-5dbc1c392c76",  # Block 7
    "0ef1e297-5aa7-4f40-9f3f-550186f50791"   # Block 8
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

def insert_blocks_with_filter(token, doc_id, blocks, batch_size=25):
    """插入 blocks，跳过问题块"""
    url = f"https://open.feishu.cn/open-apis/docx/v1/documents/{doc_id}/blocks/{doc_id}/children"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    # 过滤掉问题块
    filtered_blocks = [
        b for b in blocks
        if b.get("block_id") not in PROBLEM_BLOCK_IDS
    ]

    print(f"过滤后块数: {len(filtered_blocks)} (过滤掉 {len(blocks) - len(filtered_blocks)} 个问题块)")

    total_inserted = 0
    batch_count = 0

    for i in range(0, len(filtered_blocks), batch_size):
        batch_count += 1
        batch = filtered_blocks[i:i + batch_size]
        data = {"children": batch}

        print(f"\n批次 {batch_count}: 插入 {len(batch)} 个 blocks...")

        try:
            resp = requests.post(url, headers=headers, json=data, timeout=30)
            result = resp.json()

            if result.get("code") != 0:
                print(f"  ✗ 失败: {result.get('msg', result)}")
            else:
                inserted = result["data"].get("children", [])
                total_inserted += len(inserted)
                print(f"  ✓ 成功: 插入 {len(inserted)}/{len(batch)} 个 blocks")
        except Exception as e:
            print(f"  ✗ 异常: {str(e)}")

    return total_inserted

def main():
    print("\n" + "="*70)
    print("最终修复：完成稳定币文档填充")
    print("="*70)

    # 获取 token
    print("\n获取飞书 token...")
    token = get_token()
    print("✓ 认证成功")

    # 读取初稿
    draft_path = Path(DRAFT_BASE) / DOC_INFO["draft_file"]
    if not draft_path.exists():
        print(f"✗ 初稿文件不存在: {draft_path}")
        return

    with open(draft_path, 'r', encoding='utf-8') as f:
        markdown = f.read()

    print(f"✓ 读取初稿")

    # 转换 blocks
    blocks, first_level_ids = convert_markdown(token, markdown)
    print(f"✓ 转换 blocks: {len(blocks)} 个")

    # 清理不支持的 block 类型
    UNSUPPORTED = {31, 32}
    cleaned_blocks = [b for b in blocks if b.get("block_type") not in UNSUPPORTED]

    if len(cleaned_blocks) < len(blocks):
        print(f"⚠️  过滤不支持的 block 类型 ({len(blocks) - len(cleaned_blocks)} 个)")

    # 排序
    block_map = {b.get("block_id"): b for b in cleaned_blocks}
    sorted_blocks = [block_map[bid] for bid in first_level_ids if bid in block_map]
    remaining = [b for b in cleaned_blocks if b.get("block_id") not in set(first_level_ids)]
    sorted_blocks.extend(remaining)

    print(f"\n处理文档: {DOC_INFO['title']}")
    print(f"Doc ID: {DOC_INFO['doc_id']}")

    # 使用过滤和较小的批量大小重新插入Batch 3
    batch3_start = 50 + 25
    batch3_blocks = sorted_blocks[batch3_start:batch3_start + 25]

    print(f"\nBatch 3 原始块数: {len(batch3_blocks)}")
    total_inserted = insert_blocks_with_filter(
        token, DOC_INFO["doc_id"], batch3_blocks, batch_size=5
    )

    # 插入batch 4剩余块
    batch4_start = batch3_start + 25
    batch4_blocks = sorted_blocks[batch4_start:]

    if batch4_blocks:
        print(f"\nBatch 4 块数: {len(batch4_blocks)}")
        batch4_inserted = insert_blocks_with_filter(
            token, DOC_INFO["doc_id"], batch4_blocks, batch_size=5
        )
        total_inserted += batch4_inserted

    print(f"\n" + "="*70)
    print(f"✓ 完成：{total_inserted} 个块已插入")
    print(f"文档链接: https://bytedance.larkoffice.com/docx/{DOC_INFO['doc_id']}")
    print("="*70 + "\n")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n✗ 错误: {str(e)}\n")
        sys.exit(1)
