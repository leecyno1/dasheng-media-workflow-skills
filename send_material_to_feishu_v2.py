#!/usr/bin/env python3
"""
将 Material 阶段素材回填到飞书，并发送到群

流程：
1. 读取初稿 markdown
2. Markdown 转 blocks
3. 分批插入 blocks 到文档（API 限制：单次最多 50 个）
4. 发送文档链接到群
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

DOCS = [
    {
        "draft_file": "03_标准初稿_claude新模型引发华尔街紧急会议-ai对金融业的风险在哪.md",
        "title": "Claude新模型引发华尔街紧急会议：AI对金融业的风险在哪",
        "stage_emoji": "🤖"
    },
    {
        "draft_file": "03_标准初稿_稳定币牌照落地-加密市场的-银行牌照时刻.md",
        "title": "稳定币牌照落地：加密市场的\"银行牌照时刻\"",
        "stage_emoji": "💰"
    },
    {
        "draft_file": "03_标准初稿_日本士兵闯使馆事件背后-个体极端行为还是系统性问题.md",
        "title": "日本士兵闯使馆事件背后：个体极端行为还是系统性问题？",
        "stage_emoji": "⚠️"
    }
]

def get_token():
    """获取飞书 token"""
    url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
    resp = requests.post(url, json={"app_id": APP_ID, "app_secret": APP_SECRET}, timeout=10)
    result = resp.json()
    if result.get("code") != 0:
        raise Exception(f"获取 token 失败: {result}")
    return result["tenant_access_token"]

def create_document(token, title):
    """创建飞书文档"""
    url = "https://open.feishu.cn/open-apis/docx/v1/documents"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    data = {"folder_token": "", "title": title}

    resp = requests.post(url, headers=headers, json=data, timeout=10)
    result = resp.json()
    if result.get("code") != 0:
        raise Exception(f"创建文档失败: {result}")

    return result["data"]["document"]["document_id"]

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

def insert_blocks_batch(token, doc_id, blocks):
    """分批插入 blocks（API 限制：单次最多 50 个）"""
    url = f"https://open.feishu.cn/open-apis/docx/v1/documents/{doc_id}/blocks/{doc_id}/children"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    total_inserted = 0
    batch_size = 50

    for i in range(0, len(blocks), batch_size):
        batch = blocks[i:i+batch_size]
        data = {"children": batch}

        resp = requests.post(url, headers=headers, json=data, timeout=30)
        result = resp.json()
        if result.get("code") != 0:
            raise Exception(f"插入 blocks 失败 (批次 {i//batch_size + 1}): {result}")

        inserted = result["data"].get("children", [])
        total_inserted += len(inserted)
        print(f"  ✓ 批次 {i//batch_size + 1}: 插入 {len(inserted)}/{len(batch)} 个 blocks")

    return total_inserted

def send_to_chat(token, chat_id, doc_id, title, stage_emoji):
    """发送文档到飞书群"""
    url = "https://open.feishu.cn/open-apis/im/v1/messages"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    doc_url = f"https://bytedance.larkoffice.com/docx/{doc_id}"

    data = {
        "receive_id": chat_id,
        "msg_type": "text",
        "content": json.dumps({
            "text": f"{stage_emoji} {title}\n\n📎 飞书文档：{doc_url}\n\n✍️ Material 阶段素材已回填，请查看并评论"
        })
    }

    params = {"receive_id_type": "chat_id"}
    resp = requests.post(url, headers=headers, params=params, json=data, timeout=10)
    result = resp.json()
    if result.get("code") != 0:
        raise Exception(f"发送消息失败: {result}")

    return doc_url

def process_doc(token, doc_info):
    """处理单篇文档"""
    draft_file = doc_info["draft_file"]
    title = doc_info["title"]
    stage_emoji = doc_info["stage_emoji"]

    print(f"\n{'='*70}")
    print(f"{stage_emoji} 处理: {title}")
    print(f"{'='*70}")

    # 1. 读取初稿
    draft_path = Path(DRAFT_BASE) / draft_file
    if not draft_path.exists():
        print(f"✗ 初稿文件不存在: {draft_path}")
        return None

    with open(draft_path, 'r', encoding='utf-8') as f:
        markdown = f.read()

    print(f"✓ 读取初稿: {draft_file}")

    # 2. 创建文档
    doc_id = create_document(token, title)
    print(f"✓ 创建文档: {doc_id}")

    # 3. Markdown 转 blocks
    blocks, first_level_ids = convert_markdown(token, markdown)
    print(f"✓ 转换 blocks: {len(blocks)} 个")

    # 4. 清理不支持的 block 类型
    UNSUPPORTED = {31, 32}  # Table, TableCell
    cleaned_blocks = [b for b in blocks if b.get("block_type") not in UNSUPPORTED]

    if len(cleaned_blocks) < len(blocks):
        print(f"⚠️  过滤不支持的 block 类型 ({len(blocks) - len(cleaned_blocks)} 个)")

    # 5. 排序
    block_map = {b.get("block_id"): b for b in cleaned_blocks}
    sorted_blocks = [block_map[bid] for bid in first_level_ids if bid in block_map]
    remaining = [b for b in cleaned_blocks if b.get("block_id") not in set(first_level_ids)]
    sorted_blocks.extend(remaining)

    # 6. 分批插入 blocks
    total = insert_blocks_batch(token, doc_id, sorted_blocks)
    print(f"✓ 总计插入: {total} 个 blocks")

    # 7. 发送到群
    doc_url = send_to_chat(token, CHAT_ID, doc_id, title, stage_emoji)
    print(f"✓ 发送到群")

    return {
        "title": title,
        "url": doc_url,
        "doc_id": doc_id
    }

def main():
    print("\n" + "#"*70)
    print("# Material 阶段 — 素材回填完成，发送到飞书")
    print("#"*70)

    # 获取 token
    print("\n获取飞书 token...")
    token = get_token()
    print("✓ 认证成功")

    # 处理每篇文档
    results = []
    for doc_info in DOCS:
        try:
            result = process_doc(token, doc_info)
            if result:
                results.append(result)
        except Exception as e:
            print(f"✗ 处理失败: {str(e)}")

    # 总结
    print(f"\n" + "#"*70)
    print(f"# ✓ 完成 - {len(results)} 篇文档已发送")
    print("#"*70)

    print(f"\n📊 发送清单：")
    for i, r in enumerate(results, 1):
        print(f"  {i}. {r['title']}")
        print(f"     {r['url']}")

    print(f"\n💬 所有文档已发送到飞书群 ✓\n")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n✗ 错误: {str(e)}\n")
        sys.exit(1)
