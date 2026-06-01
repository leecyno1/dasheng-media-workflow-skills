# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a suite of OpenClaw/Codex Skills for daily media content production teams. It implements a fixed 7-stage workflow from content intake to post-publication review, designed for multi-person collaboration with Feishu integration.

**Fixed workflow chain**: `intake -> brief -> draft -> material -> rewrite -> publish -> postmortem`

**Optional pre-work asset**: `paradigm-learning` / `dasheng-paradigm-profiler`. It produces `ParadigmProfile` artifacts before Brief when users provide standard articles, templates, successful samples, or channel examples. It is not a formal stage and must not be treated as a required gate.

## Architecture

### Skill Structure

The only formal orchestration entry is **dasheng-media-sop**. Legacy entrypoints may still exist for compatibility, but new work should enter through the canonical runner and stage contracts.

Current formal skill set exported by `scripts/export_skill_suite.py`:

1. **dasheng-media-sop** - The single workflow controller and stage router.
2. **dasheng-paradigm-profiler** - Optional pre-work asset builder for article paradigms and channel frameworks.
3. **dasheng-daily-intake** - Content intake and source aggregation.
4. **dasheng-daily-phase2** - AI-only topic brief generation and topic card production.
5. **dasheng-daily-material** - Material gathering, chart gating, image/video search, and asset reports.
6. **dasheng-stage-publish** - Publish orchestration, video supplement, channel adaptation, channel execution, and publish verification.
7. **dasheng-daily-postmortem** - Post-publication review and knowledge writeback.
8. **dasheng-style-profiler** - Personal writing Style DNA extraction using the 14-dimensional style framework.
9. **feishu-doc-creator** - Feishu document creation support.

### Critical Constraints

- **Stage order is immutable** - never skip stages or produce downstream deliverables prematurely
- **ParadigmProfile is optional** - it can inform Brief/Draft/Rewrite/Publish, but it is not a formal stage gate
- **Per-topic isolation** - each topic must have its own directory; never mix content from different topics
- **Manifest requirement** - every stage must produce both a document and a manifest JSON file
- **Inheritance rule** - rewrite stage must inherit the final structure from the draft, not force a fixed three-part structure

### Writing Enhancement System

The rewrite stage now supports advanced writing capabilities:

**Writing Frameworks** (7 types):
- Painpoint (痛点型): Problem-solution structure for how-to content
- Story (故事型): Narrative structure for people/events/trends
- Checklist (清单型): List-based structure for recommendations
- Comparison (对比型): A vs B analysis structure
- Hot-topic (热点解读型): Current events commentary
- Opinion (纯观点型): Strong stance with solid arguments
- Retrospective (复盘型): Post-event analysis and lessons

**Content Enhancement Strategies** (4 types):
- Angle Discovery (角度发现): Find unique perspectives for hot-topic/opinion pieces
- Density Boost (密度强化): Add actionable details for painpoint/checklist pieces
- Detail Anchoring (细节锚定): Use real details for story/retrospective pieces
- Real Experience (真实体感): Use authentic user voices for comparison pieces

**Style DNA System**:
- Preset DNA: luxun (sharp, data-driven) and lemon (warm, narrative)
- Personal DNA: Extract from 10+ historical articles using 14-dimensional analysis
- Includes: paragraph recipes, narrative systems, content progression patterns, punctuation preferences

**ParadigmProfile System**:
- ParadigmProfile controls structure, narrative path, argument model, information density, and channel framework
- Style DNA controls voice, vocabulary, sentence rhythm, and author expression
- Sample facts, unverified data, and original sentences must never be reused as article evidence

**⭐ NEW: Framework & Strategy Integration**:
- Brief stage recommends framework and strategy for each topic
- Draft stage generates content following the recommended framework
- Rewrite stage fully applies framework structure and enhancement strategy
- Intelligent content expansion based on topic context (no more hardcoded blocks)

## Environment Setup

1. Copy environment template:
```bash
cp ENV_TEMPLATE.env ~/.openclaw/dasheng.env
```

