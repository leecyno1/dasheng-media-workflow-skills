# Dasheng Canonical Stage Contract

## Stage Order

`intake -> brief -> draft -> material -> rewrite -> publish -> postmortem`

## Required Deliverables

- Intake: `intake_manifest.json`
- Brief: `brief_manifest.json`
- Draft: `draft_manifest.json`
- Material: `material_manifest.json`
- Rewrite: `rewrite_manifest.json` + per-topic `meta.json`
- Publish: `publish_manifest.json` + `publish_video_supplement_manifest.json`
- Postmortem: `postmortem_manifest.json`

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

- Publish includes `Publish Gate / Video Supplement / Channel Adaptation / Channel Execution / Publish Guard`
- `distribute` is not a standalone formal stage in the current chain
- Video supplement outputs:
  - `videos/interactive_charts/*.webm|*.mp4`
  - `videos/motion_narrative/*.webm|*.mp4`
- Publish outputs:
  - `channel_adaptation_manifest.json`
  - `channel_execution_manifest.json`
  - `publish_verification_report.json`
  - `publish_manifest.json`
