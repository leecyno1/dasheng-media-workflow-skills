#!/usr/bin/env node

const message = [
  '[dasheng-daily-clustering] 旧 clustering 入口已停用。',
  '当前 Stage 2 已并入 AI-only brief 主链，请改用 dasheng-media-sop。',
  '正式链路：intake -> brief -> draft -> material -> rewrite -> publish -> postmortem。',
].join(' ');

function failLegacyEntry() {
  throw new Error(message);
}

if (require.main === module) {
  console.error(message);
  process.exit(1);
}

module.exports = {
  clustering: failLegacyEntry,
};
