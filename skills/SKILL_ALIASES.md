# 大圣媒体工作流 - Skill 别名与版本映射

本文档定义技能的正式名称、别名与版本关系。

## 正式 Skill 列表

| Skill 名称 | 版本 | 状态 | 说明 |
|------------|------|------|------|
| `dasheng-media-sop` | 1.0.0 | ✅ 正式 | 总控入口，唯一正式编排 skill |
| `dasheng-daily-intake` | 1.0.0 | ✅ 正式 | 内容采集阶段 |
| `dasheng-daily-phase2` | 1.0.0 | ✅ 正式 | 选题分析阶段（替代 dasheng-daily-brief） |
| `dasheng-daily-draft` | 1.0.0 | ✅ 正式 | 初稿生成阶段 |
| `dasheng-daily-material` | 1.0.0 | ✅ 正式 | 素材收集阶段 |
| `dasheng-stage-rewrite-v3` | 1.0.0 | ✅ 正式 | 多版本改写（推荐使用） |
| `dasheng-stage-publish` | 1.0.0 | ✅ 正式 | 内容发布阶段 |
| `dasheng-daily-postmortem` | 1.0.0 | ✅ 正式 | 复盘与知识回写 |

## 已废弃 Skill（请勿使用）

| Skill 名称 | 替代方案 | 废弃原因 |
|------------|----------|----------|
| `dasheng-stage-brief-ai` | `dasheng-daily-phase2` | 能力已被吸收合并 |
| `dasheng-daily-brief` | `dasheng-daily-phase2` | 与 phase2 重复 |
| `dasheng-daily-clustering` | `dasheng-daily-intake` | 与 intake 重复 |
| `dasheng-daily-outline` | `dasheng-daily-draft` | 与 draft 重复 |
| `dasheng-daily-final` | `dasheng-daily-draft` | 与 draft 重复 |
| `dasheng-stage-draft` | `dasheng-daily-draft` | 旧版本，已合并 |
| `dasheng-stage-material-refill` | `dasheng-daily-material` | 旧版本，已合并 |
| `dasheng-stage-rewrite` | `dasheng-stage-rewrite-v3` | 旧版本，功能不完整 |
| `dasheng-stage-intake-brief-draft` | `dasheng-daily-intake` + `dasheng-daily-phase2` | 多阶段合并 |
| `dasheng-stage-publish-video` | `dasheng-stage-publish` | 已并入 publish 阶段 |
| `dasheng-stage-distribute` | `dasheng-stage-publish` | 已并入 publish 阶段 |
| `dasheng-collection-workflow` | `dasheng-daily-intake` | 能力已并入 intake |
| `dasheng-sop-orchestrator` | `dasheng-media-sop` | 旧版本总控 |
| `dasheng-style-profiler` | `dasheng-media-sop` | 能力已并入 SOP |

## 别名映射

以下别名用于兼容旧调用：

```json
{
  "aliases": {
    "dasheng-stage-brief-ai": "dasheng-daily-phase2",
    "dasheng-daily-brief": "dasheng-daily-phase2",
    "dasheng-daily-clustering": "dasheng-daily-intake",
    "dasheng-daily-outline": "dasheng-daily-draft",
    "dasheng-daily-final": "dasheng-daily-draft",
    "dasheng-stage-draft": "dasheng-daily-draft",
    "dasheng-stage-material-refill": "dasheng-daily-material",
    "dasheng-stage-rewrite": "dasheng-stage-rewrite-v3",
    "dasheng-stage-intake-brief-draft": "dasheng-daily-intake",
    "dasheng-stage-publish-video": "dasheng-stage-publish",
    "dasheng-stage-distribute": "dasheng-stage-publish",
    "dasheng-collection-workflow": "dasheng-daily-intake",
    "dasheng-sop-orchestrator": "dasheng-media-sop",
    "dasheng-style-profiler": "dasheng-media-sop"
  }
}
```

## 路径约定

所有正式 skill 位于 `skills/` 目录，使用 `dasheng-daily-*` 或 `dasheng-stage-*` 命名：
- `dasheng-daily-*`：日常生产流程 skill
- `dasheng-stage-*`：单阶段执行 skill
- `dasheng-media-*`：核心引擎 skill

## 安装说明

当通过 `scripts/install.sh` 安装时，系统会自动：
1. 验证所有正式 skill 的完整性
2. 创建必要的符号链接（如果有别名配置）
3. 更新 OpenClaw 的 skill 注册表
