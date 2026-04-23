#!/usr/bin/env bash
set -euo pipefail

ROOT="/Volumes/PSSD/Projects/公众号文章"
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
      python3 /Volumes/PSSD/Projects/公众号文章/scripts/run_mainline_stage.py material --run-id <run_id>
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
