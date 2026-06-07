# Dasheng Canonical Stage Contract

## Stage Order

`intake -> brief -> draft -> publish -> postmortem`

## Required Deliverables

- Intake: `intake_manifest.json`
- Brief: `brief_manifest.json`
- Draft: `draft_manifest.json`
- Publish: `publish_manifest.json` + `publish_decision.json`
- Postmortem: `postmortem_manifest.json`

Optional tools may emit `material_manifest.json` or `rewrite_manifest.json`, but these files are not required gates in the canonical mainline.

## Brief Contract

- Generation mode: `ai_only`
- Output shape: 8-10 flat independent topic cards
- Canonical outputs:
  - `02_编辑Brief库.md`
  - `02_研究Brief库.md`
  - `02_编辑Brief_报告.md`
  - `topic_cards.json`
  - `selected_topics.json`
  - `brief_manifest.json`

## Publish Contract

- Formal upstream input: `draft_manifest.json`
- Required gate: `publish_decision.json`
- Publish includes `Publish Gate / Video Supplement / Channel Adaptation / Channel Execution / Publish Guard`
- `distribute` is not a standalone formal stage in the current chain
- Video supplement is optional unless the selected channel requires video. Outputs, when present:
  - `videos/interactive_charts/*.webm|*.mp4`
  - `videos/motion_narrative/*.webm|*.mp4`
- Publish outputs:
  - `channel_adaptation_manifest.json`
  - `channel_execution_manifest.json`
  - `publish_verification_report.json`
  - `publish_manifest.json`
