#!/usr/bin/env python3
"""
修复稳定币文档：重试失败的批次，使用更小的批量大小
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
    "doc_id": "VdDpdPZ6ToqIcoxFtPNceTTwnVg",  # 已创建的文档ID
    "draft_file": "03_标准初稿_稳定币牌照落地-加密市场的-银行牌照时刻.md",
    "title": "稳定币牌照落地：加密市场的\"银行牌照时刻\"",
    "stage_emoji": "💰"
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

def insert_blocks_with_retry(token, doc_id, blocks, start_batch=2, batch_size=25):
    """插入 blocks，从指定批次开始，使用更小的批量大小"""
    url = f"https://open.feishu.cn/open-apis/docx/v1/documents/{doc_id}/blocks/{doc_id}/children"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    total_inserted = 0
    failed_batches = []

    # 计算起始位置（前面已经插入的块数）
    start_index = (start_batch - 1) * 50
    remaining_blocks = blocks[start_index:]

    print(f"\n从批次 {start_batch} 开始重试，使用批量大小 {batch_size}")
    print(f"剩余块数: {len(remaining_blocks)}")

    for i in range(0, len(remaining_blocks), batch_size):
        batch_num = start_batch + (i // batch_size)
        batch = remaining_blocks[i:i + batch_size]
        data = {"children": batch}

        print(f"\n批次 {batch_num}: 插入 {len(batch)} 个 blocks...")

        try:
            resp = requests.post(url, headers=headers, json=data, timeout=30)
            result = resp.json()

            if result.get("code") != 0:
                print(f"  ✗ 失败: {result.get('msg', result)}")
                failed_batches.append({
                    "batch": batch_num,
                    "size": len(batch),
                    "error": result.get('msg', str(result))
                })
            else:
                inserted = result["data"].get("children", [])
                total_inserted += len(inserted)
                print(f"  ✓ 成功: 插入 {len(inserted)}/{len(batch)} 个 blocks")
        except Exception as e:
            print(f"  ✗ 异常: {str(e)}")
            failed_batches.append({
                "batch": batch_num,
                "size": len(batch),
                "error": str(e)
            })

    return total_inserted, failed_batches

def main():
    print("\n" + "="*70)
    print("稳定币文档修复 — 重试失败的块插入")
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

    print(f"✓ 读取初稿: {DOC_INFO['draft_file']}")

    # 转换 blocks
    blocks, first_level_ids = convert_markdown(token, markdown)
    print(f"✓ 转换 blocks: {len(blocks)} 个")

    # 清理不支持的 block 类型
    UNSUPPORTED = {31, 32}  # Table, TableCell
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

    # 重试从批次2开始
    total_inserted, failed_batches = insert_blocks_with_retry(
        token, DOC_INFO["doc_id"], sorted_blocks, start_batch=2, batch_size=25
    )

    print(f"\n" + "="*70)
    print(f"结果: {total_inserted} 个额外块已插入")

    if failed_batches:
        print(f"\n⚠️  {len(failed_batches)} 个批次失败:")
        for fb in failed_batches:
            print(f"  - 批次 {fb['batch']}: {fb['error'][:80]}")
    else:
        print(f"\n✓ 所有块插入成功！")

    print("="*70 + "\n")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n✗ 错误: {str(e)}\n")
        sys.exit(1)
