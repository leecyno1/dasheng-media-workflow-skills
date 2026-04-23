#!/bin/bash
# Material 阶段视频素材优化补丁

set -e

# 自动检测项目根目录
_CURRENT_SCRIPT="${BASH_SOURCE[0]}"
if [ -L "$_CURRENT_SCRIPT" ]; then
  _CURRENT_SCRIPT=$(readlink -f "$_CURRENT_SCRIPT")
fi
_ROOT=$(cd "$(dirname "$_CURRENT_SCRIPT")/.." && pwd)

# 支持环境变量覆盖
ROOT="${DASHENG_ROOT:-$_ROOT}"
export DASHENG_ROOT="$ROOT"

SCRIPT_PATH="${ROOT}/scripts/material_execute_pack.py"

echo "🔧 应用 Material 视频素材优化补丁..."
echo ""

# 检查文件是否存在
if [ ! -f "$SCRIPT_PATH" ]; then
    echo "❌ 错误: 找不到文件 $SCRIPT_PATH"
    exit 1
fi

# 备份原文件
BACKUP_PATH="${SCRIPT_PATH}.backup.$(date +%Y%m%d_%H%M%S)"
cp "$SCRIPT_PATH" "$BACKUP_PATH"
echo "✅ 已备份原文件到: $BACKUP_PATH"
echo ""

# 修改 1: 将视频下载默认值从 0 改为 3
echo "📝 修改 1: 启用视频自动下载（默认值 0 → 3）"
sed -i '' 's/--video-download-limit", type=int, default=0/--video-download-limit", type=int, default=3/' "$SCRIPT_PATH"

if grep -q 'default=3' "$SCRIPT_PATH"; then
    echo "   ✅ 成功: 视频下载默认值已改为 3"
else
    echo "   ❌ 失败: 未能修改默认值"
    echo "   恢复备份..."
    cp "$BACKUP_PATH" "$SCRIPT_PATH"
    exit 1
fi

echo ""
echo "✅ 补丁应用成功！"
echo ""
echo "📋 修改摘要:"
echo "   - 视频下载默认值: 0 → 3"
echo "   - 每个查询自动下载前 3 个合格视频"
echo ""
echo "🔄 如需回滚，运行:"
echo "   cp $BACKUP_PATH $SCRIPT_PATH"
echo ""
echo "🧪 测试命令:"
echo "   cd ${ROOT}"
echo "   python3 scripts/material_execute_pack.py --draft-manifest <manifest.json>"
echo ""
