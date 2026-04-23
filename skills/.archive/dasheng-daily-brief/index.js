#!/usr/bin/env node

const message = [
  '[dasheng-daily-brief] 旧入口已停用。',
  '请改用唯一主链 skill：dasheng-media-sop。',
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
  generateBrief: failLegacyEntry,
};
