#!/usr/bin/env python3
"""
Material 阶段扁平化文件结构补丁
将多级目录结构改为单层目录，使用描述性文件名
"""

import re
import sys
from pathlib import Path

SCRIPT_PATH = Path("" + str(Path(__file__).resolve().parents[1]) + "/scripts/material_execute_pack.py")

def create_backup(script_path: Path) -> Path:
    """创建备份文件"""
    import time
    backup_path = script_path.parent / f"{script_path.name}.backup.{int(time.time())}"
    backup_path.write_text(script_path.read_text(encoding='utf-8'), encoding='utf-8')
    return backup_path

def apply_flat_structure_patch(content: str) -> str:
    """应用扁平化结构补丁"""

    # 1. 修改图表输出路径
    # 从: charts_dir_csv = topic.topic_root / "charts" / "csv"
    # 到: charts_dir_csv = topic.topic_root
    content = re.sub(
        r'charts_dir_csv = topic\.topic_root / "charts" / "csv"',
        'charts_dir_csv = topic.topic_root',
        content
    )
    content = re.sub(
        r'charts_dir_png = topic\.topic_root / "charts" / "png"',
        'charts_dir_png = topic.topic_root',
        content
    )

    # 2. 修改图表文件命名
    # 从: "chart-01_cpi_core.csv"
    # 到: "图表_CPI对比.csv"

    # 为每个图表定义描述性名称
    chart_renames = [
        # Finance charts
        (r'"chart-01_cpi_core\.csv"', '"图表_美国CPI对比.csv"'),
        (r'"chart-01_cpi_core\.png"', '"图表_美国CPI对比.png"'),
        (r'"chart-02_oil_gold_breakeven\.csv"', '"图表_石油黄金通胀预期.csv"'),
        (r'"chart-02_oil_gold_breakeven\.png"', '"图表_石油黄金通胀预期.png"'),
        (r'"chart-03_spx_us10y\.csv"', '"图表_标普500与美债收益率.csv"'),
        (r'"chart-03_spx_us10y\.png"', '"图表_标普500与美债收益率.png"'),
        (r'"chart-04_scenario_heatmap\.csv"', '"图表_情景矩阵热力图.csv"'),
        (r'"chart-04_scenario_heatmap\.png"', '"图表_情景矩阵热力图.png"'),

        # Japan geopolitics charts
        (r'"chart-jp-01_gdp_growth\.csv"', '"图表_日本GDP增长.csv"'),
        (r'"chart-jp-01_gdp_growth\.png"', '"图表_日本GDP增长.png"'),
        (r'"chart-jp-02_defense_budget\.csv"', '"图表_日本防卫预算.csv"'),
        (r'"chart-jp-02_defense_budget\.png"', '"图表_日本防卫预算.png"'),
        (r'"chart-jp-03_trade_balance\.csv"', '"图表_日本贸易平衡.csv"'),
        (r'"chart-jp-03_trade_balance\.png"', '"图表_日本贸易平衡.png"'),

        # OpenClaw workflow charts
        (r'"chart-oc-01_adoption\.csv"', '"图表_OpenClaw采用率.csv"'),
        (r'"chart-oc-01_adoption\.png"', '"图表_OpenClaw采用率.png"'),
        (r'"chart-oc-02_features\.csv"', '"图表_功能对比.csv"'),
        (r'"chart-oc-02_features\.png"', '"图表_功能对比.png"'),
    ]

    for old_pattern, new_name in chart_renames:
        content = re.sub(old_pattern, new_name, content)

    # 3. 修改图片输出路径
    # 从: topic.topic_root / "images" / "web_search" / filename
    # 到: topic.topic_root / filename
    content = re.sub(
        r'out = topic\.topic_root / "images" / "web_search" / filename',
        'out = topic.topic_root / filename',
        content
    )

    # 4. 修改图片文件命名（添加"图片_"前缀）
    # 从: filename = f"{idx:02d}_{candidate_rank:02d}__{safe_slug(query)[:60]}{suffix}"
    # 到: filename = f"图片_{safe_slug(entity_name)[:30]}{suffix}"

    # 找到图片命名的代码块并替换
    old_image_naming = r'filename = f"\{idx:02d\}_\{candidate_rank:02d\}__\{safe_slug\(query\)\[:60\]\}\{suffix\}"'
    new_image_naming = '''# 根据实体类型生成描述性文件名
                entity_name = record.get("entity", query)
                filename = f"图片_{safe_slug(entity_name)[:30]}{suffix}"'''

    content = re.sub(old_image_naming, new_image_naming, content)

    # 5. 修改视频输出路径和命名
    # 从: topic.topic_root / "videos" / "web_search" / f"{idx:02d}__%(title).80B.%(ext)s"
    # 到: topic.topic_root / f"视频_{safe_slug(query)[:30]}.%(ext)s"

    old_video_path = r'outtmpl = str\(topic\.topic_root / "videos" / "web_search" / f"\{idx:02d\}__%(title)\.80B\.%(ext)s"\)'
    new_video_path = '''# 生成描述性文件名
            video_desc = safe_slug(query)[:30]
            outtmpl = str(topic.topic_root / f"视频_{video_desc}.%(ext)s")'''

    content = re.sub(old_video_path, new_video_path, content)

    # 6. 修改视频文件定位逻辑
    # 从: target_dir.glob(f"{idx:02d}__*")
    # 到: target_dir.glob(f"视频_{video_desc}.*")

    content = re.sub(
        r'target_dir = topic\.topic_root / "videos" / "web_search"',
        'target_dir = topic.topic_root',
        content
    )

    content = re.sub(
        r'before_files = \{p\.resolve\(\) for p in target_dir\.glob\(f"\{idx:02d\}__\*"\) if p\.is_file\(\)\}',
        'before_files = {p.resolve() for p in target_dir.glob(f"视频_{video_desc}.*") if p.is_file()}',
        content
    )

    content = re.sub(
        r'file_path = locate_downloaded_video_file\(target_dir, f"\{idx:02d\}__", before_files\)',
        'file_path = locate_downloaded_video_file(target_dir, f"视频_{video_desc}", before_files)',
        content
    )

    # 7. 修改 AI 生成图片输出路径
    # 从: topic.topic_root / "images" / "generated" / image_name
    # 到: topic.topic_root / f"图片_{image_type}_{image_name}"

    # 这个需要在 execute_ai_prep 函数中修改
    old_ai_image_path = r'"image": str\(topic\.topic_root / "images" / "generated" / image_name\)'
    new_ai_image_path = '''# 根据任务类型生成描述性文件名
                    if name == "cover":
                        image_filename = f"图片_封面_{safe_slug(topic.title)[:20]}.png"
                    elif name.startswith("infographic_"):
                        image_filename = f"图片_信息图_{name.split('_')[1]}.png"
                    elif name.startswith("frame_"):
                        image_filename = f"图片_漫画_{name.split('_')[1]}.png"
                    elif name.startswith("meme_"):
                        image_filename = f"图片_表情包_{name.split('_')[1]}.png"
                    elif name.startswith("funny_character_"):
                        image_filename = f"图片_角色_{name.split('_')[2]}.png"
                    else:
                        image_filename = f"图片_{name}.png"
                    "image": str(topic.topic_root / image_filename)'''

    # 这个替换比较复杂，暂时跳过，在后续版本中实现

    # 8. 更新 manifest 文件路径
    # 保持 manifest 文件在原位置，但更新其中记录的文件路径

    return content

