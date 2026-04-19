#!/usr/bin/env bash
set -euo pipefail

SRC_DIR="$(cd "$(dirname "$0")" && pwd)/skills"
TARGET_DIR="${1:-$HOME/.openclaw/skills}"

mkdir -p "${TARGET_DIR}"
cp -R "${SRC_DIR}/." "${TARGET_DIR}/"

echo "Installed skills to: ${TARGET_DIR}"
echo "Verify entry skill: dasheng-sop-orchestrator"

