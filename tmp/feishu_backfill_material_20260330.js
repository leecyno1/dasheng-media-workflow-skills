#!/usr/bin/env node

const fs = require('fs');
const path = require('path');
const {
  createClient,
  listBlocks,
  extractBlockText,
  getSiblingContext,
  writeDocSection,
  refillDocAnchorsWithLocalAssets,
  uploadDriveFile,
  createFolder,
  sendTextMessage
} = require('/Volumes/PSSD/Projects/公众号文章/skills/dasheng-daily-shared/runtime/feishu-client.js');

const ROOT_FOLDER_TOKEN = 'L9d1f3xcNl0rKxdvvN9cLy2InHb';
const OUTPUT_ROOT = '/Users/lichengyin/Desktop/自媒体创作临时交付/2026-03-30/05_material';
const REPORT_JSON = path.join(OUTPUT_ROOT, '05_Feishu回填结果.json');
const REPORT_MD = path.join(OUTPUT_ROOT, '05_Feishu回填结果.md');

const DOCS = [
  {
    name: '半导体误判',
    token: 'JuDzdvqypoDDrixsn6rc2vJ3nGT',
    url: 'https://ccnokd2fmz4u.feishu.cn/docx/JuDzdvqypoDDrixsn6rc2vJ3nGT',
    dir: '/Users/lichengyin/Desktop/自媒体创作临时交付/2026-03-30/05_material/01_半导体误判',
    anchors: [
      ['图表', '01', '全球规模增长图', '文末素材区', '图表', '半导体误判_图表01_global_market_size.png'],
      ['图表', '02', '平台结构分化图', '文末素材区', '图表', '半导体误判_图表02_platform_mix.png'],
      ['图表', '03', '晶圆厂资本开支图', '文末素材区', '图表', '半导体误判_图表03_fab_capex.png'],
      ['图表', '04', '细分环节景气指数图', '文末素材区', '图表', '半导体误判_图表04_segment_growth_index.png'],
      ['图片', '01', 'SIA官方截图', '文末素材区', '图片', '半导体误判_官方截图01_SIA.png'],
      ['图片', '02', 'WSTS官方截图', '文末素材区', '图片', '半导体误判_官方截图02_WSTS.png'],
      ['图片', '03', 'TSMC官方截图', '文末素材区', '图片', '半导体误判_官方截图03_TSMC.png'],
      ['图片', '04', '信息图01', '文末素材区', '图片', '半导体误判_图片04_信息图01.png'],
      ['图片', '05', '信息图02', '文末素材区', '图片', '半导体误判_图片05_信息图02.png'],
      ['表格', '01', '全球规模增长数据表', '文末素材区', '表格', '半导体误判_数据01_global_market_size.csv'],
      ['表格', '02', '平台结构数据表', '文末素材区', '表格', '半导体误判_数据02_platform_mix.csv']
    ],
    videos: [
      '半导体误判_视频01_SIA证据卡.mp4',
      '半导体误判_视频02_总量增长图表卡.mp4',
      '半导体误判_视频03_结构分化图表卡.mp4'
    ]
  },
  {
    name: 'OpenClaw一键安装',
    token: 'NfNSdRRhFoqpK3xFZpEc35lKnGh',
    url: 'https://ccnokd2fmz4u.feishu.cn/docx/NfNSdRRhFoqpK3xFZpEc35lKnGh',
    dir: '/Users/lichengyin/Desktop/自媒体创作临时交付/2026-03-30/05_material/02_OpenClaw一键安装',
    anchors: [
      ['图表', '01', '安装流程图', '文末素材区', '图表', 'OpenClaw一键安装_图表01_安装流程图.png'],
      ['图表', '02', '安全边界矩阵', '文末素材区', '图表', 'OpenClaw一键安装_图表02_安全边界矩阵.png'],
      ['图表', '03', '团队治理闭环', '文末素材区', '图表', 'OpenClaw一键安装_图表03_团队治理闭环.png'],
      ['图表', '04', '故障排查树', '文末素材区', '图表', 'OpenClaw一键安装_图表04_故障排查树.png'],
      ['图片', '01', 'GitHub主页截图', '文末素材区', '图片', 'OpenClaw一键安装_官方截图01_GitHub主页.png'],
      ['图片', '02', 'Feishu设置截图', '文末素材区', '图片', 'OpenClaw一键安装_官方截图02_Feishu设置.png'],
      ['图片', '03', '控制档位截图', '文末素材区', '图片', 'OpenClaw一键安装_官方截图03_控制档位.png'],
      ['图片', '04', '信息图01', '文末素材区', '图片', 'OpenClaw一键安装_图片04_信息图01.png'],
      ['图片', '05', '信息图02', '文末素材区', '图片', 'OpenClaw一键安装_图片05_信息图02.png'],
      ['表格', '01', '安装流程节点表', '文末素材区', '表格', 'OpenClaw一键安装_数据01_安装流程节点数据.csv'],
      ['表格', '02', '安全边界数据表', '文末素材区', '表格', 'OpenClaw一键安装_数据02_安全边界数据.csv']
    ],
    videos: [
      'OpenClaw一键安装_视频01_GitHub主页卡.mp4',
      'OpenClaw一键安装_视频02_安装流程卡.mp4',
      'OpenClaw一键安装_视频03_安全边界卡.mp4'
    ]
  },
  {
    name: '供给秩序重估',
    token: 'IxsNdUZqkoGe45xfjyhcpLT4nxb',
    url: 'https://ccnokd2fmz4u.feishu.cn/docx/IxsNdUZqkoGe45xfjyhcpLT4nxb',
    dir: '/Users/lichengyin/Desktop/自媒体创作临时交付/2026-03-30/05_material/03_供给秩序重估',
    anchors: [
      ['图表', '01', '核心CPI趋势图', '文末素材区', '图表', '供给秩序重估_图表01_cpi_core.png'],
      ['图表', '02', '油金与盈亏平衡通胀图', '文末素材区', '图表', '供给秩序重估_图表02_oil_gold_breakeven.png'],
      ['图表', '03', '美股与美债收益率图', '文末素材区', '图表', '供给秩序重估_图表03_spx_us10y.png'],
      ['图表', '04', '情景热力图', '文末素材区', '图表', '供给秩序重估_图表04_scenario_heatmap.png'],
      ['图片', '01', 'EIA官方截图', '文末素材区', '图片', '供给秩序重估_官方截图01_EIA.png'],
      ['图片', '02', 'STEO官方截图', '文末素材区', '图片', '供给秩序重估_官方截图02_STEO.png'],
      ['图片', '03', 'Fed官方截图', '文末素材区', '图片', '供给秩序重估_官方截图03_Fed.png'],
      ['图片', '04', '油轮航运图', '文末素材区', '图片', '供给秩序重估_图片01_01_oil_tanker_aerial.jpg'],
      ['图片', '05', '黄金储备图', '文末素材区', '图片', '供给秩序重估_图片02_02_gold_bullion_vaul.jpg'],
      ['表格', '01', '核心CPI数据表', '文末素材区', '表格', '供给秩序重估_数据01_cpi_core.csv'],
      ['表格', '02', '油金联动数据表', '文末素材区', '表格', '供给秩序重估_数据02_oil_gold_breakeven.csv']
    ],
    videos: [
      '供给秩序重估_视频01_01_4KFreeStockFoot.mp4',
      '供给秩序重估_视频02_02_Oiltanker-Drone.mp4',
      '供给秩序重估_视频03_EIA证据卡.mp4',
      '供给秩序重估_视频04_油金联动图表卡.mp4',
      '供给秩序重估_视频05_情景热力图卡.mp4'
    ]
  }
];