2. Fill in required credentials and paths in `~/.openclaw/dasheng.env`:
   - `DASHENG_WORKSPACE` - main workspace path
   - `FINANCE_MOTION_WORKSPACE` - video generation workspace
   - `DASHENG_OUTPUT_ROOT` - daily output directory
   - `DASHENG_FEISHU_ROOT_URL` - Feishu shared folder URL
   - `DASHENG_FEISHU_CHAT_ID` - Feishu group chat ID
   - `FEISHU_APP_ID` / `FEISHU_APP_SECRET` - Feishu app credentials
   - `TUSHARE_TOKEN` - data API token
   - Image generation provider keys (QHAIGC, MOLI, VECTOR, MINIMAX)

3. Load environment before running:
```bash
set -a; source ~/.openclaw/dasheng.env; set +a
```

## Installation

Install skills to OpenClaw:
```bash
# Default installation to ~/.openclaw/skills
bash install_to_openclaw.sh

# Custom installation path
bash install_to_openclaw.sh /your/openclaw/skills
```

## Daily Workflow

### Mandatory Pre-Run Check

Before running any production tasks each day, execute the smoke test from `SMOKE_PROMPTS.md`:
- Verifies paths are accessible
- Confirms credentials are valid
- Checks all stage delivery interfaces
- Validates publish video pipeline
- Outputs results to `smoke_report.md`

### Stage Execution

Always enter through `dasheng-media-sop` to prevent stage misalignment. The media SOP will route to the appropriate stage skill based on current progress.

### Stage Deliverables

Each stage must produce:
- **paradigm-learning (optional)**: `00_范式画像.md`, `paradigm_profile.yaml`, `paradigm_prompt_block.md`, `paradigm_manifest.json`
- **intake**: `intake_manifest.json`
- **brief**: `brief_manifest.json`
- **draft**: `draft_manifest.json`
- **material**: `material_manifest.json`, `05_MaterialPack.md`, `05_Material_报告.md`
- **rewrite**: `rewrite_manifest.json` (with platform_metadata for all 8 variants), per-topic `meta.json`, `<topic>__rewrite_bundle.md`
- **publish**: `publish_manifest.json`, `publish_video_supplement_manifest.json`, `channel_adaptation_manifest.json`, `channel_execution_manifest.json`, `publish_verification_report.json`, video files in `videos/interactive_charts/` and `videos/motion_narrative/`
- **postmortem**: `postmortem_manifest.json`

## Key Commands

### Intake
```bash
cd "${DASHENG_WORKSPACE}"
python3 scripts/run_stage1_intake.py
```

### Brief (AI-driven, recommended)
```bash
# Use dasheng-stage-brief-ai skill for natural language titles
# Generates topics with clear arguments and framework recommendations
# Output: 产物/02_Brief/{run_id}_ai/
```

### Draft (Framework-driven, recommended)
```bash
cd "${DASHENG_WORKSPACE}"
python3 scripts/draft_with_framework.py \
  --brief-dir "产物/02_Brief/{run_id}_ai" \
  --output-dir "产物/03_Draft/{run_id}"

# Generates structured drafts following recommended frameworks
# Applies content enhancement strategies
# Validates quality (word count, structure, citations)
```

### Material Generation (AI-optimized, 2026-04-06 enhanced)
```bash
cd "${DASHENG_WORKSPACE}"

# Standard material generation with AI optimization
python3 scripts/material_execute_pack.py \
  --pack-root "<topic_pack_root>" \
  --steps charts,image_search,video_search,ai_prep

# AI features:
# - Intelligent chart gating (decides which data needs visualization)
# - Optimized search keywords (improves hit rate)
# - Quality reports

# Parallel execution
python3 scripts/material_parallel_launcher.py --pack-root "<pack_root>"
```

**2026-04-06 优化**：
- ✅ **扁平化文件结构**：所有素材在单层目录，无多级子目录
- ✅ **描述性命名**：图表_、图片_、视频_ 中文前缀，便于编辑人员查找
- ✅ **视频自动下载**：默认每个查询下载 3 个视频，无需手动指定参数
- 详见：[MATERIAL_FLAT_STRUCTURE_IMPLEMENTATION.md](docs/MATERIAL_FLAT_STRUCTURE_IMPLEMENTATION.md)

