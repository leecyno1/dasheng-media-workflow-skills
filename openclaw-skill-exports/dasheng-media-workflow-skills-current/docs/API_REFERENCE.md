# API Reference

Complete API reference for the Dasheng Media Workflow system.

## Overview

The system uses a **manifest-driven architecture** where each stage produces:
1. **Manifest JSON** - Canonical state (source of truth)
2. **Gate JSON** - HITL decision point
3. **Markdown Report** - Human-readable delivery view

## Stage Interfaces

### Stage 1: Intake (内容采集)

#### Input
- None (scrapes from configured data sources)

#### Output Files
- `intake_manifest.json` - Canonical intake state
- `intake_records.json` - Raw intake records
- `entity_rankings.json` - Entity frequency analysis
- `event_clusters.json` - Event clustering results
- `channel_top10.json` - Top 10 per channel
- `brief_input.json` - Prepared input for Brief stage
- `intake_review.json` - Optional HITL gate

#### Manifest Schema
```json
{
  "run_id": "YYYY-MM-DD_HHMMSS",
  "stage": "intake",
  "status": "completed",
  "timestamp": "ISO8601",
  "sources": {
    "port_5173": { "count": 0, "valid": 0 },
    "port_18080": { "count": 0, "valid": 0 },
    "port_8001": { "count": 0, "valid": 0 },
    "external": { "count": 0, "valid": 0 }
  },
  "summary": {
    "total_items": 0,
    "valid_items": 0,
    "dedup_items": 0,
    "top_entities": []
  },
  "next_stage": "brief"
}
```

#### CLI
```bash
python3 scripts/run_stage1_intake.py
```

---

### Stage 2: Brief (选题分析)

#### Input
- `brief_input.json` (from Intake)
- `channel_top10.json` (from Intake)
- `event_clusters.json` (from Intake)

#### Output Files
- `brief_manifest.json` - Canonical brief state
- `topic_cards.json` - Structured topic cards
- `selected_topics.json` - **MANDATORY GATE** for Draft

#### Topic Card Schema
```json
{
  "topic_id": "string",
  "topic_kind": "hot_event|trend_analysis|opinion_piece",
  "mother_topic_id": "string|null",
  "angle_variant_of": "string|null",
  "core_proposition": "string",
  "conflict_axis": "string",
  "scoring": {
    "heat": 0-10,
    "sharpness": 0-10,
    "evidence": 0-10,
    "longevity": 0-10,
    "reader_value": 0-10
  },
  "proof_requirements": [
    {
      "requirement": "string",
      "current_evidence": [],
      "gap": "string"
    }
  ],
  "recommended_data_angles": [],
  "recommended_visual_angles": []
}
```

#### Gate Schema (selected_topics.json)
```json
{
  "run_id": "string",
  "status": "approved",
  "selected_topics": [
    {
      "topic_id": "string",
      "editor_note": "string",
      "priority": 1-10
    }
  ]
}
```

---

### Stage 3: Draft (初稿生成)

#### Input
- `selected_topics.json` - **MANDATORY GATE**
- `topic_cards.json` (from Brief)

#### Output Files
- `draft_manifest.json` - Canonical draft state
- `03_标准初稿_<topic>.md` - Standard draft per topic
- `03_ReasoningSheet_<topic>.md` - Reasoning structure
- `03_ReasoningSheet_<topic>.json` - Structured reasoning
- `final_structure_snapshot.json` - **MANDATORY GATE** for Material/Rewrite

#### Manifest Schema
```json
{
  "run_id": "string",
  "stage": "draft",
  "status": "completed",
  "output_dir": "string",
  "drafts": [
    {
      "topic_id": "string",
      "title": "string",
      "draft_file": "string",
      "reasoning_sheet_file": "string",
      "reasoning_sheet_json": "string",
      "word_count": 0,
      "h2_count": 0
    }
  ],
  "next_stage": "material"
}
```

#### Gate Schema (final_structure_snapshot.json)
```json
{
  "run_id": "string",
  "status": "approved",
  "topics": [
    {
      "topic_id": "string",
      "title": "string",
      "doc_file": "string",
      "final_primary_sections": ["string"],
      "h2_count": 0,
      "editor_note": "string"
    }
  ]
}
```

#### CLI
```bash
python3 scripts/build_stage3_draft.py \
  --selected-topics /path/to/selected_topics.json \
  --run-id YYYY-MM-DD_HHMMSS
```

---

### Stage 4: Material (素材收集)

#### Input
- `draft_manifest.json` (from Draft)
- `final_structure_snapshot.json` - **MANDATORY GATE**

