#!/usr/bin/env node

const message = [
  '[dasheng-daily-final] 旧 final 入口已停用。',
  '当前正式主链不存在 final 阶段，请改用 dasheng-media-sop。',
  '终稿结构由 Final Structure Gate 锁定，后续走 material / rewrite / publish。',
].join(' ');

function failLegacyEntry() {
  throw new Error(message);
}

if (require.main === module) {
  console.error(message);
  process.exit(1);
}

module.exports = {
  generateFinal: failLegacyEntry,
};