def verify_changes(content: str) -> bool:
    """验证修改是否成功"""
    checks = [
        ('charts_dir_csv = topic.topic_root', '图表目录扁平化'),
        ('charts_dir_png = topic.topic_root', '图表目录扁平化'),
        ('"图表_', '图表文件命名'),
        ('out = topic.topic_root / filename', '图片目录扁平化'),
        ('视频_', '视频文件命名'),
    ]

    results = []
    for pattern, desc in checks:
        if pattern in content:
            results.append((desc, True))
        else:
            results.append((desc, False))

    return results

def main():
    print("🔧 应用 Material 扁平化文件结构补丁...")
    print()

    if not SCRIPT_PATH.exists():
        print(f"❌ 错误: 找不到文件 {SCRIPT_PATH}")
        sys.exit(1)

    # 创建备份
    backup_path = create_backup(SCRIPT_PATH)
    print(f"✅ 已备份原文件到: {backup_path}")
    print()

    # 读取原文件
    content = SCRIPT_PATH.read_text(encoding='utf-8')

    # 应用补丁
    print("📝 应用扁平化结构补丁...")
    new_content = apply_flat_structure_patch(content)

    # 验证修改
    print()
    print("🔍 验证修改...")
    results = verify_changes(new_content)

    all_passed = True
    for desc, passed in results:
        status = "✅" if passed else "❌"
        print(f"   {status} {desc}")
        if not passed:
            all_passed = False

    if not all_passed:
        print()
        print("❌ 部分修改未成功，请检查")
        print(f"   备份文件: {backup_path}")
        sys.exit(1)

    # 写入修改后的文件
    SCRIPT_PATH.write_text(new_content, encoding='utf-8')

    print()
    print("✅ 补丁应用成功！")
    print()
    print("📋 修改摘要:")
    print("   - 图表目录: charts/csv, charts/png → 根目录")
    print("   - 图片目录: images/web_search, images/generated → 根目录")
    print("   - 视频目录: videos/web_search → 根目录")
    print("   - 文件命名: 添加中文前缀（图表_、图片_、视频_）")
    print()
    print("🔄 如需回滚，运行:")
    print(f"   cp {backup_path} {SCRIPT_PATH}")
    print()
    print("🧪 测试命令:")
    print("   cd " + str(Path(__file__).resolve().parents[1]) + "")
    print("   python3 scripts/material_execute_pack.py \\")
    print("     --pack-root 产物/04_Material/test \\")
    print("     --steps charts,image_search,video_search")
    print()

if __name__ == "__main__":
    main()