#### Output Files
- `material_manifest.json` - Canonical material state
- `material_acceptance.json` - **MANDATORY GATE** for Rewrite
- `pack_assets/<topic>/` - Asset directories

#### Manifest Schema
```json
{
  "run_id": "string",
  "stage": "material",
  "status": "completed",
  "topics": [
    {
      "topic_id": "string",
      "assets": [
        {
          "asset_id": "string",
          "asset_type": "chart|image|video|infographic",
          "claim_id": "string",
          "section_id": "string",
          "file_path": "string",
          "usage_type": "evidence|illustration|cover",
          "relevance_score": 0.0-1.0,
          "editor_status": "pending|approved|rejected"
        }
      ]
    }
  ],
  "next_stage": "rewrite"
}
```

#### Gate Schema (material_acceptance.json)
```json
{
  "run_id": "string",
  "status": "approved",
  "topics": [
    {
      "topic_id": "string",
      "assets_count": 0,
      "editor_review": {
        "charts_approved": 0,
        "images_approved": 0,
        "videos_approved": 0,
        "total_approved": 0
      }
    }
  ]
}
```

#### CLI
```bash
python3 scripts/material_execute_pack.py \
  --draft-manifest /path/to/draft_manifest.json
```

---

### Stage 5: Rewrite (改写)

#### Input
- `draft_manifest.json` (from Draft)
- `final_structure_snapshot.json` - **MANDATORY GATE**
- `material_manifest.json` (optional, for asset integration)

#### Output Files
- `rewrite_manifest.json` - Canonical rewrite state
- `<topic>__rewrite_bundle.md` - All versions bundled
- `<topic>__wechat_luxun_hot.md` - WeChat hot version
- `<topic>__wechat_lemon_normal.md` - WeChat normal version
- `<topic>__xhs_video_luxun_hot.md` - Xiaohongshu hot version
- `<topic>__xhs_video_lemon_normal.md` - Xiaohongshu normal version
- `meta.json` - Version metadata

#### Manifest Schema
```json
{
  "run_id": "string",
  "stage": "rewrite",
  "status": "completed",
  "topics": {
    "topic-001": {
      "wechat_hot": {
        "status": "completed",
        "content": "string",
        "quality_score": 8.0-10.0,
        "quality_status": "excellent|good|acceptable",
        "anchor_preserved_rate": 0-100,
        "word_count": 0,
        "target_word_count": 0,
        "attempt": 1-3
      }
    }
  },
  "summary": {
    "total_topics": 0,
    "completed_versions": 0,
    "failed_topics": 0,
    "versions": []
  },
  "next_stage": "publish"
}
```

#### Version Schema
```json
{
  "wechat_hot": {
    "platform": "wechat",
    "tone": "hot",
    "word_count": {
      "target": 1300,
      "min": 1105,
      "max": 1495
    },
    "primary_audience": "知识精英、投资者"
  },
  "wechat_normal": {
    "platform": "wechat",
    "tone": "normal",
    "word_count": {
      "target": 1000,
      "min": 850,
      "max": 1150
    }
  },
  "xiaohongshu_hot": {
    "platform": "xiaohongshu",
    "tone": "hot",
    "word_count": {
      "target": 900,
      "min": 765,
      "max": 1035
    }
  },
  "xiaohongshu_normal": {
    "platform": "xiaohongshu",
    "tone": "normal",
    "word_count": {
      "target": 650,
      "min": 553,
      "max": 748
    }
  }
}
```

#### Quality Requirements
- **Quality Score**: ≥8.0/10
- **Word Count Deviation**: ±15%
- **Anchor Preservation Rate**: ≥80%
- **Auto-retry**: Up to 3 attempts

#### CLI
```bash
python3 scripts/rewrite_execute_stage5.py \
  --draft-manifest /path/to/draft_manifest.json \
  --versions wechat_hot,wechat_normal,xiaohongshu_hot,xiaohongshu_normal \
  --json-output
```

---

### Stage 6: Publish (渠道分发)

#### Input
- `rewrite_manifest.json` (from Rewrite)
- `material_manifest.json` (from Material)

#### Output Files
- `publish_manifest.json` - Canonical publish state
- `publish_decision.json` - **MANDATORY GATE**
- `channel_adaptation_manifest.json` - Channel-specific adaptations
- `channel_execution_manifest.json` - Execution results
- `publish_verification_report.json` - Post-publish verification

#### Manifest Schema
```json
{
  "run_id": "string",
  "stage": "publish",
  "status": "completed|blocked",
  "channel_packs": [
    {
      "platform": "wechat|weibo|xhs|douyin|zhihu",
      "topic_id": "string",
      "version": "string",
      "url": "string",
      "status": "draft|published|manual_required",
      "msg_id": "string"
    }
  ],
  "publish_skill_stack": {
    "wechat": [],
    "weibo": [],
    "xhs": [],
    "douyin": [],
    "zhihu": []
  },
  "next_stage": "postmortem"
}
```

