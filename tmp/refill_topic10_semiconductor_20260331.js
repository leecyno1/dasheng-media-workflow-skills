#!/usr/bin/env node

const fs = require('fs');
const path = require('path');
const {
  createClient,
  listBlocks,
  extractBlockText,
  clearSectionAfterHeading,
  writeDocSection,
  getSiblingContext,
  refillDocAnchorsWithLocalAssets,
  buildDocUrl
} = require('/Volumes/PSSD/Projects/公众号文章/skills/dasheng-daily-shared/runtime/feishu-client.js');

const DOC_TOKEN = 'JuDzdvqypoDDrixsn6rc2vJ3nGT';
const MATERIAL_ROOT = '/Volumes/PSSD/Projects/公众号文章/产物/03_素材收集/2026-03-29_105535/pack_assets/topic-10';
const ANCHOR_FILE = '/Volumes/PSSD/Projects/公众号文章/tmp/topic10_refill_anchors_20260331.md';
const REPORT_FILE = '/Users/lichengyin/Desktop/自媒体创作临时交付/2026-03-31/05_material/refill_topic10_result.json';

const CLEAR_HEADINGS = [
  '素材回填区',
  '2026-03-30 素材回填区',
  '文末素材区',
  '视频素材链接',
  '2026-03-30 视频素材链接'
];

const INSERT_HEADING_PRIORITY = [
  '素材回填区',
  '2026-03-30 素材回填区',
  '文末素材区'
];

function ensureExists(filePath) {
  if (!fs.existsSync(filePath)) {
    throw new Error('missing file: ' + filePath);
  }
  return filePath;
}

function walkFiles(root) {
  if (!fs.existsSync(root)) return [];
  const result = [];
  const queue = [root];
  while (queue.length) {
    const current = queue.shift();
    for (const entry of fs.readdirSync(current, { withFileTypes: true })) {
      if (entry.name.startsWith('.')) continue;
      const fullPath = path.join(current, entry.name);
      if (entry.isDirectory()) queue.push(fullPath);
      if (entry.isFile()) result.push(fullPath);
    }
  }
  return result.sort();
}

function findHeadingBlock(blocks, heading) {
  const target = String(heading || '').trim();
  return blocks.find(block => {
    const text = String(extractBlockText(block) || '').trim();
    return text === target || text.includes(target);
  }) || null;
}

function pickAssets() {
  const chartPngDir = path.join(MATERIAL_ROOT, 'charts', 'png');
  const chartCsvDir = path.join(MATERIAL_ROOT, 'charts', 'csv');
  const imageDir = path.join(MATERIAL_ROOT, 'images', 'generated');
  const videoDir = path.join(MATERIAL_ROOT, 'videos');

  const charts = [
    ensureExists(path.join(chartPngDir, 'chart-01_global_market_size.png')),
    ensureExists(path.join(chartPngDir, 'chart-02_platform_mix.png')),
    ensureExists(path.join(chartPngDir, 'chart-03_fab_capex.png')),
    ensureExists(path.join(chartPngDir, 'chart-04_segment_growth_index.png'))
  ];

  const images = [
    ensureExists(path.join(imageDir, 'cover.png')),
    ensureExists(path.join(imageDir, 'comic-01.png')),
    ensureExists(path.join(imageDir, 'comic-02.png')),
    ensureExists(path.join(imageDir, 'infographic_1.png')),
    ensureExists(path.join(imageDir, 'infographic_2.png')),
    ensureExists(path.join(imageDir, 'infographic_3.png'))
  ];

  const tables = [
    ensureExists(path.join(chartCsvDir, 'chart-01_global_market_size.csv')),
    ensureExists(path.join(chartCsvDir, 'chart-02_platform_mix.csv'))
  ];

  const localVideos = walkFiles(videoDir).filter(file => /\.(mp4|mov|m4v|avi|mkv|webm)$/i.test(file));
  let videos = localVideos.slice(0, 2);
  if (videos.length < 2) {
    const fallback = [
      path.join(videoDir, 'web_search', 'youtube_download_results.json'),
      path.join(videoDir, 'web_search', 'youtube_candidates.json')
    ].filter(file => fs.existsSync(file));
    videos = videos.concat(fallback).slice(0, 2);
  }
  if (videos.length < 2) {
    throw new Error('video assets < 2 under ' + videoDir);
  }

  return { charts, images, tables, videos };
}

