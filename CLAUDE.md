# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a suite of OpenClaw/Codex Skills for daily media content production teams. It implements a fixed 7-stage workflow from content intake to post-publication review, designed for multi-person collaboration with Feishu integration.

**Fixed workflow chain**: `intake -> brief -> draft -> material -> rewrite -> publish -> postmortem`

## Architecture

### Skill Structure

The repository contains 6 skills organized under `skills/`:

1. **dasheng-sop-orchestrator** - Entry point and stage router. Enforces stage order, prevents stage skipping, and routes to appropriate stage skills.

2. **dasheng-stage-intake-brief-draft** - Handles the first 3 stages: content intake, topic briefing (8-10 candidates), and standard draft generation (factual, no platform styling).

3. **dasheng-stage-material-refill** - Generates and refills assets (charts, images, videos) into editor-confirmed final documents.

4. **dasheng-stage-rewrite** - Produces 4 platform-specific rewrites per topic with strict word count validation:
   - WeChat + luxun + hot (≥4000 words)
   - WeChat + lemon + normal (≥4000 words)
   - XHS video + luxun + hot (≥1800 words)
   - XHS video + lemon + normal (≥1800 words)
   - Supports personal style DNA injection and 7 writing frameworks with 4 content enhancement strategies

5. **dasheng-stage-publish-video** - Pre-publish video enhancement: generates interactive chart videos and motion narrative videos using finance-motion-8787 engine.

6. **dasheng-style-profiler** - Extracts personal writing style DNA from historical articles using 14-dimensional analysis framework. Generates reusable style profiles for personalized rewrites.

### Critical Constraints

- **Stage order is immutable** - never skip stages or produce downstream deliverables prematurely
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

Always enter through `dasheng-sop-orchestrator` to prevent stage misalignment. The orchestrator will route to the appropriate stage skill based on current progress.

### Stage Deliverables

Each stage must produce:
- **intake**: `intake_manifest.json`
- **brief**: `brief_manifest.json`
- **draft**: `draft_manifest.json`
- **material**: `material_manifest.json`, `05_MaterialPack.md`, `05_Material_报告.md`
- **rewrite**: `rewrite_manifest.json`, per-topic `meta.json`, `<topic>__rewrite_bundle.md`
- **publish**: `publish_manifest.json`, `publish_video_supplement_manifest.json`, video files in `videos/interactive_charts/` and `videos/motion_narrative/`
- **postmortem**: `postmortem_manifest.json`

## Key Commands

### Intake/Brief/Draft
```bash
cd "${DASHENG_WORKSPACE}"
python3 scripts/run_stage1_intake.py
```

### Material Generation
```bash
cd "${DASHENG_WORKSPACE}"
python3 scripts/material_execute_pack.py --pack-root "<topic_pack_root>" --steps charts,image_search,video_search,ai_prep

# Parallel execution
python3 scripts/material_parallel_launcher.py --pack-root "<pack_root>"
```

### Style DNA Extraction (Optional, before first rewrite)
```bash
# Extract personal writing style from historical articles
# Requires 3-10 sample articles in ${DASHENG_WORKSPACE}/风格参考/{作者}/
# Generates style profile with 14-dimensional analysis
```

### Rewrite
```bash
cd "${DASHENG_WORKSPACE}"

# Using preset DNA (default: luxun/lemon)
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
python3 scripts/publish_video_supplement.py
```

## Version Management

- Naming convention: `dasheng-media-workflow-skills-YYYYMMDD-vX`
- Multiple iterations on same day: increment v1, v2, v3
- Never overwrite historical packages to ensure rollback capability

## Important References

- Stage contract specification: [skills/dasheng-sop-orchestrator/references/stage-contract.md](skills/dasheng-sop-orchestrator/references/stage-contract.md)
- Writing frameworks: [skills/dasheng-stage-rewrite/references/frameworks.md](skills/dasheng-stage-rewrite/references/frameworks.md)
- Content enhancement strategies: [skills/dasheng-stage-rewrite/references/content-enhance.md](skills/dasheng-stage-rewrite/references/content-enhance.md)
- 14-dimensional style analysis: [skills/dasheng-style-profiler/references/style-14d-framework.md](skills/dasheng-style-profiler/references/style-14d-framework.md)
- Smoke test prompts: [SMOKE_PROMPTS.md](SMOKE_PROMPTS.md)
- Export manifest: [EXPORT_MANIFEST.md](EXPORT_MANIFEST.md)
- Optimization analysis: [OPTIMIZATION_ANALYSIS.md](OPTIMIZATION_ANALYSIS.md)