#### Gate Schema (publish_decision.json)
```json
{
  "run_id": "string",
  "status": "approved",
  "decisions": [
    {
      "topic_id": "string",
      "platform": "string",
      "version": "string",
      "publish_mode": "draft|publish|skip",
      "scheduled_time": "ISO8601|null"
    }
  ]
}
```

#### CLI
```bash
python3 scripts/publish_video_supplement.py \
  --rewrite-manifest /path/to/rewrite_manifest.json \
  --material-manifest /path/to/material_manifest.json
```

---

### Stage 7: Postmortem (分析复盘)

#### Input
- `publish_manifest.json` (from Publish)
- `rewrite_manifest.json` (from Rewrite)
- `material_manifest.json` (from Material)

#### Output Files
- `postmortem_manifest.json` - Canonical postmortem state
- `08_复盘报告.md` - Postmortem report
- `08_L1回写建议.md` - L1 knowledge base update suggestions

#### Manifest Schema
```json
{
  "run_id": "string",
  "stage": "postmortem",
  "status": "completed",
  "topics": [
    {
      "topic_id": "string",
      "performance_metrics": {
        "wechat": {
          "read_count": 0,
          "like_count": 0,
          "share_count": 0,
          "comment_count": 0
        }
      },
      "quality_metrics": {
        "wechat_hot": {
          "score": 0.0,
          "word_count": 0
        }
      }
    }
  ],
  "pattern_updates": {
    "topic_patterns": 0,
    "evidence_patterns": 0,
    "visual_patterns": 0,
    "channel_patterns": 0
  }
}
```

---

## Common Patterns

### Manifest File Naming
- Format: `<stage>_manifest.json`
- Location: `产物/<stage_number>_<stage_name>/<run_id>/`
- Example: `产物/06_改写/2026-04-17_120000/rewrite_manifest.json`

### Gate File Naming
- Format: `<gate_name>.json`
- Location: Same as manifest
- Examples:
  - `selected_topics.json` (Brief → Draft gate)
  - `final_structure_snapshot.json` (Draft → Material/Rewrite gate)
  - `material_acceptance.json` (Material → Rewrite gate)
  - `publish_decision.json` (Rewrite → Publish gate)

### Run ID Format
- Format: `YYYY-MM-DD_HHMMSS`
- Example: `2026-04-17_120000`
- Generated: `datetime.now().strftime("%Y-%m-%d_%H%M%S")`

### Status Values
- `pending` - Not started
- `in_progress` - Currently executing
- `completed` - Successfully finished
- `failed` - Execution failed
- `blocked` - Waiting for gate approval
- `approved` - Gate approved (for gate files)

---

## Error Handling

### Standard Error Response
```json
{
  "success": false,
  "error": "string",
  "error_code": "string",
  "stage": "string",
  "run_id": "string"
}
```

### Common Error Codes
- `GATE_NOT_FOUND` - Required gate file missing
- `GATE_NOT_APPROVED` - Gate status not approved
- `MANIFEST_INVALID` - Manifest JSON invalid
- `QUALITY_THRESHOLD_NOT_MET` - Quality score below threshold
- `WORD_COUNT_OUT_OF_RANGE` - Word count deviation too large
- `ANCHOR_PRESERVATION_LOW` - Anchor preservation rate too low

---

## Skill Invocation

### Skill Invoker Interface
```python
from skill_invoker import SkillInvoker

invoker = SkillInvoker()
result = invoker.invoke(skill_name, payload, context)
```

### Standard Skill Response
```json
{
  "success": true|false,
  "data": {},
  "error": "string|null",
  "metadata": {
    "skill_name": "string",
    "execution_time_ms": 0,
    "model_used": "string"
  }
}
```

---

## Validation Rules

### Word Count Validation
```python
def validate_word_count(actual, target, tolerance=0.15):
    min_allowed = target * (1 - tolerance)
    max_allowed = target * (1 + tolerance)
    return min_allowed <= actual <= max_allowed
```

### Quality Score Validation
```python
def validate_quality_score(score, threshold=8.0):
    return score >= threshold
```

### Anchor Preservation Validation
```python
def validate_anchor_preservation(rate, threshold=80):
    return rate >= threshold
```

---

## Next Steps

- See [INSTALLATION.md](INSTALLATION.md) for installation guide
- See [CONFIGURATION.md](CONFIGURATION.md) for configuration options
- See [CLAUDE.md](../CLAUDE.md) for development guidelines
