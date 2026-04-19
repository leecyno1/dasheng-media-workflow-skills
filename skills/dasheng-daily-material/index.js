#!/usr/bin/env node

const fs = require('fs');
const path = require('path');
const {
  nowIso,
  readJsonIfExists,
  writeJson,
  ensureDir,
  sha1,
  createManifest,
  updateManifest,
  markStepCompleted,
  markStepFailed
} = require('../dasheng-daily-shared/runtime/manifest');
const {
  persistArtifact,
  persistTextArtifact,
  getArtifactsDir,
  appendArtifactRef
} = require('../dasheng-daily-shared/runtime/artifact-store');

const RUNTIME_DIR = path.join(__dirname, '..', 'dasheng-daily-shared', 'runtime-data');
const MATERIAL_LIMITS = {
  imageSearch: 10,
  videoSearch: 8,
  comicFrames: 10,
  memeIdeas: 3,
  infographicCount: 3,
  personPriority: 4,
  entityTopN: 8,
  newsScreenshot: 4,
  funnyComicCharacters: 3
};

function asArray(value) {
  return Array.isArray(value) ? value : value ? [value] : [];
}

function uniqueList(items = []) {
  return [...new Set(items.filter(Boolean).map(item => String(item).trim()).filter(Boolean))];
}

function normalizeEvidenceItem(item, index = 0, topicId = 'topic') {
  if (!item) {
    return {
      id: `${topicId}-evidence-${String(index + 1).padStart(2, '0')}`,
      title: `evidence_${index + 1}`,
      url: '',
      source: 'unknown',
      source_tier: null,
      note: '',
      platform: '',
      evidence_type: 'unknown'
    };
  }
  if (typeof item === 'string') {
    return {
      id: `${topicId}-evidence-${String(index + 1).padStart(2, '0')}`,
      title: item,
      url: '',
      source: 'brief',
      source_tier: null,
      note: '',
      platform: '',
      evidence_type: 'text'
    };
  }
  return {
    id: item.evidence_id || item.id || `${topicId}-evidence-${String(index + 1).padStart(2, '0')}`,
    title: item.title || item.name || `evidence_${index + 1}`,
    url: item.url || item.link || '',
    source: item.source || item.source_type || item.platform || 'brief',
    source_tier: item.source_tier || null,
    note: item.note || '',
    platform: item.platform || '',
    evidence_type: item.evidence_type || 'article_link'
  };
}

function normalizeLegacyBrief(brief) {
  const topicId = brief.topic_id || brief.meta?.id || `topic-${sha1(JSON.stringify(brief)).slice(0, 8)}`;
  const evidenceItems = asArray(brief.evidence_items || brief.references || brief.sources).map((item, index) => normalizeEvidenceItem(item, index, topicId));
  const proofRequirements = uniqueList([].concat(asArray(brief.proof_requirements), asArray(brief.evidence_requirements)));
  const claims = asArray(brief.claims).length
    ? asArray(brief.claims)
    : (proofRequirements.length ? proofRequirements : [brief.core_claim]).slice(0, 3).map((statement, index) => ({
        claim_id: `${topicId}-claim-${String(index + 1).padStart(2, '0')}`,
        section_id: `section-${String(index + 1).padStart(2, '0')}`,
        statement,
        counterpoint: brief.counterintuitive_angle || null,
        missing_proof: uniqueList(asArray(brief.missing_evidence).concat(asArray(brief.risk_notes))).slice(0, 3),
        chart_need: asArray(brief.chart_needs)[index] || null
      }));

  return {
    meta: brief.meta || {
      id: `${topicId}:material-input`,
      object_type: 'MaterialInput',
      run_id: '',
      version: '1.0.0',
      status: 'ready',
      generated_by: 'dasheng-daily-material'
    },
    topic_id: topicId,
    title: brief.title || brief.core_claim || topicId,
    core_claim: brief.core_claim || brief.title || topicId,
    angle_candidates: asArray(brief.angle_candidates),
    risk_notes: uniqueList(asArray(brief.risk_notes).concat(asArray(brief.missing_evidence))),
    evidence_requirements: proofRequirements,
    proof_requirements: proofRequirements,
    chart_needs: uniqueList(asArray(brief.chart_needs)),
    recommended_media: asArray(brief.recommended_media).length ? asArray(brief.recommended_media) : ['article', 'video', 'infographic'],
    evidence_items: evidenceItems,
    existing_evidence: evidenceItems,
    missing_evidence: uniqueList(asArray(brief.missing_evidence).concat(asArray(brief.risk_notes))),
    counterintuitive_angle: brief.counterintuitive_angle || null,
    claims,
    chart_anchors: asArray(brief.chart_anchors),
    image_queries: asArray(brief.image_queries),
    news_screenshot_queries: asArray(brief.news_screenshot_queries),
    video_queries: asArray(brief.video_queries),
    generated_visuals: brief.generated_visuals || null,
    scene_plan: asArray(brief.scene_plan),
    topic_type_hint: brief.topic_type_hint || '',
    article_markdown: brief.article_markdown || '',
    article_source: brief.article_source || null,
    material_decision: brief.material_decision || null,
    material_decision_file: brief.material_decision_file || null,
    generation_basis: brief.generation_basis || '',
    upstream_object_type: brief.meta?.object_type || 'ContentBrief'
  };
}

function normalizeReasoningSheet(sheet) {
  const topicId = sheet.topic_id || sheet.meta?.id || `topic-${sha1(JSON.stringify(sheet)).slice(0, 8)}`;
  const claims = asArray(sheet.claims).map((claim, index) => ({
    claim_id: claim.claim_id || `${topicId}-claim-${String(index + 1).padStart(2, '0')}`,
    section_id: claim.section_id || `section-${String(index + 1).padStart(2, '0')}`,
    statement: claim.statement || sheet.core_thesis || sheet.title || topicId,
    counterpoint: claim.counterpoint || null,
    missing_proof: uniqueList(asArray(claim.missing_proof)),
    chart_need: claim.chart_need || null
  }));
  const evidenceItems = asArray(sheet.evidence_items).map((item, index) => normalizeEvidenceItem(item, index, topicId));
  return {
    meta: sheet.meta || {
      id: `${topicId}:reasoning`,
      object_type: 'ReasoningSheet',
      run_id: '',
      version: '1.0.0',
      status: 'ready',
      generated_by: 'dasheng-daily-material'
    },
    topic_id: topicId,
    title: sheet.title || topicId,
    core_claim: sheet.core_thesis || sheet.title || topicId,
    angle_candidates: uniqueList([sheet.selection_reason, sheet.editor_note]),
    risk_notes: uniqueList(claims.flatMap(item => item.missing_proof)),
    evidence_requirements: claims.map(item => item.statement),
    proof_requirements: claims.map(item => item.statement),
    chart_needs: uniqueList(claims.map(item => item.chart_need)),
    recommended_media: ['article', 'video', 'infographic'],
    evidence_items: evidenceItems,
    existing_evidence: evidenceItems,
    missing_evidence: uniqueList(claims.flatMap(item => item.missing_proof)),
    counterintuitive_angle: claims.find(item => item.counterpoint)?.counterpoint || null,
    claims,
    structure_contract: sheet.structure_contract || {},
    chart_anchors: asArray(sheet.chart_anchors),
    image_queries: asArray(sheet.image_queries),
    news_screenshot_queries: asArray(sheet.news_screenshot_queries),
    video_queries: asArray(sheet.video_queries),
    generated_visuals: sheet.generated_visuals || null,
    scene_plan: asArray(sheet.scene_plan),
    topic_type_hint: sheet.topic_type_hint || '',
    article_markdown: sheet.article_markdown || '',
    article_source: sheet.article_source || null,
    material_decision: sheet.material_decision || null,
    material_decision_file: sheet.material_decision_file || null,
    generation_basis: sheet.generation_basis || '',
    upstream_object_type: sheet.meta?.object_type || 'ReasoningSheet'
  };
}

function collectReasoningSheetsFromManifest(manifestFile, parsed) {
  const baseDir = path.dirname(manifestFile);
  const drafts = asArray(parsed.drafts);
  const sheets = [];
  const files = [];
  drafts.forEach(draft => {
    const candidate = draft.reasoning_sheet_json || draft.reasoning_sheet_file || null;
    if (!candidate) return;
    const fullPath = path.isAbsolute(candidate) ? candidate : path.resolve(baseDir, candidate);
    if (!fs.existsSync(fullPath)) return;
    const payload = JSON.parse(fs.readFileSync(fullPath, 'utf8'));
    sheets.push(normalizeReasoningSheet(payload));
    files.push(fullPath);
  });
  return { sheets, files };
}

