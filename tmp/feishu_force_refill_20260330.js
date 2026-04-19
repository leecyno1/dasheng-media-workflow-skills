#!/usr/bin/env node

const fs = require('fs');
const path = require('path');
const {
  createClient,
  listBlocks,
  extractBlockText,
  getSiblingContext,
  writeDocSection,
  refillDocAnchorsWithLocalAssets
} = require('/Volumes/PSSD/Projects/公众号文章/skills/dasheng-daily-shared/runtime/feishu-client.js');

const REPORT_JSON = '/Users/lichengyin/Desktop/自媒体创作临时交付/2026-03-30/05_material/05_Feishu强制回填结果.json';

const DOCS = [
  {
    name: '半导体误判',
    token: 'JuDzdvqypoDDrixsn6rc2vJ3nGT',
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
    ]
  },
  {
    name: 'OpenClaw一键安装',
    token: 'NfNSdRRhFoqpK3xFZpEc35lKnGh',
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
    ]
  },
  {
    name: '供给秩序重估',
    token: 'IxsNdUZqkoGe45xfjyhcpLT4nxb',
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
    ]
  }
];

function textOf(block) {
  return String(extractBlockText(block) || '').trim();
}

function buildAnchorMarkdown(doc) {
  return doc.anchors.map(([kind, index, label, position, format, fileName]) => {
    const filePath = path.join(doc.dir, fileName);
    if (!fs.existsSync(filePath)) throw new Error('missing file: ' + filePath);
    return '[素材锚点-' + kind + '-' + index + '：' + label + '｜' + position + '｜' + format + '｜`' + filePath + '`]';
  }).join('\n');
}

async function findHeading(client, docToken, headingText) {
  const blocks = await listBlocks(client, docToken);
  return blocks.find(item => textOf(item) === headingText) || null;
}

async function insertAnchorsIfMissing(client, doc) {
  const blocks = await listBlocks(client, doc.token);
  const hasMarker = blocks.some(block => textOf(block).includes('素材锚点-'));
  const tempFile = path.join(doc.dir, '00_feishu_backfill_anchors.md');
  const anchorMarkdown = buildAnchorMarkdown(doc);
  fs.writeFileSync(tempFile, anchorMarkdown + '\n', 'utf8');
  if (hasMarker) return { inserted: false, tempFile };

  const heading = await findHeading(client, doc.token, '2026-03-30 素材回填区');
  if (!heading) throw new Error('missing heading 2026-03-30 素材回填区');

  const sibling = await getSiblingContext(client, doc.token, heading.block_id);
  await writeDocSection(client, doc.token, anchorMarkdown, {
    mode: 'plain_text_document',
    parentBlockId: sibling.parentBlockId,
    index: sibling.index + 1
  });
  return { inserted: true, tempFile };
}

async function main() {
  const { client } = createClient();
  const results = [];
  for (const doc of DOCS) {
    const result = { name: doc.name };
    try {
      const insertion = await insertAnchorsIfMissing(client, doc);
      result.anchor_inserted = insertion.inserted;
      result.refill = await refillDocAnchorsWithLocalAssets(client, doc.token, [insertion.tempFile]);
    } catch (error) {
      result.error = error && error.stack ? error.stack : String(error);
    }
    results.push(result);
  }
  fs.writeFileSync(REPORT_JSON, JSON.stringify(results, null, 2), 'utf8');
  console.log(JSON.stringify(results, null, 2));
}

main().catch(error => {
  console.error(error && error.stack ? error.stack : String(error));
  process.exit(1);
});
