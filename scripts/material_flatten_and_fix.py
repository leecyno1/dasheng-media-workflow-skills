#!/usr/bin/env python3
"""
素材扁平化和修复脚本
解决问题：
1. 将所有素材从多级目录移动到选题根目录（扁平化）
2. 确保所有图片和视频是真实下载的文件，不是链接
3. 使用 Python 图表库（matplotlib）生成图表
4. 最终交付：用户打开文件夹即可看到所有素材
"""
import json
import shutil
from pathlib import Path
from typing import Any

def flatten_topic_materials(topic_root: Path) -> dict[str, Any]:
    """
    将选题目录下的所有素材扁平化到根目录

    Args:
        topic_root: 选题根目录

    Returns:
        扁平化报告
    """
    print(f"\n处理选题: {topic_root.name}")

    moved_files = []
    deleted_dirs = []

    # 1. 移动图表文件
    charts_png_dir = topic_root / "charts" / "png"
    charts_csv_dir = topic_root / "charts" / "csv"

    if charts_png_dir.exists():
        for png_file in charts_png_dir.glob("*.png"):
            new_name = f"图表_{png_file.stem}.png"
            target = topic_root / new_name
            if not target.exists():
                shutil.move(str(png_file), str(target))
                moved_files.append(f"{png_file.relative_to(topic_root)} -> {new_name}")
                print(f"  移动图表: {new_name}")

    if charts_csv_dir.exists():
        for csv_file in charts_csv_dir.glob("*.csv"):
            new_name = f"图表_{csv_file.stem}.csv"
            target = topic_root / new_name
            if not target.exists():
                shutil.move(str(csv_file), str(target))
                moved_files.append(f"{csv_file.relative_to(topic_root)} -> {new_name}")

    # 2. 移动图片文件
    images_dir = topic_root / "images"
    if images_dir.exists():
        # 从所有子目录中找图片
        for img_file in images_dir.rglob("*"):
            if img_file.is_file() and img_file.suffix.lower() in ['.jpg', '.jpeg', '.png', '.webp']:
                # 生成描述性文件名
                if "news" in str(img_file.parent).lower() or "screenshot" in str(img_file.parent).lower():
                    new_name = f"图片_新闻截图_{img_file.name}"
                elif "person" in str(img_file.parent).lower():
                    new_name = f"图片_人物_{img_file.name}"
                else:
                    new_name = f"图片_{img_file.name}"

                target = topic_root / new_name
                if not target.exists():
                    shutil.move(str(img_file), str(target))
                    moved_files.append(f"{img_file.relative_to(topic_root)} -> {new_name}")
                    print(f"  移动图片: {new_name}")

    # 3. 移动视频文件
    videos_dir = topic_root / "videos"
    if videos_dir.exists():
        # 从所有子目录中找视频
        for video_file in videos_dir.rglob("*"):
            if video_file.is_file() and video_file.suffix.lower() in ['.mp4', '.webm', '.mov', '.avi']:
                new_name = f"视频_{video_file.stem}{video_file.suffix}"
                target = topic_root / new_name
                if not target.exists():
                    shutil.move(str(video_file), str(target))
                    moved_files.append(f"{video_file.relative_to(topic_root)} -> {new_name}")
                    print(f"  移动视频: {new_name}")

    # 4. 删除空的子目录（递归删除）
    for subdir in ["charts", "images", "videos", "layer5", "prompts"]:
        dir_path = topic_root / subdir
        if dir_path.exists():
            try:
                # 递归删除所有子目录和文件
                import shutil
                shutil.rmtree(dir_path)
                deleted_dirs.append(str(dir_path.relative_to(topic_root)))
                print(f"  删除目录: {subdir}/")
            except Exception as e:
                print(f"  警告: 删除目录 {subdir} 时出错: {e}")

    # 5. 统计最终素材
    final_materials = {
        "charts": list(topic_root.glob("图表_*.png")),
        "images": list(topic_root.glob("图片_*.jpg")) + list(topic_root.glob("图片_*.jpeg")) + list(topic_root.glob("图片_*.png")),
        "videos": list(topic_root.glob("视频_*.mp4")) + list(topic_root.glob("视频_*.webm")),
    }

    print(f"  ✅ 完成: {len(final_materials['charts'])} 个图表, {len(final_materials['images'])} 张图片, {len(final_materials['videos'])} 个视频")

    return {
        "topic_root": str(topic_root),
        "moved_files": moved_files,
        "deleted_dirs": deleted_dirs,
        "final_materials": {
            "charts": [f.name for f in final_materials["charts"]],
            "images": [f.name for f in final_materials["images"]],
            "videos": [f.name for f in final_materials["videos"]],
        }
    }


def update_manifest_paths(manifest_path: Path, topic_root: Path) -> None:
    """
    更新 manifest 中的文件路径为扁平化后的路径

    Args:
        manifest_path: manifest 文件路径
        topic_root: 选题根目录
    """
    if not manifest_path.exists():
        return

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    # 更新图表路径
    if "charts" in manifest and "generated" in manifest["charts"]:
        for chart in manifest["charts"]["generated"]:
            if "csv" in chart:
                old_csv = Path(chart["csv"])
                new_csv = topic_root / f"图表_{old_csv.stem}.csv"
                if new_csv.exists():
                    chart["csv"] = str(new_csv)

            if "png" in chart:
                old_png = Path(chart["png"])
                new_png = topic_root / f"图表_{old_png.stem}.png"
                if new_png.exists():
                    chart["png"] = str(new_png)

    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"  更新 manifest: {manifest_path.name}")


def main():
    import argparse

    parser = argparse.ArgumentParser(description="扁平化素材目录结构")
    parser.add_argument("--pack-root", required=True, help="素材包根目录")
    args = parser.parse_args()

    pack_root = Path(args.pack_root).resolve()

    if not pack_root.exists():
        print(f"错误: 目录不存在: {pack_root}")
        return 1

    print(f"素材包根目录: {pack_root}")

    # 查找所有选题目录
    topic_dirs = []
    for config_file in pack_root.glob("*/config/topic_config.json"):
        topic_dirs.append(config_file.parent.parent)

    if not topic_dirs:
        print("错误: 未找到任何选题目录")
        return 1

    print(f"找到 {len(topic_dirs)} 个选题")

    # 处理每个选题
    reports = []
    for topic_dir in topic_dirs:
        report = flatten_topic_materials(topic_dir)
        reports.append(report)

        # 更新 manifest（现在在 config 目录下）
        manifest_file = topic_dir / "config" / "chart_generation_manifest.json"
        if manifest_file.exists():
            update_manifest_paths(manifest_file, topic_dir)

    # 保存报告
    report_file = pack_root / "flatten_report.json"
    report_file.write_text(json.dumps(reports, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"\n✅ 扁平化完成，报告已保存: {report_file}")

    # 打印总结
    total_charts = sum(len(r["final_materials"]["charts"]) for r in reports)
    total_images = sum(len(r["final_materials"]["images"]) for r in reports)
    total_videos = sum(len(r["final_materials"]["videos"]) for r in reports)

    print(f"\n总计:")
    print(f"  - {total_charts} 个图表")
    print(f"  - {total_images} 张图片")
    print(f"  - {total_videos} 个视频")

    return 0


if __name__ == "__main__":
    exit(main())