function resolveMaterialInputs(inputFile, options = {}) {
  const upstreamFile = inputFile
    || options.reasoning_sheet_file
    || options.reasoning_manifest_file
    || options.draft_manifest_file
    || options.content_briefs_file;
  if (!upstreamFile || !fs.existsSync(upstreamFile)) {
    throw new Error('缺少可用上游输入：需要 ReasoningSheet / draft_manifest / content_briefs_file');
  }

  const fullPath = path.resolve(upstreamFile);
  const parsed = JSON.parse(fs.readFileSync(fullPath, 'utf8'));
  let normalized = [];
  let upstreamType = 'unknown';
  let upstreamFiles = [fullPath];

  if (Array.isArray(parsed)) {
    const objectType = parsed[0]?.meta?.object_type || 'array';
    if (objectType === 'ReasoningSheet') {
      normalized = parsed.map(normalizeReasoningSheet);
      upstreamType = 'ReasoningSheet[]';
    } else {
      normalized = parsed.map(normalizeLegacyBrief);
      upstreamType = `${objectType}[]`;
    }
  } else if (parsed?.meta?.object_type === 'ReasoningSheet') {
    normalized = [normalizeReasoningSheet(parsed)];
    upstreamType = 'ReasoningSheet';
  } else if (Array.isArray(parsed?.drafts)) {
    const collected = collectReasoningSheetsFromManifest(fullPath, parsed);
    normalized = collected.sheets;
    upstreamFiles = uniqueList(upstreamFiles.concat(collected.files));
    upstreamType = 'DraftManifest';
  } else if (Array.isArray(parsed?.selected_topics) && parsed?.candidate_topics) {
    throw new Error('selected_topics.json 不能直接作为 material 输入；请传 draft_manifest.json 或 ReasoningSheet JSON');
  } else {
    normalized = [normalizeLegacyBrief(parsed)];
    upstreamType = parsed?.meta?.object_type || 'ContentBrief';
  }

  const runId = options.run_id || normalized?.[0]?.meta?.run_id || parsed?.run_id;
  if (!runId) {
    throw new Error('无法从上游对象推断 run_id');
  }
  if (!normalized.length) {
    throw new Error('未从上游对象解析出可用的 material 输入');
  }

  return {
    runId,
    upstreamFile: fullPath,
    upstreamType,
    upstreamFiles,
    items: normalized
  };
}

async function supplementMaterial(contentBriefsFile, options = {}) {
  let manifest;
  let manifestFile;

  try {
    const upstream = resolveMaterialInputs(contentBriefsFile, options);
    const briefs = upstream.items;
    const runId = upstream.runId;

    manifestFile = path.join(RUNTIME_DIR, 'runs', runId, 'run_manifest.json');
    manifest = readJsonIfExists(manifestFile);
    if (!manifest) {
      manifest = createManifest({
        workflowName: 'dasheng-daily',
        workflowVersion: '3.1.0',
        runId,
        currentStep: 'material'
      });
      manifest = updateManifest(manifest, {
        current_step: 'material',
        status: 'running',
        selection_state: {
          selected_topic_ids: briefs.map(brief => brief.topic_id).filter(Boolean),
          rejected_topic_ids: []
        },
        operator_decisions: [
          {
            at: nowIso(),
            step: 'material',
            decision: 'bootstrap_runtime_manifest_from_canonical_draft',
            note: '旧 runtime manifest 缺失，已从 canonical draft/material 输入自举。'
          }
        ]
      });
      writeJson(manifestFile, manifest);
    }

    console.log(`[material] 开始补充素材 run_id=${runId} upstream=${upstream.upstreamType}`);

    const artifactsDir = getArtifactsDir(RUNTIME_DIR, runId, 'material');
    ensureDir(artifactsDir);
    const packRoot = path.join(artifactsDir, 'pack_assets');
    ensureDir(packRoot);

    const materialPacks = briefs.map(brief => buildMaterialPack(brief, runId, packRoot));
    const resultFile = persistArtifact({
      baseDir: RUNTIME_DIR,
      runId,
      step: 'material',
      name: 'material-packs.json',
      data: materialPacks
    });
    const materialDoc = persistTextArtifact({
      baseDir: RUNTIME_DIR,
      runId,
      step: 'material',
      name: '04_MaterialPack.md',
      content: renderMaterialPackMarkdown(runId, upstream, materialPacks, packRoot)
    });
    const reportFile = persistTextArtifact({
      baseDir: RUNTIME_DIR,
      runId,
      step: 'material',
      name: '04_Material_报告.md',
      content: renderMaterialReportMarkdown(runId, materialPacks, packRoot)
    });
    const stageManifest = buildStageManifest(runId, upstream, materialPacks, packRoot);
    const stageManifestFile = persistArtifact({
      baseDir: RUNTIME_DIR,
      runId,
      step: 'material',
      name: 'material_manifest.json',
      data: stageManifest
    });

    manifest = appendArtifactRef(manifest, {
      step: 'material',
      object_type: 'MaterialPack',
      count: materialPacks.length,
      file: resultFile,
      doc_url: null
    });
    manifest = appendArtifactRef(manifest, {
      step: 'material',
      object_type: 'MaterialMarkdown',
      count: 1,
      file: materialDoc,
      doc_url: null
    });
    manifest = appendArtifactRef(manifest, {
      step: 'material',
      object_type: 'MaterialReport',
      count: 1,
      file: reportFile,
      doc_url: null
    });
    manifest = appendArtifactRef(manifest, {
      step: 'material',
      object_type: 'MaterialManifest',
      count: 1,
      file: stageManifestFile,
      doc_url: null
    });

    manifest = markStepCompleted(manifest, 'material');
    manifest = updateManifest(manifest, {
      current_step: 'rewrite',
      status: 'running'
    });
    writeJson(manifestFile, manifest);

    console.log(`[material] 完成，共 ${materialPacks.length} 个素材包`);
    return {
      success: true,
      run_id: runId,
      total_packs: materialPacks.length,
      material_packs_file: resultFile,
      material_markdown: materialDoc,
      material_report: reportFile,
      material_manifest_file: stageManifestFile,
      manifest_file: manifestFile,
      next_step: 'publish_or_layer5'
    };
  } catch (error) {
    if (manifest && manifestFile) {
      manifest = markStepFailed(manifest, 'material', error.message);
      writeJson(manifestFile, manifest);
    }
    console.error('[material] 错误:', error.message);
    throw error;
  }
}

function buildMaterialPack(brief, runId, packRoot) {
  const createdAt = nowIso();
  const topicType = inferTopicType(brief);
  const topicSlug = makeTopicSlug(brief);
  const topicRoot = path.join(packRoot, topicSlug);
  ensureTopicDirectories(topicRoot);
  const plan = buildTopicPlan(brief, topicType, topicSlug);
  writeTopicArtifacts(topicRoot, plan);

  return {
    meta: {
      id: `${runId}:material:${brief.meta.id.split(':').pop()}`,
      object_type: 'MaterialPack',
      run_id: runId,
      version: '3.1.0',
      status: 'ready',
      generated_by: 'dasheng-daily-material',
      input_digest: sha1(brief.meta.id + brief.title),
      upstream_ids: [brief.meta.id],
      doc_refs: [],
      created_at: createdAt,
      updated_at: createdAt
    },
    topic_id: brief.topic_id,
    title: brief.title,
    topic_type: topicType,
    upstream_object_type: brief.upstream_object_type || brief.meta?.object_type || 'unknown',
    claim_bindings: plan.claim_bindings,
    materials: {
      images: buildImageMaterials(plan),
      videos: buildVideoMaterials(plan),
      quotes: buildQuoteMaterials(brief),
      data_points: buildDataPointMaterials(plan),
      references: buildReferenceMaterials(plan)
    },
    coverage_notes: [
      `生成依据：${plan.generation_basis || 'reasoning_sheet'}`,
      `已覆盖主张：${brief.core_claim}`,
      `建议媒介：${(brief.recommended_media || []).join(', ') || 'article / video / infographic'}`,
      `AI 图像分支：连环画 ${plan.generated.comic_storyboard.length} 张 / 梗图 ${plan.generated.meme_prompts.length} 张 / 搞笑人物 ${(plan.generated.funny_comic_character_prompts || []).length} 张`,
      `Layer 5：${plan.layer5.template_id}`,
      '视频质检：不设固定分辨率门槛，允许新闻直播/访谈，过滤口播自媒体'
    ],
    gaps: buildGaps(brief, plan),
    asset_root: topicRoot,
    layer5_delivery: plan.layer5,
    generated_visuals: plan.generated,
    video_quality_policy: plan.video_quality_policy
  };
}

function makeTopicSlug(brief) {
  const base = String(brief.topic_id || brief.title || 'topic')
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9\u4e00-\u9fa5_-]+/g, '-')
    .replace(/-+/g, '-')
    .replace(/^-|-$/g, '');
  if (base) return base;
  return `topic-${sha1(brief.title || JSON.stringify(brief)).slice(0, 8)}`;
}

function inferTopicType(brief) {
  const hinted = String(
    brief.topic_type_hint
    || brief.material_decision?.topic_type
    || ''
  ).trim();
  if (hinted) {
    return hinted;
  }
  const text = [
    brief.title,
    brief.core_claim,
    ...(brief.angle_candidates || []),
    ...(brief.evidence_requirements || [])
  ].join(' ');

  const financePatterns = [
    /黄金|白银|原油|油价|利率|通胀|再通胀|债券|股市|etf|期货|宏观|市场|货币|美联储|fed/ig
  ];
  const geoPatterns = [
    /战争|制裁|地缘|外交|台海|日本|高市|安全|联盟|选举|中东|航运|冲突|军事|霍尔木兹|海峡|封锁|停火|油轮|黎巴嫩|伊朗|以色列/ig
  ];
  const techPatterns = [
    /ai|芯片|算力|科技|硬件|开源|平台|软件/ig
  ];

  const scorePatterns = (patterns) =>
    patterns.reduce((sum, pattern) => sum + ((text.match(pattern) || []).length), 0);

  const financeScore = scorePatterns(financePatterns);
  const geoScore = scorePatterns(geoPatterns);
  const techScore = scorePatterns(techPatterns);
  const strongGeo = /(战争|冲突|中东|霍尔木兹|海峡|封锁|停火|军事|外交|航运)/i.test(text);

  if (geoScore > financeScore && geoScore > 0) {
    return 'geopolitics';
  }
  if (financeScore > geoScore && financeScore > 0) {
    return 'finance_macro';
  }
  if (geoScore > 0 && strongGeo) {
    return 'geopolitics';
  }
  if (techScore > 0) {
    return 'industry_tech';
  }
  if (financeScore > 0) {
    return 'finance_macro';
  }
  if (geoScore > 0) {
    return 'geopolitics';
  }
  return 'general_commentary';
}

