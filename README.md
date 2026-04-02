# Dasheng Media Workflow Skills

一套面向自媒体日更团队的 OpenClaw/Codex Skills 包，覆盖从采集到发布复盘的完整 SOP。

## 1. 能力概览

- 固定主链：`intake -> brief -> draft -> material -> rewrite -> publish -> postmortem`
- 面向多人协作：按“每题独立目录”组织，避免混稿
- 兼容飞书交付：文档与素材链路可接入人工审核
- 发布前增强：支持图表动效视频与叙事动画视频补充

## 2. 技能清单

仓库内共 5 个技能：

1. `dasheng-sop-orchestrator`  
   全链路入口与调度器，负责阶段识别、路由和规则约束。

2. `dasheng-stage-intake-brief-draft`  
   负责 `intake/brief/draft` 三阶段串联交付。

3. `dasheng-stage-material-refill`  
   负责素材生成、筛选、落盘及回填策略。

4. `dasheng-stage-rewrite`  
   负责多渠道改写、多 DNA 风格与情绪档位适配。

5. `dasheng-stage-publish-video`  
   负责发布前视频增强（动态图表 + motion 叙事）。

## 3. 目录结构

```text
.
├── skills/
│   ├── dasheng-sop-orchestrator/
│   ├── dasheng-stage-intake-brief-draft/
│   ├── dasheng-stage-material-refill/
│   ├── dasheng-stage-rewrite/
│   └── dasheng-stage-publish-video/
├── ENV_TEMPLATE.env
├── SMOKE_PROMPTS.md
├── EXPORT_MANIFEST.md
└── install_to_openclaw.sh
```

## 4. 安装

### 4.1 快速安装到默认目录

```bash
bash install_to_openclaw.sh
```

默认安装目标：`~/.openclaw/skills`

### 4.2 安装到自定义目录

```bash
bash install_to_openclaw.sh /your/openclaw/skills
```

## 5. 环境配置

1. 复制模板：

```bash
cp ENV_TEMPLATE.env ~/.openclaw/dasheng.env
```

2. 填写你自己的密钥与路径（重点字段）：

- `DASHENG_WORKSPACE`
- `FINANCE_MOTION_WORKSPACE`
- `DASHENG_OUTPUT_ROOT`
- `DASHENG_FEISHU_ROOT_URL`
- `DASHENG_FEISHU_CHAT_ID`
- `FEISHU_APP_ID`
- `FEISHU_APP_SECRET`
- `TUSHARE_TOKEN`
- 生图 provider key（启航、魔力方舟、向量、MiniMax）

3. 运行前加载：

```bash
set -a; source ~/.openclaw/dasheng.env; set +a
```

## 6. 每日启动建议（强烈推荐）

使用 `SMOKE_PROMPTS.md` 先做一次最小自检，确认：

- 路径可达
- 凭据可用
- 各阶段交付接口齐全
- 发布前视频链路可执行

建议将自检结果输出到 `smoke_report.md` 后再跑正式任务。

## 7. 标准运行方式

### 7.1 入口 skill

优先从 `dasheng-sop-orchestrator` 进入，避免阶段错位。

### 7.2 执行规则（关键）

- 必须遵循固定主链顺序
- 不跨阶段提前产出正式交付
- 每阶段必须有“文档 + manifest”
- 多选题必须按题拆分（每题单独目录）

## 8. 发布前视频增强（已集成）

`publish` 阶段支持两类补充：

1. **动态图表视频**  
   CSV/表格数据 -> `finance-motion-8787` 场景渲染 -> `webm/mp4`

2. **叙事动画视频**  
   基于改写稿提炼结构与关键数据 -> motion skills 生成短视频资产

## 9. 版本策略

- 命名规范：`dasheng-media-workflow-skills-YYYYMMDD-vX`
- 同日多次迭代：`v1/v2/v3` 递增
- 禁止覆盖历史包，确保可回滚

## 10. 升级建议

- 在每次新增规则后同步更新 `SKILL.md` 与 `EXPORT_MANIFEST.md`
- 变更路径或接口时先更新 `ENV_TEMPLATE.env`
- 先跑自检，再跑正式阶段，减少运行中断

## 11. 仓库信息

- Repo: <https://github.com/leecyno1/dasheng-media-workflow-skills>
- Visibility: `PUBLIC`