### Style DNA Extraction (Optional, before first rewrite)
```bash
# Extract personal writing style from historical articles
# Requires 3-10 sample articles in ${DASHENG_WORKSPACE}/风格参考/{作者}/
# Generates style profile with 14-dimensional analysis
```

### Paradigm Learning (Optional, before Brief)
```bash
cd "${DASHENG_WORKSPACE}"
python3 scripts/run_mainline_stage.py paradigm sample.md \
  --run-id "$(date +%F_%H%M%S)" \
  --profile-name 结构变化解读 \
  --scenario 行业解读 \
  --channel 公众号
```

### Rewrite
```bash
cd "${DASHENG_WORKSPACE}"

# Using preset DNA (default: luxun/lemon)
# Generates 8 variants with platform metadata
python3 scripts/rewrite_rerun_with_final_structure.py

# Using personal style DNA (after running dasheng-style-profiler)
python3 scripts/rewrite_with_personal_dna.py --dna-path "${DASHENG_WORKSPACE}/风格库/{作者}/风格画像.md"

# Push to Feishu
node scripts/feishu_rewrite_push.js "$(date +%F)"

# Learn from manual edits (optional, for continuous improvement)
python3 scripts/learn_edits_from_feishu.py --date "$(date +%F)"
```

### Publish Video Supplement
```bash
cd "${DASHENG_WORKSPACE}"

# With style selection (5 templates available)
python3 scripts/publish_video_supplement.py --style claude-purple
# Available styles: claude-purple, cyberpunk, finance-business, medical-lancet, anime-light
```
```

## Version Management

- Naming convention: `dasheng-media-workflow-skills-YYYYMMDD-vX`
- Multiple iterations on same day: increment v1, v2, v3
- Never overwrite historical packages to ensure rollback capability

## Important References

- Stage contract specification: [skills/dasheng-media-sop/references/stage-contract.md](skills/dasheng-media-sop/references/stage-contract.md)
- **⭐ Brief AI generation guide**: [skills/dasheng-stage-brief-ai/references/ai-generation-guide.md](skills/dasheng-stage-brief-ai/references/ai-generation-guide.md)
- **⭐ Topic evaluation framework**: [skills/dasheng-stage-brief-ai/references/topic-evaluation.md](skills/dasheng-stage-brief-ai/references/topic-evaluation.md)
- Writing frameworks: [skills/dasheng-stage-rewrite/references/frameworks.md](skills/dasheng-stage-rewrite/references/frameworks.md)
- Content enhancement strategies: [skills/dasheng-stage-rewrite/references/content-enhance.md](skills/dasheng-stage-rewrite/references/content-enhance.md)
- **⭐ Platform metadata rules**: [skills/dasheng-stage-rewrite/references/platform-metadata.md](skills/dasheng-stage-rewrite/references/platform-metadata.md)
- 14-dimensional style analysis: [skills/dasheng-style-profiler/references/style-14d-framework.md](skills/dasheng-style-profiler/references/style-14d-framework.md)
- **⭐ Video template styles**: [skills/dasheng-stage-publish-video/references/template-styles.md](skills/dasheng-stage-publish-video/references/template-styles.md)
- **Paradigm profiler**: [skills/dasheng-paradigm-profiler/SKILL.md](skills/dasheng-paradigm-profiler/SKILL.md)
- **Publish architecture**: [skills/dasheng-media-sop/references/publish-architecture.md](skills/dasheng-media-sop/references/publish-architecture.md)
- **Publish skill matrix**: [skills/dasheng-media-sop/references/publish-skill-matrix.md](skills/dasheng-media-sop/references/publish-skill-matrix.md)
- **⭐ Motion integration guide**: [docs/MOTION_INTEGRATION_GUIDE.md](docs/MOTION_INTEGRATION_GUIDE.md)
- Smoke test prompts: [SMOKE_PROMPTS.md](SMOKE_PROMPTS.md)
- Export manifest: [EXPORT_MANIFEST.md](EXPORT_MANIFEST.md)
- Optimization analysis: [OPTIMIZATION_ANALYSIS.md](OPTIMIZATION_ANALYSIS.md)
- **⭐ Brief AI test report**: [BRIEF_AI_TEST_REPORT.md](BRIEF_AI_TEST_REPORT.md)
- **⭐ Brief AI comparison**: [BRIEF_AI_COMPARISON.md](BRIEF_AI_COMPARISON.md)
- **⭐ Phase 2 upgrade summary**: [PHASE2_UPGRADE_SUMMARY.md](PHASE2_UPGRADE_SUMMARY.md)
- **⭐ ClawHub skills installation**: [docs/CLAWHUB_SKILLS_INSTALLATION.md](docs/CLAWHUB_SKILLS_INSTALLATION.md)
- **⭐ MCP services comparison**: [docs/MCP_SERVICES_COMPARISON.md](docs/MCP_SERVICES_COMPARISON.md)
- **⭐ Integration summary**: [docs/INTEGRATION_SUMMARY.md](docs/INTEGRATION_SUMMARY.md)
- **⭐ Video generation complete**: [VIDEO_GENERATION_COMPLETE.md](VIDEO_GENERATION_COMPLETE.md)
- **⭐ Xiaohongshu publish integration**: [docs/XIAOHONGSHU_PUBLISH_INTEGRATION.md](docs/XIAOHONGSHU_PUBLISH_INTEGRATION.md)

## Recent Upgrades

### Phase 1: Brief AI-ification (Completed)
- Replaced hardcoded template system with AI reasoning
- Natural language titles instead of "对象A、对象B：固定句式"
- Clear arguments with evidence needs
- Framework and strategy recommendations
- 5-dimension evaluation system

**Problem solved**: "题目特别硬，逻辑关系像生搬硬套" → Natural, insightful titles

### Phase 2: Draft & Material Optimization (Completed)
- Framework-driven draft generation
- AI-powered chart gating (reduces unnecessary charts by 30-50%)
- AI-optimized search keywords (improves hit rate by 50-100%)
- Quality validation and reporting
- Seamless Brief → Draft → Material workflow

**Key improvement**: End-to-end AI-driven workflow from topic generation to material preparation

### Phase 3: Platform Adaptation & Motion Templates (Completed - 2026-04-06)
- **Rewrite Enhancement**: Expanded from 4 to 8 variants per topic
  - Added Bilibili and WeChat Channels support
  - Platform-specific metadata generation (titles, hashtags, descriptions, captions)
  - Metadata embedded in rewrite_manifest.json
- **Motion Templates**: 5 standard video style templates
  - Claude Purple, Cyberpunk, Finance Business, Medical Lancet, Anime Light
  - Integration between Finance Motion 8787 (preview) and Remotion (rendering)
  - Conversion script for seamless workflow
- **Publish Enhancement**: Platform distribution is now part of publish
  - Added Bilibili and WeChat Channels
  - Reads metadata from rewrite stage (no more temporary generation)
  - `distribute` is no longer a standalone formal stage
- **Video Generation**: Successfully generated motion narrative videos
  - Created 2 Remotion components (AIMergersXhs, ChinaPlanXhs) from rewrite content
  - Rendered high-quality videos (1080x1920, 25s, Claude Purple style)
  - Render scripts for automated video generation
  - See [VIDEO_GENERATION_COMPLETE.md](VIDEO_GENERATION_COMPLETE.md) for details
- **Material Stage Optimization**: Flat structure and auto-download
  - Flat single-level directory structure (no subdirectories)
  - Descriptive Chinese-prefixed naming (图表_, 图片_, 视频_)
  - Video auto-download (default 3 per query)
  - See [MATERIAL_FLAT_STRUCTURE_IMPLEMENTATION.md](docs/MATERIAL_FLAT_STRUCTURE_IMPLEMENTATION.md) for details

**Key improvements**: 
- Complete platform adaptation with metadata generation
- Professional video template system with 5 styles
- Seamless Finance Motion → Remotion workflow
- Automated video generation from rewrite content
- Editor-friendly material organization with flat structure and descriptive naming