function ensureTopicDirectories(topicRoot) {
  [
    'charts/csv',
    'charts/markdown',
    'charts/config',
    'charts/png',
    'images/generated',
    'images/web_search',
    'videos/source_links',
    'videos/web_search',
    'prompts',
    'config',
    'layer5'
  ].forEach(dir => ensureDir(path.join(topicRoot, dir)));
}

function buildTopicPlan(brief, topicType, topicSlug) {
  const evidenceItems = collectEvidenceItems(brief);
  const claimBindings = buildClaimBindings(brief);
  const chartAnchors = buildChartAnchors(brief, topicType);
  const chartQualityGate = buildChartQualityGate();
  const imagePlan = buildImageQueries(brief, topicType);
  const videoQueries = buildVideoQueries(brief, topicType);
  const videoQualityPolicy = buildVideoQualityPolicy();
  const generated = buildGeneratedVisualPlan(brief, topicType);
  const layer5 = buildLayer5Plan(topicType, chartAnchors, brief);

  return {
    topic_slug: topicSlug,
    topic_type: topicType,
    title: brief.title,
    thesis: brief.core_claim,
    generation_basis: brief.generation_basis || 'reasoning_sheet',
    article_source: brief.article_source || null,
    article_markdown: brief.article_markdown || '',
    material_decision_file: brief.material_decision_file || null,
    claim_bindings: claimBindings,
    evidence_items: evidenceItems,
    chart_anchors: chartAnchors,
    chart_quality_gate: chartQualityGate,
    web_search: {
      image_queries: imagePlan.image_queries,
      news_screenshot_queries: imagePlan.news_screenshot_queries,
      video_queries: videoQueries
    },
    video_quality_policy: videoQualityPolicy,
    entity_signals: imagePlan.entity_signals,
    generated,
    layer5,
    recommended_sources: recommendDataSources(topicType, evidenceItems),
    scene_plan: buildScenePlan(brief, topicType)
  };
}

function buildClaimBindings(brief) {
  const existingClaims = Array.isArray(brief.claims) ? brief.claims : [];
  if (existingClaims.length) {
    return existingClaims.map((claim, index) => ({
      claim_id: claim.claim_id || `${brief.topic_id || 'topic'}-claim-${String(index + 1).padStart(2, '0')}`,
      section_id: claim.section_id || `section-${String(index + 1).padStart(2, '0')}`,
      statement: claim.statement || claim.title || brief.core_claim,
      counterpoint: claim.counterpoint || brief.counterintuitive_angle || null,
      missing_proof: claim.missing_proof || brief.missing_evidence || [],
      chart_need: claim.chart_need || null
    }));
  }

  const requirements = []
    .concat(Array.isArray(brief.proof_requirements) ? brief.proof_requirements : [])
    .concat(Array.isArray(brief.evidence_requirements) ? brief.evidence_requirements : []);

  const seeds = requirements.length ? requirements.slice(0, 3) : [brief.core_claim, '补结构性证据', '补数据与图表'];
  return seeds.map((statement, index) => ({
    claim_id: `${brief.topic_id || 'topic'}-claim-${String(index + 1).padStart(2, '0')}`,
    section_id: `section-${String(index + 1).padStart(2, '0')}`,
    statement,
    counterpoint: brief.counterintuitive_angle || null,
    missing_proof: brief.missing_evidence || brief.risk_notes || [],
    chart_need: Array.isArray(brief.chart_needs) ? brief.chart_needs[index] || null : null
  }));
}

function bindAsset(plan, index, assetType, payload = {}) {
  const claims = Array.isArray(plan.claim_bindings) && plan.claim_bindings.length
    ? plan.claim_bindings
    : [{ claim_id: 'claim-01', section_id: 'section-01', statement: plan.thesis }];
  const claim = claims[index % claims.length];
  const relevanceBase = assetType === 'chart' ? 0.96 : assetType === 'reference' ? 0.92 : assetType === 'video' ? 0.84 : 0.88;
  return {
    claim_id: claim.claim_id,
    section_id: claim.section_id,
    usage_type: payload.usage_type || assetType,
    relevance_score: Number((payload.relevance_score || Math.max(0.55, relevanceBase - index * 0.03)).toFixed(2)),
    editor_status: payload.editor_status || 'pending_review',
    ...payload
  };
}

function buildChartQualityGate() {
  return {
    enabled: true,
    version: '1.0',
    thresholds: {
      cv_min: 0.03,
      slope_abs_min: 0.005,
      r2_min: 0.25,
      trend_strength_min: 0.30,
      heatmap_var_min: 0.05
    },
    fallback: {
      mode: 'logical_relation_table',
      outputs: ['charts/csv/*.csv', 'charts/markdown/*.md'],
      trigger_rule: '当 CV、斜率、R²、趋势强度均不达标时，不生成 PNG，仅输出逻辑关系表格'
    }
  };
}

function collectEvidenceItems(brief) {
  const candidates = []
    .concat(Array.isArray(brief.evidence_items) ? brief.evidence_items : [])
    .concat(Array.isArray(brief.existing_evidence) ? brief.existing_evidence : [])
    .concat(Array.isArray(brief.references) ? brief.references : [])
    .concat(Array.isArray(brief.sources) ? brief.sources : []);

  const normalized = candidates
    .filter(Boolean)
    .map((item, index) => {
      if (typeof item === 'string') {
        return { id: `source-${index + 1}`, title: item, url: '', source: 'brief' };
      }
      return {
        id: item.id || `source-${index + 1}`,
        title: item.title || item.name || `source-${index + 1}`,
        url: item.url || item.link || '',
        source: item.source || item.platform || 'brief',
        platform: item.platform || '',
        note: item.note || '',
        heat: item.heat ?? null
      };
    });

  const seen = new Set();
  return normalized.filter(item => {
    const key = `${item.title}|${item.url}`;
    if (seen.has(key)) return false;
    seen.add(key);
    return true;
  });
}

function buildChartAnchors(brief, topicType) {
  const overrideAnchors = asArray(brief.chart_anchors).filter(Boolean);
  if (overrideAnchors.length) {
    return overrideAnchors.map((item, index) => ({
      anchor_id: item.anchor_id || `chart-${String(index + 1).padStart(2, '0')}`,
      title: item.title || `图表 ${index + 1}`,
      purpose: item.purpose || item.why || '补充正文论证',
      data_sources: uniqueList(asArray(item.data_sources).length ? asArray(item.data_sources) : ['手工整理 CSV']),
      chart_type: item.chart_type || 'line',
      section_id: item.section_id || '',
      only_if_worth_chart: item.only_if_worth_chart !== false
    }));
  }
  if (topicType === 'finance_macro') {
    return [
      {
        anchor_id: 'chart-01',
        title: '通胀 / 利率 / 核心资产三联图',
        purpose: '判断再通胀叙事是否进入资产定价主线',
        data_sources: ['FRED', 'tushare', 'akshare'],
        chart_type: 'multi_line'
      },
      {
        anchor_id: 'chart-02',
        title: '商品价格与通胀预期联动图',
        purpose: '识别油价、金价、breakeven、实际利率之间的牵引关系',
        data_sources: ['FRED', 'tushare', 'akshare'],
        chart_type: 'dual_axis'
      },
      {
        anchor_id: 'chart-03',
        title: 'ETF/持仓/成交热度图',
        purpose: '补交易层证据，而不只停留在宏观判断',
        data_sources: ['tushare', '新浪财经', '交易所数据'],
        chart_type: 'bar'
      },
      {
        anchor_id: 'chart-04',
        title: '情景收益矩阵',
        purpose: '给出黄金、白银、原油、长债、权益在不同通胀路径下的映射',
        data_sources: ['手工整理 CSV'],
        chart_type: 'heatmap'
      }
    ];
  }

  if (topicType === 'geopolitics') {
    return [
      {
        anchor_id: 'chart-01',
        title: '关键事件时间线',
        purpose: '把冲突、政策、制裁、表态放到统一时间轴',
        data_sources: ['人民网', '新华社', 'AP', '官方声明'],
        chart_type: 'timeline'
      },
      {
        anchor_id: 'chart-02',
        title: '结构压力图',
        purpose: '展示人口、外劳、防务、供应链等底层约束',
        data_sources: ['官方统计', '世界银行', 'OECD'],
        chart_type: 'bar_line'
      },
      {
        anchor_id: 'chart-03',
        title: '阵营/联盟关系图',
        purpose: '帮助读者看清力量重组，而不是只看单一人物',
        data_sources: ['公开新闻', '政府官网'],
        chart_type: 'network_matrix'
      },
      {
        anchor_id: 'chart-04',
        title: '风险外溢地图',
        purpose: '把航运、能源、台海、制裁路径可视化',
        data_sources: ['地图底图', '公开路线数据'],
        chart_type: 'map'
      }
    ];
  }

  return [
    {
      anchor_id: 'chart-01',
      title: '主判断核心变量趋势图',
      purpose: '验证主线变量是否在中期趋势上成立',
      data_sources: ['akshare', 'tushare', '官方统计', 'FRED'],
      chart_type: 'line'
    },
    {
      anchor_id: 'chart-02',
      title: '事件冲击与市场反应对照图',
      purpose: '把事件与价格/情绪/利率变化放在同一时间轴',
      data_sources: ['akshare', 'tushare', '新浪财经'],
      chart_type: 'dual_axis'
    },
    {
      anchor_id: 'chart-03',
      title: '结构拆解图',
      purpose: '把总判断拆成 3-5 个支撑维度',
      data_sources: ['官方统计', '研究报告', '手工整理 CSV'],
      chart_type: 'bar'
    },
    {
      anchor_id: 'chart-04',
      title: '风险情景图',
      purpose: '给出不同情景下的观察变量与触发条件',
      data_sources: ['手工整理 CSV'],
      chart_type: 'scenario'
    }
  ];
}

