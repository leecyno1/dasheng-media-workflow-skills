# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A suite of OpenClaw/Codex skills that drive a daily self-media production workflow for a Chinese-language content team. The pipeline is fixed, manifest-driven, and integrated with Feishu for HITL review across multiple operators.

**Canonical chain (6 stages)**:
`intake -> brief -> draft -> transwrite -> publish -> postmortem`

**Optional pre-work asset**: `paradigm-learning` (skill `dasheng-paradigm-profiler`). Produces a `ParadigmProfile` from sample articles/templates and feeds Brief/Draft/Transwrite/Publish. It is NOT a formal gate.

> ⚠️ The chain was previously documented as 7 stages with separate `material` and `rewrite`. As of commit `3b0e9c2` (`chore: remove material stage`), material has been absorbed into Draft (data/charts/HTML embedding live there), and rewrite has been renamed and reshaped into `transwrite` (3 channel outputs: WeChat article / talking-head video / podcast). Do not regenerate the old layout.

### Tooling history

This repo was originally developed against **OpenAI Codex CLI** and later migrated to **Claude Code**. Residual Codex artifacts you may encounter:

- `.codex_work/` — empty session scratch dir, safe to ignore.
- `skills/*/agents/openai.yaml` — empty stub files from the Codex agent convention (`skills/dasheng-media-sop/agents/`, `dasheng-stage-brief-ai/agents/`, `dasheng-style-profiler/agents/`, `jiebang/agents/`). Not consumed by the current runtime.
- `skills/.archive/` — deprecated Codex-era skill directories kept for reference (`dasheng-sop-orchestrator`, `dasheng-stage-intake-brief-draft`, `dasheng-stage-publish-video`, `dasheng-stage-rewrite`). Mapped to current names in `skills/SKILL_ALIASES.md`.
- No `AGENTS.md` exists; **this `CLAUDE.md` is the single agent guide**. If a Codex run is ever revived, mirror this file to `AGENTS.md` rather than maintaining two sources of truth.

## Architecture

### Canonical entry points

