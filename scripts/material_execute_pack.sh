#!/usr/bin/env bash
set -euo pipefail

# 自动检测项目根目录
_CURRENT_SCRIPT="${BASH_SOURCE[0]}"
if [ -L "$_CURRENT_SCRIPT" ]; then
  _CURRENT_SCRIPT=$(readlink -f "$_CURRENT_SCRIPT")
fi
_ROOT=$(cd "$(dirname "$_CURRENT_SCRIPT")/.." && pwd)

# 支持环境变量覆盖
ROOT="${DASHENG_ROOT:-$_ROOT}"
export DASHENG_ROOT="$ROOT"

PYTHON_SCRIPT="$ROOT/scripts/material_execute_pack.py"

print_wrapper_help() {
  cat <<'HELP'
material_execute_pack.sh 包装入口

示例：
  scripts/material_execute_pack.sh --draft-manifest <draft_manifest.json>

说明：
  - 本包装入口已完全收口到 canonical `draft_manifest.json`。
  - `--pack-root`、`--latest-pack`、`--single` 等旧参数已停用。
  - 如需更复杂的主链执行，请改用：
      python3 $DASHENG_ROOT/scripts/run_mainline_stage.py material --run-id <run_id>
HELP
}

args=()
while [[ $# -gt 0 ]]; do
  if [[ "$1" == "-h" || "$1" == "--help" ]]; then
    print_wrapper_help
    echo
    echo "----- Python 主脚本帮助 -----"
    if [ -x "$ROOT/.venv_media/bin/python" ]; then
      exec "$ROOT/.venv_media/bin/python" "$PYTHON_SCRIPT" --help
    fi
    exec python3 "$PYTHON_SCRIPT" --help
  elif [[ "$1" == "--single" || "$1" == "--single-topic" || "$1" == "--latest-pack" || "$1" == "--pack-root" || "$1" == "--layer5" || "$1" == "--all-layer5" || "$1" == "--no-layer5" ]]; then
    echo "error: 旧参数 $1 已停用；请改用 --draft-manifest <draft_manifest.json> 走 canonical material 主链。" >&2
    shift
  else
    args+=("$1")
    shift
  fi
done

if [ -x "$ROOT/.venv_media/bin/python" ]; then
  exec "$ROOT/.venv_media/bin/python" "$PYTHON_SCRIPT" "${args[@]}"
fi

exec python3 "$PYTHON_SCRIPT" "${args[@]}"