function buildImageQueries(brief, topicType) {
  const entitySignals = buildEntitySignals(brief);
  const imageOverride = asArray(brief.image_queries).filter(Boolean);
  const screenshotOverride = asArray(brief.news_screenshot_queries).filter(Boolean);
  if (imageOverride.length || screenshotOverride.length) {
    return {
      image_queries: imageOverride.map((item, index) => (
        typeof item === 'string'
          ? { query: item, entity_type: 'topic', entity: '', priority: 100 - index, channel: 'wikimedia' }
          : {
              query: item.query || '',
              entity_type: item.entity_type || 'topic',
              entity: item.entity || '',
              priority: Number(item.priority || (100 - index)),
              channel: item.channel || 'wikimedia'
            }
      )).filter(item => item.query),
      news_screenshot_queries: screenshotOverride.map((item, index) => (
        typeof item === 'string'
          ? { query: item, channel: 'news_screenshot', priority: 180 - index }
          : {
              query: item.query || '',
              channel: item.channel || 'news_screenshot',
              priority: Number(item.priority || (180 - index))
            }
      )).filter(item => item.query),
      entity_signals: entitySignals
    };
  }
  const base = extractKeywords(brief);
  const personQueries = entitySignals.people
    .slice(0, MATERIAL_LIMITS.personPriority)
    .flatMap((item, idx) => ([
      {
        query: `${item.name} portrait news photo`,
        entity_type: 'person',
        entity: item.name,
        priority: 300 - idx * 2,
        channel: 'wikimedia'
      },
      {
        query: `${item.name} speech press conference`,
        entity_type: 'person',
        entity: item.name,
        priority: 299 - idx * 2,
        channel: 'wikimedia'
      }
    ]));
  const countryOrgQueries = []
    .concat(
      entitySignals.countries.slice(0, 3).map((item, idx) => ({
        query: `${item.name} government building crowd`,
        entity_type: 'country',
        entity: item.name,
        priority: 220 - idx,
        channel: 'wikimedia'
      }))
    )
    .concat(
      entitySignals.orgs.slice(0, 3).map((item, idx) => ({
        query: `${item.name} headquarters exterior`,
        entity_type: 'org',
        entity: item.name,
        priority: 210 - idx,
        channel: 'wikimedia'
      }))
    );
  const querySets = {
    finance_macro: [
      'oil tanker aerial',
      'gold bullion vault',
      'futures trading screen',
      'stock market floor crowd',
      'federal reserve building exterior',
      'oil refinery aerial',
      'shipping port cranes aerial',
      'commodity warehouse barrels',
      'investor crowd watching market',
      `${base.secondary} chart screen`
    ],
    geopolitics: [
      `${base.primary} parliament speech crowd`,
      `${base.primary} rally crowd`,
      `${base.primary} military drill`,
      `${base.primary} shipping route map`,
      `${base.primary} parliament building exterior`,
      `${base.primary} elderly crowd city`,
      `${base.primary} port aerial`,
      `${base.primary} diplomatic meeting`,
      `${base.primary} protest crowd`,
      `${base.primary} border checkpoint`
    ],
    industry_tech: [
      `${base.primary} factory production line`,
      `${base.primary} chip lab`,
      `${base.primary} server room`,
      `${base.primary} conference crowd`,
      `${base.primary} robotics assembly`,
      `${base.primary} clean room`,
      `${base.primary} engineer team`,
      `${base.primary} warehouse logistics`,
      `${base.primary} keynote stage`,
      `${base.primary} industrial aerial`
    ],
    general_commentary: [
      `${base.primary} news conference`,
      `${base.primary} city crowd`,
      `${base.primary} office team`,
      `${base.primary} dramatic scene`,
      `${base.primary} protest crowd`,
      `${base.primary} aerial city`,
      `${base.primary} meeting room`,
      `${base.primary} chart infographic`,
      `${base.primary} documentary still`,
      `${base.primary} headline concept`
    ]
  };

  const fallbackQueries = (querySets[topicType] || querySets.general_commentary).map((query, idx) => ({
    query,
    entity_type: 'topic',
    entity: '',
    priority: 100 - idx,
    channel: 'wikimedia'
  }));

  const dedup = new Map();
  personQueries
    .concat(countryOrgQueries)
    .concat(fallbackQueries)
    .forEach(item => {
      const key = String(item.query || '').trim().toLowerCase();
      if (!key) return;
      const previous = dedup.get(key);
      if (!previous || Number(item.priority || 0) > Number(previous.priority || 0)) {
        dedup.set(key, item);
      }
    });

  const imageQueries = Array.from(dedup.values())
    .sort((a, b) => Number(b.priority || 0) - Number(a.priority || 0))
    .slice(0, MATERIAL_LIMITS.imageSearch);
  const newsScreenshotQueries = buildNewsScreenshotQueries(brief, topicType, base, entitySignals);

  return {
    image_queries: imageQueries,
    news_screenshot_queries: newsScreenshotQueries,
    entity_signals: entitySignals
  };
}

function buildVideoQueries(brief, topicType) {
  const override = asArray(brief.video_queries).filter(Boolean);
  if (override.length) {
    return override.map(item => (typeof item === 'string' ? item : item.query || '')).filter(Boolean).slice(0, MATERIAL_LIMITS.videoSearch);
  }
  const base = extractKeywords(brief);
  const querySets = {
    finance_macro: [
      'stock market b roll 4k newsroom',
      'oil tanker aerial 4k',
      'refinery aerial 4k',
      'gold vault documentary 4k',
      'federal reserve press briefing live',
      'commodities trading floor 4k',
      'shipping port cranes aerial 4k',
      'financial news interview raw footage'
    ],
    geopolitics: [
      `${base.primary} parliament session 4k`,
      `${base.primary} election rally crowd 4k live feed`,
      `${base.primary} military drill 4k`,
      `${base.primary} navy fleet aerial 4k`,
      `${base.primary} port shipping lane 4k`,
      `${base.primary} government building exterior 4k news live`,
      `${base.primary} city crowd documentary 4k`,
      `${base.primary} diplomatic summit interview raw footage`
    ],
    industry_tech: [
      `${base.primary} factory 4k`,
      `${base.primary} server room 4k`,
      `${base.primary} assembly line 4k`,
      `${base.primary} keynote event crowd 4k official stream`,
      `${base.primary} robotics lab 4k`,
      `${base.primary} newsroom interview footage`,
      `${base.primary} semiconductor fab 4k`,
      `${base.primary} cargo logistics 4k`
    ],
    general_commentary: [
      `${base.primary} documentary b roll 4k`,
      `${base.primary} city aerial 4k`,
      `${base.primary} public crowd 4k`,
      `${base.primary} government meeting 4k`,
      `${base.primary} news conference 4k live`,
      `${base.primary} industrial aerial 4k`,
      `${base.primary} interview raw footage`,
      `${base.primary} official briefing live stream`
    ]
  };
  return (querySets[topicType] || querySets.general_commentary).slice(0, MATERIAL_LIMITS.videoSearch);
}

function buildVideoQualityPolicy() {
  return {
    min_height: 0,
    min_duration_seconds: 8,
    min_scene_changes: 2,
    min_scene_change_rate: 0.08,
    allow_news_live_or_interview: true,
    block_self_media_talking_head: true,
    reject_screenshot_montage: true,
    report_fields: [
      'source_category',
      'source_ok',
      'resolution_height',
      'duration_seconds',
      'scene_changes',
      'scene_change_rate',
      'anti_screenshot_montage_pass',
      'final_pass',
      'fail_reasons'
    ]
  };
}

function buildGeneratedVisualPlan(brief, topicType) {
  if (brief.generated_visuals) {
    return {
      cover_prompt: brief.generated_visuals.cover_prompt || `围绕“${brief.title}”生成封面，突出主判断。`,
      infographic_prompts: asArray(brief.generated_visuals.infographic_prompts),
      comic_storyboard: asArray(brief.generated_visuals.comic_storyboard),
      meme_prompts: asArray(brief.generated_visuals.meme_prompts),
      funny_comic_character_prompts: asArray(brief.generated_visuals.funny_comic_character_prompts)
    };
  }
  const base = extractKeywords(brief);
  return {
    cover_prompt: `围绕“${brief.title}”生成封面，突出 ${base.primary} 与 ${base.secondary} 的冲突感，适合财经/时政深度内容封面，避免口播截图感。`,
    infographic_prompts: buildInfographicPrompts(brief, topicType),
    comic_storyboard: buildComicStoryboard(brief, topicType),
    meme_prompts: buildMemePrompts(topicType),
    funny_comic_character_prompts: buildFunnyComicCharacterPrompts(brief, topicType)
  };
}

function buildFunnyComicCharacterPrompts(brief, topicType) {
  const base = extractKeywords(brief);
  const roleMap = {
    finance_macro: ['紧张交易员', '淡定央行官员', '慌张散户'],
    geopolitics: ['严肃发言人', '焦虑外交官', '围观群众'],
    industry_tech: ['熬夜工程师', '产品经理', '机器人助手'],
    general_commentary: ['新闻主播', '数据分析师', '路人评论员']
  };
  const roles = roleMap[topicType] || roleMap.general_commentary;
  return roles.slice(0, MATERIAL_LIMITS.funnyComicCharacters).map((role, index) => (
    `搞笑漫画人物设定 ${index + 1}：${role}，主题“${brief.title}”，围绕 ${base.primary} / ${base.secondary}。` +
    '简单卡通线条、纯色背景、轻松表情、低细节，不要复杂光影与写实质感。'
  ));
}

