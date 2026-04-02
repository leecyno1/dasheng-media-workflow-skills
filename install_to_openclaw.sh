#!/usr/bin/env bash
set -euo pipefail

BASE_DIR="$(cd "$(dirname "$0")" && pwd)"
SRC_DIR="${BASE_DIR}/skills"
TARGET_DIR="${1:-$HOME/.openclaw/skills}"

mkdir -p "${TARGET_DIR}"
cp -R "${SRC_DIR}/." "${TARGET_DIR}/"

echo "Installed skills to: ${TARGET_DIR}"
echo "Verify entry skill: dasheng-sop-orchestrator"
echo "Next: copy env template -> ~/.openclaw/dasheng.env"
echo "Template file: ${BASE_DIR}/ENV_TEMPLATE.env"
echo "Smoke prompts: ${BASE_DIR}/SMOKE_PROMPTS.md"
