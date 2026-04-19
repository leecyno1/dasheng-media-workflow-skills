# 控制中心

这个目录是当前项目后续使用的统一控制入口。

目标只有两个：

1. 把所有控制文件、模板、阶段入口集中到一个地方
2. 让日常交付统一导出到桌面临时目录，避免产物分散

## 当前工作流顺序

1. `intake`
2. `brief`
3. `draft`
4. `rewrite`
5. `material`（含补素材）
6. `publish`
7. `postmortem`

## 固定规则

- 引擎、模板、控制文档统一从本目录进入
- 正式沉淀仍保留在项目仓库内，不直接依赖桌面临时目录
- 对外审阅和协作时，优先给桌面日目录中的绝对路径
- 每天单独建一个桌面日期目录，作为临时工作区

## 入口文件

- `00_控制文件导航.md`
- 总控 Skill：`skills/dasheng-media-sop/SKILL.md`
- 重构路线图：`10_大圣daily重构路线图.md`
- 模块迁移表：`11_大圣daily模块迁移表.md`
- 阶段模块映射：`/Volumes/PSSD/Projects/公众号文章/skills/dasheng-media-sop/references/stage-module-map.md`

## 当前默认总控 Skill

以后凡是本项目内的内容创作任务，默认优先遵循：

- `skills/dasheng-media-sop/SKILL.md`

它负责：

- 统一当前 7 阶段主链
- 约束阶段边界
- 规定交付接口
- 作为后续流程更新的唯一总控模板

旧 `dasheng-daily-*` 目录中的 skill 现在只承担三种角色：

- `internal module`
- `historical module`
- `legacy`

不再作为新的默认入口。

## 桌面交付目录

- 默认根目录：`/Users/lichengyin/Desktop/自媒体创作临时交付`
- 每日目录示例：`/Users/lichengyin/Desktop/自媒体创作临时交付/2026-03-26`

## 一键导出脚本

- `scripts/export_daily_delivery.py`
