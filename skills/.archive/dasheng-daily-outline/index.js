#!/usr/bin/env node

const message = [
  '[dasheng-daily-outline] 旧 outline 入口已停用。',
  '当前正式主链已改为 SelectedTopic -> ReasoningSheet -> 标准初稿，不再存在独立 outline 阶段。',
  '请改用 dasheng-media-sop 或 canonical `build_stage3_draft.py`。',
].join(' ');

function failLegacyEntry() {
  throw new Error(message);
}

if (require.main === module) {
  console.error(message);
  process.exit(1);
}

module.exports = {
  generateOutline: failLegacyEntry,
  buildOutlinePlan: failLegacyEntry,
};