function buildInfographicPrompts(brief, topicType) {
  const prompts = [
    `基于题目“${brief.title}”生成一张 dense-modules 信息图，拆出 4 个核心观点、4 个证据位、2 个风险位。`,
    `基于主判断“${brief.core_claim}”生成一张 hierarchical-layers 信息图，把表象、机制、影响、建议四层可视化。`,
    `为“${brief.title}”生成一张 dashboard 风格信息图，包含关键指标、关键事件、关键结论。`
  ];
  if (topicType === 'geopolitics') {
    prompts[2] = `为“${brief.title}”生成一张 winding-roadmap 或 map 叙事信息图，展示事件推进、角色、地区外溢。`;
  }
  return prompts.slice(0, MATERIAL_LIMITS.infographicCount);
}

function buildComicStoryboard(brief, topicType) {
  return buildScenePlan(brief, topicType)
    .slice(0, MATERIAL_LIMITS.comicFrames)
    .map((beat, index) => ({
      frame_id: `comic-${String(index + 1).padStart(2, '0')}`,
      title: beat.title,
      visual_prompt: `连环画第 ${index + 1} 格：${beat.visual}。风格统一，适合视频插画，不要真人采访截图感。`,
      caption_hint: beat.caption
    }));
}

function buildMemePrompts(topicType) {
  if (topicType === 'finance_macro') {
    return [
      '梗图：熊猫与鹰围着一桶原油拉扯，旁边金条和债券在打架，表达“市场表面交易事件，底层在交易通胀与利率”。',
      '梗图：交易员看着油价、金价、利率三块屏幕同时爆红，表情崩溃，表达“再通胀不是单线行情”。',
      '梗图：美联储像交通警察同时拦增长和通胀两辆失控汽车，表达“higher inflation and slower growth”。'
    ];
  }
  if (topicType === 'geopolitics') {
    return [
      '梗图：熊猫、鹰和武士在地图边上拉扯航运线，表达“安全叙事外溢到贸易与供应链”。',
      '梗图：政客在舞台上高喊强硬口号，后台堆满老龄化、外劳、财政压力账单，表达“强硬叙事背后的结构困境”。',
      '梗图：多国棋手围着东亚地图下棋，棋盘边缘是油轮和芯片，表达“地区安全波动影响全球市场”。'
    ];
  }
  return [
    '梗图：两拨人对着同一新闻各喊各的，最后图表从背后砸下来，表达“观点要回到证据”。',
    '梗图：作者追着热点跑，数据在后面追作者，表达“别只看情绪，先看变量”。',
    '梗图：一篇稿子前半段像吵架，后半段被图表收束，表达“讨论最终要回到结构”。'
  ];
}

function buildLayer5Plan(topicType, chartAnchors, brief) {
  const topicTitle = brief?.title || '';
  const coreClaim = brief?.core_claim || '';
  const topicId = brief?.topic_id || '';

  if (topicType === 'finance_macro') {
    return {
      template_id: 'market_story',
      template_name: '市场叙事面板 (Market Story Panel)',
      worldmonitor_project: '/Volumes/PSSD/Projects/worldmonitor',
      worldmonitor_data_dir: '/Volumes/PSSD/Projects/worldmonitor/data',
      worldmonitor_public_dir: '/Volumes/PSSD/Projects/worldmonitor/public',
      worldmonitor_entry: 'index.html',
      proxy_port: 8787,
      current_status: 'inactive',
      inputs: ['article.md', 'scene_plan.json', 'charts/*.csv', 'charts/*.png', 'key_metrics.json'],
      preferred_components: ['MarketPanel', 'EconomicPanel', 'CountryTimeline'],
      page_modules: ['hero-summary', 'key-metrics-strip', 'timeline-repricing', 'chart-gallery', 'embedded-video'],
      chart_anchor_ids: chartAnchors.map(item => item.anchor_id),
      thread_id: '019d31c5-bb7f-7a40-a087-9d219e9bd6ab',
      artifact_tag: 'layer5_finance_market_story',
      topic_slug: topicId,
      topic_title: topicTitle,
      core_claim: coreClaim,
      required_csvs: chartAnchors.map(item => `charts/csv/${item.anchor_id}.csv`),
      required_pngs: chartAnchors.map(item => `charts/png/${item.anchor_id}.png`),
      narrative_schema: 'timeline_then_signals',
      data_granularity: 'daily',
      risk_scenarios: ['再通胀抬升', '增长走弱', '利率高位钝化', '风险偏好回升'],
      key_metrics_to_emit: ['SPX', 'US10Y', 'Oil', 'Gold', 'Breakeven10Y'],
      layout_hint: 'market_panel_left + chart_gallery_right + metrics_strip_bottom'
    };
  }
  if (topicType === 'geopolitics') {
    return {
      template_id: 'geo_timeline_map',
      template_name: '地缘时政时间线地图 (Geo Timeline Map)',
      worldmonitor_project: '/Volumes/PSSD/Projects/worldmonitor',
      worldmonitor_data_dir: '/Volumes/PSSD/Projects/worldmonitor/data',
      worldmonitor_public_dir: '/Volumes/PSSD/Projects/worldmonitor/public',
      worldmonitor_entry: 'index.html',
      proxy_port: 8787,
      current_status: 'inactive',
      inputs: ['article.md', 'event_timeline.json', 'map_layers.geojson', 'charts/*.png', 'scene_plan.json'],
      preferred_components: ['StrategicRiskPanel', 'StrategicPosturePanel', 'DeckGLMap', 'CountryTimeline'],
      page_modules: ['hero-summary', 'actor-matrix', 'event-timeline', 'map-risk-layer', 'media-gallery'],
      chart_anchor_ids: chartAnchors.map(item => item.anchor_id),
      thread_id: '019d31c5-bb7f-7a40-a087-9d219e9bd6ab',
      artifact_tag: 'layer5_geo_timeline_map',
      topic_slug: topicId,
      topic_title: topicTitle,
      core_claim: coreClaim,
      required_csvs: chartAnchors.map(item => `charts/csv/${item.anchor_id}.csv`),
      required_pngs: chartAnchors.map(item => `charts/png/${item.anchor_id}.png`),
      narrative_schema: 'actors_then_events_then_risks',
      data_granularity: 'event_based',
      risk_scenarios: ['安全升级', '劳动力缺口', '外交摩擦', '供应链波动'],
      key_metrics_to_emit: ['population', 'aged_65_pct', 'military_gdp_pct', 'security_score'],
      layout_hint: 'timeline_top + map_center + actor_matrix_bottom'
    };
  }
  return {
    template_id: 'story_page',
    template_name: '通用故事面板 (Story Page)',
    worldmonitor_project: '/Volumes/PSSD/Projects/worldmonitor',
    worldmonitor_data_dir: '/Volumes/PSSD/Projects/worldmonitor/data',
    worldmonitor_public_dir: '/Volumes/PSSD/Projects/worldmonitor/public',
    worldmonitor_entry: 'index.html',
    proxy_port: 8787,
    current_status: 'inactive',
    inputs: ['article.md', 'chart_gallery.json', 'scene_plan.json'],
    preferred_components: ['CountryTimeline'],
    page_modules: ['hero-summary', 'chart-gallery', 'media-gallery'],
    chart_anchor_ids: chartAnchors.map(item => item.anchor_id),
    thread_id: '019d31c5-bb7f-7a40-a087-9d219e9bd6ab',
    artifact_tag: 'layer5_story_page',
    topic_slug: topicId,
    topic_title: topicTitle,
    core_claim: coreClaim,
    required_csvs: chartAnchors.map(item => `charts/csv/${item.anchor_id}.csv`),
    required_pngs: chartAnchors.map(item => `charts/png/${item.anchor_id}.png`),
    narrative_schema: 'thesis_then_evidence_then_risks',
    data_granularity: 'monthly',
    risk_scenarios: [],
    key_metrics_to_emit: [],
    layout_hint: 'chart_gallery_centered'
  };
}

function recommendDataSources(topicType, evidenceItems) {
  const linked = evidenceItems.filter(item => item.url).map(item => item.url).slice(0, 5);
  if (topicType === 'finance_macro') {
    return ['akshare', 'tushare', 'FRED', 'BLS', 'BEA', '新浪财经'].concat(linked);
  }
  if (topicType === 'geopolitics') {
    return ['人民网', '新华社', '政府官网', 'AP', 'Reuters', '世界银行'].concat(linked);
  }
  return ['akshare', 'tushare', '新浪财经', '人民网', '新华社', '公开官方声明'].concat(linked);
}