- **Unified CLI (preferred)**: `scripts/run_mainline_stage.py <stage>` — single subcommand dispatcher that resolves inputs from the previous stage's manifest, validates gates, and shells out to the per-stage builder. Subcommands: `intake | paradigm | brief | draft | transwrite | publish | postmortem | doctor`.
- **Diagnostics**: `scripts/workflow_doctor.py --latest` — verifies environment, paths, credentials, and stage contract compliance. Run this any time the workflow gets wedged.
- **Per-stage builders** (do not call directly unless you know what you're doing): `run_stage1_intake.py`, `phase2_rebuilder.py`, `build_stage3_draft.py` (+ `draft_with_framework.py`, `draft_html_pack.py`), `build_stage4_transwrite.py`, `build_stage5_publish.py`, `postmortem_writeback.py`, `build_paradigm_profile.py`.
- **Orchestration skill**: `skills/dasheng-media-sop/SKILL.md` — the only formal orchestration entry. Always route via this skill in agentic flows.

### Skill registry

Source of truth: `skills/SKILL_ALIASES.md`. Formal skills (✅) currently in production:

| Skill | Role |
|---|---|
| `dasheng-media-sop` | Single orchestration controller / stage router |
| `dasheng-paradigm-profiler` | Optional `ParadigmProfile` pre-work asset |
| `dasheng-daily-intake` | Stage 1 — content intake & source aggregation |
| `dasheng-daily-phase2` | Stage 2 — AI brief / topic card generation (replaces deprecated `dasheng-stage-brief-ai` / `dasheng-daily-brief`) |
| `dasheng-daily-draft` | Stage 3 — draft + data + charts + cover images + self-contained HTML |
| `dasheng-stage-transwrite` | Stage 4 — channel-specific production: WeChat article, talking-head video, podcast |
| `dasheng-stage-publish` | Stage 5 — verification, packaging, draft push / manual pack, link recovery |
| `dasheng-daily-postmortem` | Stage 6 — review + knowledge writeback |
| `dasheng-finance-data` | Draft-time financial data + Chart.js spec generation |
| `dasheng-style-profiler` | Personal Style DNA extraction (14-dimensional) |
| `dasheng-html-anything-bridge` | Draft/Transwrite bridge into HTML Anything templates |
| `dasheng-html-video-bridge` | Transwrite bridge into local html-video for talking-head clips |
| `feishu-doc-creator` | Feishu document creation helper |

On-demand tools (🧰, not part of the formal chain): `dasheng-stage-rewrite-v3` (multi-variant rewrite, called from Draft/Publish when needed), `dasheng-video-roughcut` (FunASR + FFmpeg rough cut + subtitles).

Deprecated skill directories still present under `skills/` for back-compat (e.g. `dasheng-stage-brief-ai`, `dasheng-daily-clustering`, `dasheng-daily-outline`, `dasheng-stage-draft`, `dasheng-stage-publish-video`). Do not author against them — consult `skills/SKILL_ALIASES.md` for the mapping.

### State model: manifests + gates, not "latest directory"

The runtime is driven by canonical JSON files, not by directory mtimes or naming conventions. Code lives in `scripts/canonical_workflow.py`.

- **Stage roots** (`canonical_workflow.CANONICAL_STAGE_ROOTS`):
  - `intake` → `产物/01_内容采集/<run_id>/`
  - `brief` → `产物/02_内容聚合及选题分析/<run_id>/`
  - `draft` → `产物/05_初稿生成/<run_id>/`
  - `transwrite` → `产物/06_转写生产/<run_id>/`
  - `publish` → `产物/07_发布执行/<run_id>/`
  - `postmortem` → `产物/08_分析复盘/<run_id>/`
  - Optional `paradigm` → `产物/00_范式学习/<run_id>/`
- **Stage manifests** (required for every stage): `<stage>_manifest.json` with `stage` field matching the expected value. `ensure_stage_manifest()` enforces this.
- **Gate files** (must be `approved`/`accepted`/`confirmed`/`ready`/`locked`/`finalized`/`completed`/`done` to unblock the next stage):
  - `brief → draft`: `selected_topics.json`
  - `draft → transwrite`: `final_structure_snapshot.json` + `transwrite_decision.json`
  - `transwrite → publish`: `publish_decision.json`
- Stages refuse to run if the upstream manifest or gate is missing/invalid — never short-circuit by passing a hand-rolled path; let the dispatcher resolve it from `--run-id`.

### Critical invariants

- **Stage order is immutable** — no skipping, no producing downstream artifacts pre-gate.
- **`ParadigmProfile` is optional** and never a gate. It informs Brief/Draft/Transwrite/Publish prompts only.
- **Per-topic isolation** — each topic gets its own subdirectory; never merge content across topics.
- **Every stage produces (a) human-readable doc(s) AND a manifest JSON**.
- **Rewrite/transwrite inherits the draft's final structure** — never force a fixed three-part skeleton.
- **`ParadigmProfile` ≠ Style DNA** — Paradigm controls structure/narrative path/argument model/channel framework; Style DNA controls voice/vocabulary/sentence rhythm. They must stay separated.
- **Sample facts in `ParadigmProfile` are reference only** — never quote sample sentences or unverified data as article evidence.

### Writing system

The Draft (and on-demand Rewrite) stages apply two orthogonal layers:

- **Writing frameworks** (7): Painpoint / Story / Checklist / Comparison / Hot-topic / Opinion / Retrospective. See `skills/dasheng-stage-rewrite-v3/references/` and the Draft skill's framework loader (`scripts/framework_strategy_loader.py`).
- **Content enhancement strategies** (4): Angle Discovery, Density Boost, Detail Anchoring, Real Experience.
- **Style DNA**:
  - Preset: `luxun` (sharp/data-driven), `lemon` (warm/narrative).
  - Personal: extracted by `dasheng-style-profiler` from 3–10 historical articles in `${DASHENG_WORKSPACE}/风格参考/{author}/` using a 14-dimensional analysis. See `skills/dasheng-style-profiler/references/style-14d-framework.md`.

Brief recommends framework + strategy per topic; Draft generates following them; on-demand rewrite (`dasheng-stage-rewrite-v3`) can produce platform variants when Publish needs them.

### Core engine (`core/`)

- `core/orchestrator.py` — stage status enum + HITL checkpoint logic (PENDING / RUNNING / COMPLETED / FAILED / WAITING_HITL / HITL_APPROVED / HITL_REJECTED).
- `core/dna_engine.py` — Style DNA loader and application.
- `core/ai_integrator.py` — AI provider routing.
- `core/path_resolver.py` — workspace-relative path resolution paired with `scripts/path_config.py`.

## Environment setup

Two env templates exist; pick the one matching your shell setup:

1. `.env.template` — newer, uses `DASHENG_PROJECT_ROOT` / `DASHENG_DESKTOP_ROOT` / `DASHENG_FEISHU_CONFIG`. Recommended.
2. `ENV_TEMPLATE.env` — legacy, uses `DASHENG_WORKSPACE` / `DASHENG_OUTPUT_ROOT` / `FEISHU_APP_ID`/`FEISHU_APP_SECRET` directly. Still consumed by some scripts.

Copy and fill in:
```bash
cp .env.template ~/.openclaw/dasheng.env     # or: cp ENV_TEMPLATE.env ~/.openclaw/dasheng.env
set -a; source ~/.openclaw/dasheng.env; set +a
```

Required-ish variables (cross-check both templates against your runtime):
- `DASHENG_PROJECT_ROOT` / `DASHENG_WORKSPACE` — repo root
- `DASHENG_OUTPUT_ROOT` — daily run output (default `产物/` under repo root)
- `DASHENG_FEISHU_*` — Feishu config paths or `FEISHU_APP_ID` / `FEISHU_APP_SECRET` / `DASHENG_FEISHU_ROOT_URL` / `DASHENG_FEISHU_CHAT_ID`
- `TUSHARE_TOKEN` — financial data API
- `FINANCE_MOTION_WORKSPACE` — video generation workspace (optional)
- Image provider keys: `QHAIGC_*`, `MOLI_*`, `VECTOR_IMAGE_*`, `MINIMAX_API_KEY`

## Installation

Install skills into OpenClaw:
```bash
bash install_to_openclaw.sh                  # default: ~/.openclaw/skills
bash install_to_openclaw.sh /path/to/skills  # custom target
```

Python + Node deps:
```bash
pip install -r requirements.txt              # core
pip install -r requirements-media.txt        # media pipeline extras
npm install                                  # Feishu/JS helpers
```

Verify after install:
```bash
python3 scripts/verify_installation.py
```

## Daily workflow

### Mandatory pre-run check

Run smoke tests from `SMOKE_PROMPTS.md` at the start of each production day. They verify paths, credentials, every stage delivery interface, and the publish video pipeline; output goes to `smoke_report.md`.

### Stage execution (preferred unified CLI)

```bash
cd "${DASHENG_PROJECT_ROOT:-$DASHENG_WORKSPACE}"

# Sanity check before anything
python3 scripts/workflow_doctor.py --latest

# Optional pre-work
python3 scripts/run_mainline_stage.py paradigm <sample.md> \
  --run-id "$(date +%F_%H%M%S)" \
  --profile-name 结构变化解读 --scenario 行业解读 --channel 公众号

# Mainline (each subcommand auto-resolves the prior stage by --run-id)
python3 scripts/run_mainline_stage.py intake     --run-id <run_id>
python3 scripts/run_mainline_stage.py brief      --run-id <run_id>
python3 scripts/run_mainline_stage.py draft      --run-id <run_id>
python3 scripts/run_mainline_stage.py transwrite --run-id <run_id>
python3 scripts/run_mainline_stage.py publish    --run-id <run_id>
python3 scripts/run_mainline_stage.py postmortem --run-id <run_id>

# Diagnostic on a specific run
python3 scripts/run_mainline_stage.py doctor --run-id <run_id> --strict
```

### Stage deliverables

| Stage | Required artifacts |
|---|---|
| paradigm (opt) | `00_范式画像.md`, `paradigm_profile.yaml`, `paradigm_prompt_block.md`, `paradigm_manifest.json` |
| intake | `intake_manifest.json`, `raw/intake_records.json` |
| brief | `brief_manifest.json`, `selected_topics.json`, `topic_cards.json` |
| draft | `draft_manifest.json`, per-topic doc + HTML + data/chart specs, `final_structure_snapshot.json` |
| transwrite | `transwrite_manifest.json`, per-topic `wechat_article.final.{md,html}`, talking-head + podcast packs, `transwrite_decision.json` |
| publish | `publish_manifest.json`, channel adaptation/execution manifests, `publish_verification_report.json`, video files under `videos/` |
| postmortem | `postmortem_manifest.json`, knowledge writeback notes |

### Common single-purpose commands

Framework-driven Draft (called by the dispatcher; runnable standalone):
```bash
python3 scripts/draft_with_framework.py \
  --brief-dir "产物/02_内容聚合及选题分析/<run_id>" \
  --output-dir "产物/05_初稿生成/<run_id>"
```

Publish video supplement (5 motion templates: `claude-purple`, `cyberpunk`, `finance-business`, `medical-lancet`, `anime-light`):
```bash
python3 scripts/publish_video_supplement.py --style claude-purple
```

Push transwrite to Feishu:
```bash
node scripts/feishu_rewrite_push.js "$(date +%F)"
```

On-demand multi-variant rewrite (when Publish needs platform metadata regenerated):
```bash
python3 scripts/rewrite_execute_stage5.py     # consult dasheng-stage-rewrite-v3 SKILL.md
```

## Testing

```bash
python3 -m pytest tests/ -v                  # full unit suite
python3 -m pytest tests/test_<name>.py -v    # single file
python3 -m pytest tests/test_<name>.py::test_<func> -v  # single test
python3 scripts/workflow_doctor.py           # end-to-end health
```

Test files cover stage skills, contract enforcement, intake scoring, postmortem writeback, the Feishu sync paths, paradigm profile, and `phase2` AI brief generation.

## Version management

Tarball naming: `dasheng-media-workflow-skills-YYYYMMDD-vX`. Same-day iterations bump `v1` → `v2` → … . Never overwrite a published tarball — rollback depends on history.

## Important references

Pipeline contracts (use these first):
- `docs/STAGE_INTERFACES.md` — input/output spec per stage
- `skills/dasheng-media-sop/references/stage-contract.md` — formal contract
- `skills/dasheng-media-sop/references/stage-map.md` / `stage-module-map.md` — stage ↔ script ↔ skill map
- `skills/dasheng-media-sop/references/file-contracts.md` — delivery interface
- `skills/dasheng-media-sop/references/legacy-migration-map.md` — old-name → new-name mapping
- `skills/dasheng-media-sop/references/publish-architecture.md` / `publish-skill-matrix.md` — Publish internals
- `skills/dasheng-media-sop/references/update-protocol.md` — how to evolve the chain

Skill internals:
- `skills/dasheng-stage-transwrite/SKILL.md` — three-channel transwrite spec
- `skills/dasheng-stage-rewrite-v3/references/` — writing frameworks + enhancement strategies
- `skills/dasheng-style-profiler/references/style-14d-framework.md` — 14-dimensional style analysis
- `skills/dasheng-paradigm-profiler/SKILL.md` — paradigm extraction

Setup / ops:
- `INSTALLATION.md` — install walkthrough
- `SMOKE_PROMPTS.md` — daily smoke test
- `docs/CONFIGURATION.md` — env + config reference
- `docs/PRELAUNCH_CHECKLIST.md` — pre-launch checks
- `docs/technical/architecture.md` — system architecture
- `docs/guides/stage-by-stage.md` — operator walkthrough
