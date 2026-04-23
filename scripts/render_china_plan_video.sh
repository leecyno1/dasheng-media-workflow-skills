#!/bin/bash

# 中国十五五规划视频渲染脚本
# 用途：将 Remotion 组件渲染为高质量视频

set -e

echo "🎬 开始渲染中国十五五规划视频..."
echo ""

# 配置
COMPOSITION_ID="ChinaPlanXhs"
OUTPUT_DIR="/Volumes/PSSD/Projects/公众号文章/产物/07_Publish/2026-04-05_075240_ai/videos/motion_narrative"
OUTPUT_FILE="${OUTPUT_DIR}/china-plan-xhs-claude-purple.mp4"

# 创建输出目录
mkdir -p "${OUTPUT_DIR}"

# 进入 Remotion 项目目录
cd /Users/lichengyin/clawd/remotion-video-starter

echo "📹 渲染配置："
echo "  - 组合：${COMPOSITION_ID}"
echo "  - 输出：${OUTPUT_FILE}"
echo "  - 分辨率：1080x1920（竖版）"
echo "  - 帧率：30fps"
echo "  - 质量：100（最高）"
echo ""

# 渲染视频
npx remotion render src/index.jsx ${COMPOSITION_ID} "${OUTPUT_FILE}" \
  --quality=100 \
  --concurrency=4

echo ""
echo "✅ 渲染完成！"
echo ""
echo "📁 视频位置："
echo "  ${OUTPUT_FILE}"
echo ""
echo "📊 视频信息："
ls -lh "${OUTPUT_FILE}"
echo ""
echo "🎥 可以使用以下命令预览："
echo "  open \"${OUTPUT_FILE}\""