function buildScenePlan(brief, topicType) {
  const override = asArray(brief.scene_plan).filter(Boolean);
  if (override.length) {
    return override.map((item, index) => ({
      title: item.title || `Scene ${index + 1}`,
      visual: item.visual || item.scene || '关键画面',
      caption: item.caption || item.caption_hint || ''
    }));
  }
  const base = extractKeywords(brief);
  const frames = [
    { title: 'Hook', visual: `${base.primary} 相关冲突现场，多人场景，动态感强`, caption: `先抛问题：${brief.title}` },
    { title: 'Thesis', visual: `${base.primary} 与 ${base.secondary} 的对峙式构图`, caption: `给判断：${brief.core_claim}` },
    { title: 'Mechanism-1', visual: `机制拆解信息图，突出 ${base.primary}`, caption: '第一层机制' },
    { title: 'Mechanism-2', visual: '关键变量图表与群体场景并置', caption: '第二层机制' },
    { title: 'Evidence-1', visual: '数据面板 + 人群/市场/议会现场', caption: '证据 1' },
    { title: 'Evidence-2', visual: '地图/路线/结构图', caption: '证据 2' },
    { title: 'Conflict', visual: '多方拉扯场景，增强对立与张力', caption: '冲突升级' },
    { title: 'Risk', visual: '风险分叉图或情景树', caption: '如果继续演化会怎样' },
    { title: 'Advice', visual: '投资/观察清单卡片', caption: '给建议或观察变量' },
    { title: 'CTA', visual: '回到主问题的封口画面', caption: '结尾收束与 CTA' }
  ];

  if (topicType === 'geopolitics') {
    frames[4].visual = '议会/演讲/军演/港口四宫格场景';
    frames[5].visual = '东亚或中东风险地图，航运线与节点清晰';
  }
  return frames;
}

function extractKeywords(brief) {
  const text = [brief.title, brief.core_claim, ...(brief.angle_candidates || [])].join(' ');
  const mapped = inferSemanticKeywords(text);
  if (mapped) return mapped;
  const tokens = text
    .replace(/[^\u4e00-\u9fa5a-zA-Z0-9\s]/g, ' ')
    .split(/\s+/)
    .filter(Boolean);
  return {
    primary: tokens[0] || '主题',
    secondary: tokens[1] || tokens[0] || '变量'
  };
}

function inferSemanticKeywords(text) {
  const mappings = [
    [/再通胀|通胀/i, { primary: 'reinflation', secondary: 'inflation rates' }],
    [/黄金/i, { primary: 'gold', secondary: 'bullion rates' }],
    [/白银/i, { primary: 'silver', secondary: 'metals market' }],
    [/原油|油价/i, { primary: 'oil', secondary: 'energy market' }],
    [/高市|日本/i, { primary: 'Japan politics', secondary: 'Sanae Takaichi' }],
    [/台海/i, { primary: 'Taiwan Strait', secondary: 'regional security' }],
    [/战争/i, { primary: 'war risk', secondary: 'geopolitics' }],
    [/制裁/i, { primary: 'sanctions', secondary: 'trade security' }],
    [/芯片|算力/i, { primary: 'semiconductor', secondary: 'compute race' }],
    [/ai/i, { primary: 'AI tools', secondary: 'technology industry' }]
  ];
  for (const [pattern, value] of mappings) {
    if (pattern.test(text)) return value;
  }
  return null;
}

function buildEntitySignals(brief) {
  const textChunks = gatherEntityTextChunks(brief);
  const freqMap = buildKeywordFrequency(textChunks);
  const ranked = Array.from(freqMap.entries())
    .map(([term, count]) => ({ term, count }))
    .sort((a, b) => b.count - a.count || b.term.length - a.term.length)
    .slice(0, 120);

  const people = [];
  const countries = [];
  const orgs = [];
  ranked.forEach(item => {
    if (isLikelyPerson(item.term)) people.push({ name: item.term, count: item.count });
    else if (isLikelyCountry(item.term)) countries.push({ name: item.term, count: item.count });
    else if (isLikelyOrg(item.term)) orgs.push({ name: item.term, count: item.count });
  });

  const uniqueByName = rows => {
    const seen = new Set();
    return rows.filter(item => {
      if (seen.has(item.name)) return false;
      seen.add(item.name);
      return true;
    });
  };

  return {
    top_keywords: ranked.slice(0, MATERIAL_LIMITS.entityTopN),
    people: uniqueByName(people).slice(0, MATERIAL_LIMITS.entityTopN),
    countries: uniqueByName(countries).slice(0, MATERIAL_LIMITS.entityTopN),
    orgs: uniqueByName(orgs).slice(0, MATERIAL_LIMITS.entityTopN)
  };
}

function gatherEntityTextChunks(brief) {
  const bag = []
    .concat([brief.title, brief.core_claim])
    .concat(Array.isArray(brief.angle_candidates) ? brief.angle_candidates : [])
    .concat(Array.isArray(brief.proof_requirements) ? brief.proof_requirements : [])
    .concat(Array.isArray(brief.evidence_requirements) ? brief.evidence_requirements : [])
    .concat(Array.isArray(brief.risk_notes) ? brief.risk_notes : []);

  const claims = Array.isArray(brief.claims) ? brief.claims : [];
  claims.forEach(item => {
    if (!item) return;
    bag.push(item.statement || item.title || '');
    bag.push(item.counterpoint || '');
  });

  const listFields = ['evidence_items', 'existing_evidence', 'references', 'sources'];
  listFields.forEach(field => {
    const rows = Array.isArray(brief[field]) ? brief[field] : [];
    rows.forEach(item => {
      if (!item) return;
      if (typeof item === 'string') bag.push(item);
      else bag.push(item.title || item.name || item.note || item.url || '');
    });
  });

  return bag.filter(Boolean).map(v => String(v));
}

function buildKeywordFrequency(chunks) {
  const map = new Map();
  const stopwords = new Set([
    '我们', '你们', '他们', '这个', '那个', '以及', '因为', '所以', '如果', '但是', '一个', '一种',
    'the', 'and', 'for', 'with', 'from', 'that', 'this', 'into', 'about', 'news', 'photo'
  ]);

  const push = token => {
    const clean = String(token || '').trim();
    if (!clean || clean.length < 2) return;
    if (stopwords.has(clean.toLowerCase()) || stopwords.has(clean)) return;
    map.set(clean, (map.get(clean) || 0) + 1);
  };

  chunks.forEach(text => {
    const replaced = text.replace(/[^一-龥A-Za-z0-9.\-_\s]/g, ' ');
    replaced.split(/\s+/).forEach(token => push(token));
    const zhTokens = text.match(/[一-龥]{2,8}/g) || [];
    zhTokens.forEach(token => push(token));
  });

  return map;
}

function isLikelyPerson(term) {
  const personHints = ['特朗普', '拜登', '普京', '泽连斯基', '内塔尼亚胡', '马斯克', '高市早苗', '鲍威尔'];
  if (personHints.includes(term)) return true;
  if (/^[A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,2}$/.test(term)) return true;

  const chinesePersonExclusions = /(政府|市场|公司|集团|机构|媒体|银行|央行|委员会|交易所|指数|通胀|就业|利率|航运|供应链)/;
  if (/^[一-龥]{2,4}$/.test(term) && !chinesePersonExclusions.test(term)) {
    const surnameChars = '赵钱孙李周吴郑王冯陈褚卫蒋沈韩杨朱秦尤许何吕施张孔曹严华金魏陶姜戚谢邹喻柏水窦章云苏潘葛范彭鲁韦昌马苗凤花方俞任袁柳酆鲍史唐费廉岑薛雷贺倪汤滕殷罗毕郝邬安常乐于时傅皮卞齐康伍余元卜顾孟平黄和穆萧尹姚邵湛汪祁毛禹狄米贝明臧计伏成戴谈宋茅庞熊纪舒屈项祝董梁杜阮蓝闵席季麻强贾路娄危江童颜郭梅盛林钟徐邱骆高夏蔡田樊胡凌霍虞万支柯昝管卢莫经房裘缪干解应宗丁宣贲邓郁单杭洪包诸左石崔吉钮龚程嵇邢滑裴陆荣翁荀羊於惠甄曲家封芮羿储靳汲邴糜松井段富巫乌焦巴弓牧隗山谷车侯宓蓬全郗班仰秋仲伊宫宁仇栾暴甘钭厉戎祖武符刘景詹束龙叶幸司韶郜黎蓟薄印宿白怀蒲邰从鄂索咸籍赖卓蔺屠蒙池乔阴郁胥能苍双闻莘党翟谭贡劳逄姬申扶堵冉宰郦雍郤璩桑桂濮牛寿通边扈燕冀郏浦尚农温别庄晏柴瞿阎';
    return surnameChars.includes(term[0]);
  }
  return false;
}

function isLikelyCountry(term) {
  const countryHints = [
    '中国', '美国', '日本', '韩国', '朝鲜', '俄罗斯', '乌克兰', '英国', '法国', '德国', '印度',
    '巴西', '加拿大', '澳大利亚', '欧盟', '东盟', '中东', '欧洲', '东亚', '亚洲', '非洲', '北约'
  ];
  if (countryHints.includes(term)) return true;
  return /^(US|USA|China|Japan|Russia|Ukraine|EU|NATO)$/i.test(term);
}

function isLikelyOrg(term) {
  const orgHints = ['美联储', 'FOMC', 'IMF', 'OPEC', '世行', '世界银行', '财政部', '国务院', '央行'];
  if (orgHints.includes(term)) return true;
  if (/(银行|政府|委员会|集团|公司|大学|研究院|基金|交易所|联储)/.test(term)) return true;
  if (/[部局委院署会盟司厅行社所团校台站府军队]/.test(term) && term.length <= 12) return true;
  return /^[A-Z]{2,8}$/.test(term);
}

function buildNewsScreenshotQueries(brief, topicType, base, entitySignals) {
  const topPeople = entitySignals.people.slice(0, 2).map(item => item.name);
  const topCountries = entitySignals.countries.slice(0, 2).map(item => item.name);
  const topOrgs = entitySignals.orgs.slice(0, 2).map(item => item.name);
  const baseQueries = [];

  if (topicType === 'finance_macro') {
    baseQueries.push('美联储 降息 新闻', 'Federal Reserve rate cut news');
  } else if (topicType === 'geopolitics') {
    baseQueries.push(`${base.primary} 最新局势 新闻`, `${base.primary} policy news`);
  } else {
    baseQueries.push(`${brief.title} 新闻`, `${base.primary} latest news`);
  }

  topPeople.forEach(name => baseQueries.push(`${name} 最新新闻`));
  topCountries.forEach(name => baseQueries.push(`${name} 官方新闻`));
  topOrgs.forEach(name => baseQueries.push(`${name} press release`));

  const dedup = Array.from(new Set(baseQueries.map(item => String(item || '').trim()).filter(Boolean)));
  return dedup.slice(0, MATERIAL_LIMITS.newsScreenshot).map((query, idx) => ({
    query,
    channel: 'news_screenshot',
    priority: 180 - idx
  }));
}

