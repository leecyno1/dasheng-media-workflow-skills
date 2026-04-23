#!/usr/bin/env node

const message = [
  '[dasheng-daily-draft] 旧入口已停用。',
  '请改用唯一主链 skill：dasheng-media-sop。',
  '标准初稿请走 canonical `build_stage3_draft.py`。',
].join(' ');

function failLegacyEntry() {
  throw new Error(message);
}

if (require.main === module) {
  console.error(message);
  process.exit(1);
}

module.exports = {
  generateDraft: failLegacyEntry,
};