function buildAnchorsMarkdown(assets) {
  const lines = [];
  const pushAnchor = (kind, index, label, format, filePath) => {
    lines.push(`[素材锚点-${kind}-${String(index).padStart(2, '0')}：${label}｜文末素材区｜${format}｜\`${filePath}\`]`);
  };

  const chartLabels = ['全球规模增长图', '平台结构分化图', '晶圆厂资本开支图', '细分环节景气指数图'];
  assets.charts.forEach((filePath, idx) => pushAnchor('图表', idx + 1, chartLabels[idx] || path.basename(filePath), '图表', filePath));

  const imageLabels = ['封面图', '漫画图01', '漫画图02', '信息图01', '信息图02', '信息图03'];
  assets.images.forEach((filePath, idx) => pushAnchor('图片', idx + 1, imageLabels[idx] || path.basename(filePath), '图片', filePath));

  const tableLabels = ['全球规模增长数据表', '平台结构分化数据表'];
  assets.tables.forEach((filePath, idx) => pushAnchor('表格', idx + 1, tableLabels[idx] || path.basename(filePath), '表格', filePath));

  const videoLabels = ['视频素材01', '视频素材02'];
  assets.videos.forEach((filePath, idx) => pushAnchor('视频', idx + 1, videoLabels[idx] || path.basename(filePath), '视频', filePath));

  return lines.join('\n') + '\n';
}

async function chooseInsertHeading(client, docToken) {
  const blocks = await listBlocks(client, docToken);
  for (const heading of INSERT_HEADING_PRIORITY) {
    const block = findHeadingBlock(blocks, heading);
    if (block) return { heading, block, created: false };
  }

  const fallbackHeading = INSERT_HEADING_PRIORITY[0];
  await writeDocSection(client, docToken, fallbackHeading, { mode: 'plain_text_document' });

  const refreshed = await listBlocks(client, docToken);
  const block = findHeadingBlock(refreshed, fallbackHeading);
  if (!block) throw new Error('cannot create/find insert heading: ' + fallbackHeading);
  return { heading: fallbackHeading, block, created: true };
}

async function insertAfterHeading(client, docToken, headingBlock, text) {
  const sibling = await getSiblingContext(client, docToken, headingBlock.block_id);
  return writeDocSection(client, docToken, text, {
    mode: 'plain_text_document',
    parentBlockId: sibling.parentBlockId,
    index: sibling.index + 1
  });
}

async function main() {
  const { client, config } = createClient();

  const cleared_sections = [];
  for (const heading of CLEAR_HEADINGS) {
    const cleared = await clearSectionAfterHeading(client, DOC_TOKEN, heading);
    cleared_sections.push({
      heading,
      deleted: Number(cleared.deleted || 0),
      missing: Boolean(cleared.missing)
    });
  }

  const assets = pickAssets();
  const anchorMarkdown = buildAnchorsMarkdown(assets);
  fs.mkdirSync(path.dirname(ANCHOR_FILE), { recursive: true });
  fs.writeFileSync(ANCHOR_FILE, anchorMarkdown, 'utf8');

  const insertion = await chooseInsertHeading(client, DOC_TOKEN);
  await insertAfterHeading(client, DOC_TOKEN, insertion.block, anchorMarkdown.trim());

  const refill = await refillDocAnchorsWithLocalAssets(client, DOC_TOKEN, [ANCHOR_FILE]);

  const result = {
    doc_token: DOC_TOKEN,
    doc_url: buildDocUrl(DOC_TOKEN, config.host),
    anchors_total: Number(refill.anchors_total || 0),
    anchors_filled: Number(refill.anchors_filled || 0),
    cleared_sections,
    insert_heading: insertion.heading,
    insert_heading_created: insertion.created,
    anchor_file: ANCHOR_FILE,
    assets_used: {
      charts: assets.charts,
      images: assets.images,
      tables: assets.tables,
      videos: assets.videos
    },
    refill
  };

  fs.mkdirSync(path.dirname(REPORT_FILE), { recursive: true });
  fs.writeFileSync(REPORT_FILE, JSON.stringify(result, null, 2), 'utf8');
  console.log(JSON.stringify(result, null, 2));
}

main().catch(error => {
  console.error(error && error.stack ? error.stack : String(error));
  process.exit(1);
});