function getBlockText(block) {
  return String(extractBlockText(block) || '').trim();
}

function ensureFile(filePath) {
  if (!fs.existsSync(filePath)) {
    throw new Error('missing file: ' + filePath);
  }
}

function buildAnchorMarkdown(doc) {
  return doc.anchors.map(([kind, index, label, position, format, fileName]) => {
    const filePath = path.join(doc.dir, fileName);
    ensureFile(filePath);
    return '[素材锚点-' + kind + '-' + index + '：' + label + '｜' + position + '｜' + format + '｜`' + filePath + '`]';
  }).join('\n');
}

async function findOrCreateHeading(client, docToken, headingText) {
  const blocks = await listBlocks(client, docToken);
  let block = blocks.find(item => getBlockText(item) === headingText);
  if (block) return block;
  await writeDocSection(client, docToken, headingText, { mode: 'plain_text_document' });
  const refreshed = await listBlocks(client, docToken);
  block = refreshed.find(item => getBlockText(item) === headingText);
  if (!block) {
    throw new Error('heading not found: ' + headingText);
  }
  return block;
}

async function insertPlainAfterHeading(client, docToken, headingText, content) {
  const heading = await findOrCreateHeading(client, docToken, headingText);
  const sibling = await getSiblingContext(client, docToken, heading.block_id);
  return writeDocSection(client, docToken, content, {
    mode: 'plain_text_document',
    parentBlockId: sibling.parentBlockId,
    index: sibling.index + 1
  });
}