function writeTopicArtifacts(topicRoot, plan) {
  writeJson(path.join(topicRoot, 'config', 'topic_config.json'), plan);
  if (plan.article_source) {
    writeJson(path.join(topicRoot, 'config', 'article_source.json'), plan.article_source);
  }
  if (plan.material_decision_file) {
    writeJson(path.join(topicRoot, 'config', 'material_decision_ref.json'), { material_decision_file: plan.material_decision_file });
  }
  if (plan.article_markdown) {
    fs.writeFileSync(path.join(topicRoot, 'prompts', 'article.md'), `${plan.article_markdown}\n`, 'utf8');
  }
  writeJson(path.join(topicRoot, 'images', 'web_search', 'image_search_queries.json'), plan.web_search.image_queries);
  writeJson(path.join(topicRoot, 'images', 'web_search', 'news_screenshot_queries.json'), plan.web_search.news_screenshot_queries || []);
  writeJson(path.join(topicRoot, 'videos', 'web_search', 'video_search_queries.json'), plan.web_search.video_queries);
  writeJson(path.join(topicRoot, 'videos', 'source_links', 'source_link_candidates.json'), plan.evidence_items.filter(item => item.url));
  writeJson(path.join(topicRoot, 'images', 'generated', 'ai_visual_plan.json'), plan.generated);
  writeJson(path.join(topicRoot, 'layer5', 'layer5_delivery_plan.json'), plan.layer5);
  writeJson(path.join(topicRoot, 'layer5', 'layer5_delivery_inputs.json'), buildLayer5Inputs(plan));
  writeJson(path.join(topicRoot, 'videos', 'scene_plan.json'), plan.scene_plan);
  writeJson(path.join(topicRoot, 'charts', 'config', 'chart_quality_gate.json'), plan.chart_quality_gate || {});
  fs.writeFileSync(
    path.join(topicRoot, 'charts', 'csv', 'chart_anchor_plan.csv'),
    renderChartAnchorCsv(plan.chart_anchors, plan.chart_quality_gate),
    'utf8'
  );
  fs.writeFileSync(path.join(topicRoot, 'prompts', 'material_runbook.md'), renderTopicRunbook(plan), 'utf8');
}

function buildLayer5Inputs(plan) {
  const chartAnchorIds = (plan.chart_anchors || []).map(item => item.anchor_id);
  return {
    meta: {
      object_type: 'Layer5Inputs',
      topic_slug: plan.topic_slug,
      topic_type: plan.topic_type,
      title: plan.title,
      generated_at: nowIso()
    },
    template: {
      template_id: plan.layer5.template_id,
      template_name: plan.layer5.template_name || '',
      narrative_schema: plan.layer5.narrative_schema || 'thesis_then_evidence_then_risks',
      data_granularity: plan.layer5.data_granularity || 'daily',
      layout_hint: plan.layer5.layout_hint || ''
    },
    worldmonitor: {
      thread_id: plan.layer5.thread_id || '019d31c5-bb7f-7a40-a087-9d219e9bd6ab',
      project_root: plan.layer5.worldmonitor_project,
      data_dir: plan.layer5.worldmonitor_data_dir || '',
      public_dir: plan.layer5.worldmonitor_public_dir || '',
      entry: plan.layer5.worldmonitor_entry || 'index.html',
      proxy_port: plan.layer5.proxy_port
    },
    required_assets: {
      chart_anchor_ids: chartAnchorIds,
      chart_csvs: chartAnchorIds.map(anchorId => `charts/csv/${anchorId}.csv`),
      chart_pngs: chartAnchorIds.map(anchorId => `charts/png/${anchorId}.png`),
      scene_plan: 'videos/scene_plan.json',
      source_links: 'videos/source_links/source_link_candidates.json'
    },
    key_metrics_to_emit: plan.layer5.key_metrics_to_emit || [],
    risk_scenarios: plan.layer5.risk_scenarios || [],
    preferred_components: plan.layer5.preferred_components || [],
    page_modules: plan.layer5.page_modules || []
  };
}

function renderChartAnchorCsv(chartAnchors, chartQualityGate = {}) {
  const fallbackRule = chartQualityGate?.fallback?.trigger_rule || '';
  const fallbackOutputs = (chartQualityGate?.fallback?.outputs || []).join(' | ');
  const lines = ['anchor_id,title,purpose,chart_type,data_sources,fallback_rule,fallback_outputs'];
  chartAnchors.forEach(item => {
    lines.push([
      csvEscape(item.anchor_id),
      csvEscape(item.title),
      csvEscape(item.purpose),
      csvEscape(item.chart_type),
      csvEscape((item.data_sources || []).join(' | ')),
      csvEscape(fallbackRule),
      csvEscape(fallbackOutputs)
    ].join(','));
  });
  return `${lines.join('\n')}\n`;
}

