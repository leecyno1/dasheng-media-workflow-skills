# Dasheng 7-Stage Contract (Export Snapshot)

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

## Publish Video Supplement

- Script: `scripts/publish_video_supplement.py`
- Engine: `finance-motion-8787/dashboard/scripts/export-scene-videos.mjs`
- Output:
  - `videos/interactive_charts/*.webm|*.mp4`
  - `videos/motion_narrative/*.webm|*.mp4`