async function maybeInsertAnchors(client, doc) {
  const blocks = await listBlocks(client, doc.token);
  const hasMarkers = blocks.some(block => getBlockText(block).includes('素材锚点-'));
  const hasCaptions = blocks.some(block => getBlockText(block).includes('【素材已回填】'));
  const tempFile = path.join(doc.dir, '00_feishu_backfill_anchors.md');
  if (!hasMarkers && !hasCaptions) {
    const anchorMarkdown = buildAnchorMarkdown(doc);
    fs.writeFileSync(tempFile, anchorMarkdown + '\n', 'utf8');
    await insertPlainAfterHeading(client, doc.token, '2026-03-30 素材回填区', anchorMarkdown);
    return { inserted: true, reason: null, tempFile };
  }
  if (!fs.existsSync(tempFile)) {
    fs.writeFileSync(tempFile, buildAnchorMarkdown(doc) + '\n', 'utf8');
  }
  return { inserted: false, reason: hasMarkers ? 'marker_exists' : 'caption_exists', tempFile };
}

async function ensureFeishuSubfolder(client, host, name) {
  return createFolder(client, '2026-03-30_' + name, ROOT_FOLDER_TOKEN, host);
}

async function uploadAssets(client, host, doc, folderToken) {
  const allowedExt = new Set(['.png', '.jpg', '.jpeg', '.mp4', '.csv']);
  const names = fs.readdirSync(doc.dir)
    .filter(name => allowedExt.has(path.extname(name).toLowerCase()))
    .sort();
  const uploaded = [];
  for (const name of names) {
    const filePath = path.join(doc.dir, name);
    const result = await uploadDriveFile(client, folderToken, filePath, host);
    uploaded.push({ name, url: result.url, file_token: result.file_token });
  }
  return uploaded;
}

async function appendVideoLinks(client, doc, uploaded, folderUrl) {
  const videoNames = new Set(doc.videos);
  const lines = ['素材文件夹：' + folderUrl];
  uploaded.forEach(file => {
    if (videoNames.has(file.name)) {
      lines.push(file.name + '｜' + file.url);
    }
  });
  return insertPlainAfterHeading(client, doc.token, '2026-03-30 视频素材链接', lines.join('\n'));
}

function buildMarkdownReport(results) {
  const lines = ['# 2026-03-30 Feishu 回填结果', ''];
  results.forEach(item => {
    lines.push('## ' + item.name);
    lines.push('- 文档：' + item.url);
    lines.push('- 素材目录：' + (item.folder_url || '未创建'));
    lines.push('- 锚点插入：' + (item.anchor_inserted ? '是' : '否（' + (item.anchor_reason || 'unknown') + '）'));
    lines.push('- 回填结果：' + String((item.refill && item.refill.anchors_filled) || 0) + '/' + String((item.refill && item.refill.anchors_total) || 0));
    lines.push('- 上传文件数：' + String(item.uploaded_count || 0));
    if (Array.isArray(item.video_urls) && item.video_urls.length) {
      lines.push('- 视频链接：');
      item.video_urls.forEach(url => lines.push('  - ' + url));
    }
    if (item.error) {
      lines.push('- 错误：' + item.error);
    }
    lines.push('');
  });
  return lines.join('\n');
}

async function main() {
  const { client, config } = createClient();
  const results = [];

  for (const doc of DOCS) {
    const result = { name: doc.name, url: doc.url };
    try {
      const anchorInfo = await maybeInsertAnchors(client, doc);
      result.anchor_inserted = anchorInfo.inserted;
      result.anchor_reason = anchorInfo.reason;
      result.refill = await refillDocAnchorsWithLocalAssets(client, doc.token, [anchorInfo.tempFile]);
      const folder = await ensureFeishuSubfolder(client, config.host, doc.name);
      result.folder_url = folder.url;
      const uploaded = await uploadAssets(client, config.host, doc, folder.token);
      result.uploaded_count = uploaded.length;
      result.video_urls = uploaded.filter(item => doc.videos.includes(item.name)).map(item => item.url);
      await appendVideoLinks(client, doc, uploaded, folder.url);
    } catch (error) {
      result.error = error && error.stack ? error.stack : String(error);
    }
    results.push(result);
  }

  fs.writeFileSync(REPORT_JSON, JSON.stringify(results, null, 2), 'utf8');
  fs.writeFileSync(REPORT_MD, buildMarkdownReport(results), 'utf8');

  const okCount = results.filter(item => !item.error).length;
  console.log(JSON.stringify({
    ok: okCount,
    total: results.length,
    report: REPORT_MD,
    results
  }, null, 2));

  try {
    const message = [
      'material 回填完成',
      '完成文档：' + okCount + '/' + results.length,
      '报告：' + REPORT_MD
    ].concat(results.map(item => item.name + '：' + item.url)).join('\n');
    await sendTextMessage(client, config.chatId, message);
  } catch (error) {
    console.error('sendTextMessage failed:', error.message || String(error));
  }
}

main().catch(error => {
  console.error(error && error.stack ? error.stack : String(error));
  process.exit(1);
});
