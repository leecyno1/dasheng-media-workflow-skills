# 交付接口

## 总目录约定

- 引擎：`/Volumes/PSSD/Projects/公众号文章/引擎`
- Skills：`/Volumes/PSSD/Projects/公众号文章/skills`
- 产物：`/Volumes/PSSD/Projects/公众号文章/产物`

## 控制中心

- 总控入口：`引擎/00_控制中心/README.md`
- 当前阶段接口：`引擎/03_全链路SOP工作流/STAGE_INTERFACES.md`

## 阶段交接最小集合

| 阶段 | 交给下游的最小集合 |
| --- | --- |
| Intake | 原始链接清单、来源摘要、采集结论 |
| Brief | 独立题卡、核心判断、证据缺口、研究入口、来源包 |
| Draft | 分题标准初稿、证据清单、待补证据项、最终结构确认 |
| Publish | 按需视频补充包 + 各渠道成品包、平台路由、发布时间计划、执行结果、发布验真报告 |
| Postmortem | 效果结论、失效点、L1 回写建议 |

## 飞书协作最小集合（主链强制）

| 阶段 | 飞书共享文档 | 飞书群动作 | 飞书文件夹动作 |
| --- | --- | --- | --- |
| Intake | `01_内容采集_底稿` + `01_内容采集_报告` | 发送审阅摘要 + 文档链接 | 归入当日日期文件夹 |
| Brief | `02_编辑Brief库` + `02_编辑Brief_报告` | 发送候选题摘要 + 文档链接 | 归入当日日期文件夹 |
| Draft | `03_标准初稿_<topic>` + `03_初稿_报告` | 发送初稿摘要 + 全部文档链接 | 归入当日日期文件夹 |
| Publish | `07_发布计划` + `07_发布包` | 发送发布计划 + 待人工确认项 | 归入当日日期文件夹 |
| Postmortem | `08_复盘报告` + `08_L1回写建议` | 发送复盘结论 | 归入当日日期文件夹 |

## 按需素材回填接口

- Draft 正文必须保留稳定章节位置，并在 HTML 内完成真实图片、图表、表格和数据图嵌入。
- 若 Draft 缺少必要资产，`draft_manifest.status` 必须标记为 `incomplete_assets`，不得把缺口留给独立素材环节。

## 发布前审核门

- `publish` 之前，主链至少要满足：
  - 飞书共享文档已创建
  - 飞书群已发送审阅消息
  - `final_structure_snapshot.json` 已确认
  - `publish_decision.json` 已确认标题、封面、路由、发布时间
  - 若渠道需要视频补充，相关发布补充产物已完成并落盘：
    - `publish_video_supplement_report.md`
    - `publish_video_supplement_manifest.json`

## Publish 最小交付集合

- `07_发布计划.md`
- `07_发布包.md`
- `channel_adaptation_manifest.json`
- `channel_execution_manifest.json`
- `publish_verification_report.json`
- `publish_manifest.json`

说明：

- 只有 `channel_execution_manifest.json` 不能视为发布成功。
- 必须同时存在 `publish_verification_report.json`，并且平台状态通过验真，才能对外汇报“已发布”。

## 人工干预原则

- 每阶段结尾都要留人工干预位。
- 人工可改：
  - 选题去留
  - 大纲顺序
  - 标题
  - 节奏
  - 素材优先级
  - 发布时间
- 人工不可直接绕过：
  - 事实校验
  - 证据缺失标记
  - 阶段交接文档

## 当前默认顺序

`intake -> brief -> draft -> publish -> postmortem`
