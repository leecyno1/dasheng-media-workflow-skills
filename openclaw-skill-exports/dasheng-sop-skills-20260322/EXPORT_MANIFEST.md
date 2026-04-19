# Dasheng SOP Skills Export (Sanitized)

> 已归档。该快照包含大量旧入口与历史 skill，不再建议安装。
> 当前正式导出请改用：`openclaw-skill-exports/dasheng-media-workflow-skills-current/EXPORT_MANIFEST.json`

## Export time
- 2026-03-22

## 历史说明
- 该快照属于早期导出，包含旧入口、旧阶段命名和已停用 skill。
- 不再提供逐项安装清单，避免误装回旧链。
- 如需当前正式技能，请仅安装：
  - `dasheng-sop-orchestrator`
  - `dasheng-stage-intake-brief-draft`
  - `dasheng-stage-material-refill`
  - `dasheng-stage-rewrite`
  - `dasheng-stage-publish-video`

## Sanitization applied
- Removed runtime data and historical run artifacts (`runtime-data/`, `runs/`, `artifacts/`).
- Replaced sensitive config fields with `<REPLACE_ME>`.
- Rewrote machine-specific absolute paths from `/Users/lichengyin/clawd` to `${OPENCLAW_WORKSPACE}`.

## Migration steps
1. 不要继续安装该归档包中的旧入口。
2. 改用 `openclaw-skill-exports/dasheng-media-workflow-skills-current/EXPORT_MANIFEST.json`。
3. 仅按当前正式导出清单安装 skill，并填写 `<REPLACE_ME>`。