function csvEscape(value) {
  const text = String(value ?? '');
  if (/[",\n]/.test(text)) {
    return `"${text.replace(/"/g, '""')}"`;
  }
  return text;
}

function renderTopicRunbook(plan) {
  return [
    `# ${plan.title} 素材执行手册`,
    '',
    `- 主题类型：\`${plan.topic_type}\``,
    `- 生成依据：\`${plan.generation_basis || 'reasoning_sheet'}\``,
    `- Layer 5 模板：\`${plan.layer5.template_id}\``,
    '',
    '## 先做什么',
    '',
    '1. 先按 `charts/csv/chart_anchor_plan.csv` + `charts/config/chart_quality_gate.json` 执行图表质量门控。',
    '   - 阈值：CV>=0.03、|slope|>=0.005、R²>=0.25、trend_strength>=0.30。',
    '   - 未达阈值时不生成图表 PNG，改输出逻辑关系表：`charts/csv/*.csv` + `charts/markdown/*.md`。',
    '2. 再跑 `images/web_search` 与 `videos/web_search` 的下载，并检查 `videos/web_search/video_quality_audit_report.json`。',
    '3. 关注 pack 根目录自动生成的 `video_quality_regression_report.json` / `video_quality_regression_report.md` 汇总。',
    `4. AI 图像至少补齐连环画 ${plan.generated.comic_storyboard.length} 张，梗图 ${plan.generated.meme_prompts.length} 张，搞笑人物 ${(plan.generated.funny_comic_character_prompts || []).length} 张。`,
    '5. 需要交互稿时，再按 `layer5/layer5_delivery_plan.json` 接入 worldmonitor。',
    '',
    '## 视频质检规则',
    '',
    '- 分辨率门槛：关闭（按来源可追溯、时长、帧变化筛选）。',
    '- 来源放宽：允许新闻直播 / 访谈素材。',
    '- 来源拦截：过滤口播自媒体出镜内容。',
    '- 防拼接：启用“文件来源 + 时长 + 帧变化”三重检查，拦截截图拼视频。',
    '',
    '## 推荐技能',
    '',
    '- `media-downloader`：下载图片与视频。',
    '- `baoyu-infographic`：生成信息图。',
    '- `baoyu-imagine` / `ai-image-generation`：生成封面、连环画、梗图。',
    '- `remotion-best-practices`：把 scene_plan 做成视频。',
    '- `worldmonitor`：作为 Layer 5 交互交付页母体。',
    '',
    '## 执行命令',
    '',
    `- 推荐主链命令：\`/Volumes/PSSD/Projects/公众号文章/scripts/material_execute_pack.sh --draft-manifest ${draftManifestForRunbook()} --topic-dir ${plan.topic_slug} --steps charts,image_search,video_search,ai_prep\``,
    `- 正式命令：\`python3 /Volumes/PSSD/Projects/公众号文章/scripts/material_execute_pack.py --draft-manifest <draft_manifest.json>\``,
    ''
  ].join('\n');
}

function draftManifestForRunbook() {
  return '/path/to/draft_manifest.json';
}

function buildImageMaterials(plan) {
  const generated = [
    bindAsset(plan, 0, 'image', {
      title: '封面图',
      asset_type: 'image',
      source_type: 'ai_generated',
      file: 'images/generated/ai_visual_plan.json',
      purpose: '主封面'
    })
  ];
  plan.generated.infographic_prompts.forEach((prompt, index) => {
    generated.push(bindAsset(plan, index, 'infographic', {
      title: `信息图 ${index + 1}`,
      asset_type: 'image',
      source_type: 'infographic_prompt',
      prompt,
      file: 'images/generated/ai_visual_plan.json'
    }));
  });
  plan.generated.comic_storyboard.forEach(frame => {
    generated.push(bindAsset(plan, generated.length, 'comic', {
      title: frame.title,
      asset_type: 'image',
      source_type: 'comic_frame',
      prompt: frame.visual_prompt,
      file: 'images/generated/ai_visual_plan.json'
    }));
  });
  plan.generated.meme_prompts.forEach((prompt, index) => {
    generated.push(bindAsset(plan, generated.length + index, 'meme', {
      title: `梗图 ${index + 1}`,
      asset_type: 'image',
      source_type: 'meme_prompt',
      prompt,
      file: 'images/generated/ai_visual_plan.json'
    }));
  });
  (plan.generated.funny_comic_character_prompts || []).forEach((prompt, index) => {
    generated.push(bindAsset(plan, generated.length + index, 'comic_character', {
      title: `搞笑漫画人物 ${index + 1}`,
      asset_type: 'image',
      source_type: 'funny_comic_character_prompt',
      prompt,
      file: 'images/generated/ai_visual_plan.json'
    }));
  });

  return generated.concat(
    plan.web_search.image_queries.map((queryItem, index) => bindAsset(plan, index, 'image', {
      title: `图片检索 ${index + 1}`,
      asset_type: 'image',
      source_type: 'web_search',
      query: typeof queryItem === 'string' ? queryItem : queryItem.query,
      file: 'images/web_search/image_search_queries.json'
    })).concat((plan.web_search.news_screenshot_queries || []).map((queryItem, index) => bindAsset(plan, index, 'news_screenshot', {
      title: `新闻截图检索 ${index + 1}`,
      asset_type: 'image',
      source_type: 'news_screenshot',
      query: typeof queryItem === 'string' ? queryItem : queryItem.query,
      file: 'images/web_search/news_screenshot_queries.json'
    })))
  );
}

function buildVideoMaterials(plan) {
  const sources = plan.evidence_items
    .filter(item => item.url)
    .slice(0, 6)
    .map((item, index) => bindAsset(plan, index, 'video', {
      title: item.title,
      asset_type: 'video',
      source_type: 'provided_link',
      url: item.url,
      source: item.source
    }));
  const searches = plan.web_search.video_queries.map((query, index) => bindAsset(plan, index, 'video_search', {
    title: `视频检索 ${index + 1}`,
    asset_type: 'video',
    source_type: 'web_search',
    query,
    file: 'videos/web_search/video_search_queries.json'
  }));
  return sources.concat(searches);
}

function buildQuoteMaterials(brief) {
  return [
    { text: brief.core_claim, source: 'brief.core_claim' },
    ...(brief.risk_notes || []).slice(0, 2).map((text, index) => ({
      text,
      source: `brief.risk_notes.${index}`
    }))
  ];
}

function buildDataPointMaterials(plan) {
  return plan.chart_anchors.map((item, index) => bindAsset(plan, index, 'chart', {
    asset_type: 'chart',
    label: item.title,
    title: item.title,
    value: item.chart_type,
    data_sources: item.data_sources,
    purpose: item.purpose
  }));
}

function buildReferenceMaterials(plan) {
  const fromLinks = plan.evidence_items.map((item, index) => ({
    evidence_id: item.id || item.evidence_id || `reference-${index + 1}`,
    claim_id: bindAsset(plan, index, 'reference').claim_id,
    title: item.title,
    url: item.url,
    source_type: item.source || 'brief',
    source_tier: item.source_tier || null,
    evidence_type: 'article_link',
    platform: item.platform || '',
    note: item.note || ''
  }));
  const requirements = plan.recommended_sources.map((item, index) => ({
    evidence_id: `source-hint-${index + 1}`,
    claim_id: bindAsset(plan, index, 'reference').claim_id,
    title: `source_hint_${index + 1}`,
    note: item,
    source_type: 'recommended_source',
    evidence_type: 'source_hint'
  }));
  return fromLinks.concat(requirements);
}

function buildGaps(brief, plan) {
  const gaps = []
    .concat(brief.risk_notes || [])
    .concat([
      '图表位已规划，但仍需在下一轮用 akshare / tushare / 官方数据补齐真实序列。',
      '视频检索词已生成：允许新闻直播/访谈，但需持续拦截口播自媒体与截图拼视频素材。'
    ]);
  if (plan.evidence_items.filter(item => item.url).length < 3) {
    gaps.push('原始链接型证据不足 3 条，需在 material 执行阶段继续补证据源。');
  }
  return Array.from(new Set(gaps));
}

function renderMaterialPackMarkdown(runId, upstream, materialPacks, packRoot) {
  const lines = [
    '# 第04环节 Material Pack',
    '',
    `运行批次：\`${runId}\``,
    `上游对象：\`${upstream.upstreamType}\``,
    `上游入口：\`${upstream.upstreamFile}\``,
    `素材包根目录：\`${packRoot}\``,
    '',
    '## 本轮标准',
    '',
    '- Material 优先消费 `ReasoningSheet`；若未提供，则向后兼容旧 `ContentBrief`。',
    '- 每个话题默认补：图表锚点、图片检索词、新闻截图检索词、视频检索词、AI 图像计划、Layer 5 交互交付计划。',
    '- AI 图像默认包含：封面、信息图、连环画、梗图、搞笑漫画人物。',
    '- 视频素材默认分两路：素材库原始链接 + 外网检索下载线索。',
    '- 视频质检默认：不设分辨率硬门槛，允许新闻直播/访谈，过滤口播自媒体，拦截截图拼视频。',
    '',
    '## 话题清单',
    ''
  ];

  materialPacks.forEach((pack, index) => {
    lines.push(`### 题目 ${index + 1}：${pack.title}`);
    lines.push('');
    lines.push(`- 主题类型：\`${pack.topic_type}\``);
    lines.push(`- 素材目录：\`${pack.asset_root}\``);
    lines.push(`- Layer 5 模板：\`${pack.layer5_delivery.template_id}\``);
    lines.push(`- Claim 绑定：${pack.claim_bindings.length} 条`);
    lines.push(`- 图表锚点：${pack.materials.data_points.length} 个`);
    lines.push(`- 图片计划：${pack.materials.images.length} 项`);
    lines.push(`- 视频计划：${pack.materials.videos.length} 项`);
    lines.push(`- 主要缺口：${pack.gaps[0] || '无'}`);
    lines.push('');
  });

  return `${lines.join('\n')}\n`;
}

function renderMaterialReportMarkdown(runId, materialPacks, packRoot) {
  const financeCount = materialPacks.filter(item => item.topic_type === 'finance_macro').length;
  const geoCount = materialPacks.filter(item => item.topic_type === 'geopolitics').length;
  const layer5Topics = materialPacks.filter(item => item.layer5_delivery?.template_id).length;
  const totalComic = materialPacks.reduce((sum, item) => sum + (item.generated_visuals?.comic_storyboard?.length || 0), 0);
  const qualityPolicyTopics = materialPacks.filter(item => item.video_quality_policy).length;

  return [
    '# 第04环节 Material 报告',
    '',
    `运行批次：\`${runId}\``,
    `素材包根目录：\`${packRoot}\``,
    '',
    '## 完成情况',
    '',
    `- 主题数：${materialPacks.length}`,
    `- 宏观财经题：${financeCount}`,
    `- 地缘时政题：${geoCount}`,
    `- 已生成 Layer 5 方案题目：${layer5Topics}`,
    `- 已生成连环画分镜：${totalComic} 张`,
    `- 已写入视频质检策略：${qualityPolicyTopics} 题`,
    `- AI 全文判材：${materialPacks.filter(item => item.coverage_notes.some(note => note.includes('final_doc_ai_reading'))).length} 题`,
    '',
    '## 当前判断',
    '',
    '- 旧版 `material` 仅能输出占位字段，已升级为“结构化资产包生成器”。',
    '- 这一轮先把下载与生成的执行计划全部落盘，后续可直接接 `media-downloader`、`baoyu`、`remotion`、`worldmonitor` 执行。',
    '- `8787` 对应的交互交付层确认应复用 `/Volumes/PSSD/Projects/worldmonitor`，但当前本机服务未启动，因此本轮只固化接线方案，不强行跑服务。',
    '- 视频筛选改为“新闻直播/访谈可保留 + 口播自媒体拦截 + 截图拼视频审计”，并要求输出质量审计报告。',
    '',
    '## 建议的下游动作',
    '',
    '1. 先补真实图表与 CSV。',
    '2. 再下载视频与图片，并按 scene_plan 做筛选。',
    '3. 然后批量生成封面 / 信息图 / 连环画 / 梗图。',
    '4. 如需专题页，再触发 Layer 5 增强交付分支。',
    ''
  ].join('\n');
}

function buildStageManifest(runId, upstream, materialPacks, packRoot) {
  return {
    run_id: runId,
    stage: 'material',
    upstream_type: upstream.upstreamType,
    upstream_entry: upstream.upstreamFile,
    upstream_files: upstream.upstreamFiles,
    pack_root: packRoot,
    generation_basis: 'final_doc_ai_reading',
    selected_topics: materialPacks.map(item => item.title),
    topic_types: materialPacks.map(item => ({
      topic_id: item.topic_id,
      topic_type: item.topic_type,
      layer5_template: item.layer5_delivery.template_id,
      video_quality_policy: item.video_quality_policy,
      claim_bindings: item.claim_bindings.length
    })),
    asset_counts: materialPacks.map(item => ({
      topic_id: item.topic_id,
      image_items: item.materials.images.length,
      video_items: item.materials.videos.length,
      chart_items: item.materials.data_points.length,
      reference_items: item.materials.references.length
    })),
    asset_binding_contract: ['claim_id', 'section_id', 'usage_type', 'relevance_score', 'editor_status'],
    quality_audit_expected_fields: [
      'source_category',
      'source_ok',
      'resolution_height',
      'duration_seconds',
      'scene_changes',
      'scene_change_rate',
      'anti_screenshot_montage_pass',
      'final_pass',
      'fail_reasons'
    ],
    status: 'ready_for_material_execution'
  };
}

if (require.main === module) {
  const contentBriefsFile = process.argv[2];
  supplementMaterial(contentBriefsFile).then(() => process.exit(0)).catch(() => process.exit(1));
}

module.exports = { supplementMaterial, buildMaterialPack };
