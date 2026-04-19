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
| Draft | 分题标准初稿、证据清单、待补证据项 |
| Material | 补充数据、图片、视频、封面、终稿回填说明 |
| Rewrite | 分题 4 版改写、字数统计、改写汇总包 |
| Publish | 视频补充包（互动图表 + motion）+ 各渠道成品包、平台路由、发布时间计划、执行结果、发布验真报告 |
| Postmortem | 效果结论、失效点、L1 回写建议 |

## 飞书协作最小集合（Stage 1-5 强制）

| 阶段 | 飞书共享文档 | 飞书群动作 | 飞书文件夹动作 |
| --- | --- | --- | --- |
| Intake | `01_内容采集_底稿` + `01_内容采集_报告` | 发送审阅摘要 + 文档链接 | 归入当日日期文件夹 |
| Brief | `02_编辑Brief库` + `02_编辑Brief_报告` | 发送候选题摘要 + 文档链接 | 归入当日日期文件夹 |
| Draft | `03_标准初稿_<topic>` + `03_初稿_报告` | 发送初稿摘要 + 全部文档链接 | 归入当日日期文件夹 |
| Material | `05_MaterialPack` + `05_Material_报告` | 发送素材完成摘要 + 文档链接 + 文件夹链接 | 上传素材目录到当日日期文件夹 |
| Rewrite | `<topic>__rewrite_bundle`（每题一篇） | 每题一条消息，发送字数统计 + 文档链接 | 归入当日日期文件夹 |

## 终稿 -> Material 回填接口

- 终稿必须在正文中保留标准锚点，或至少保留稳定章节位置。
- `material` 必须产出真实图片、图表、表格、数据图。
- 回填优先顺序：
  1. 直接回填到飞书终稿文档对应锚点或章节位置
  2. 同步更新 `05_MaterialPack`
  3. 在群消息中说明本轮已回填 / 待人工筛选项

## 发布前审核门

- `publish` 之前，前五阶段至少要满足：
  - 飞书共享文档已创建
  - 飞书群已发送审阅消息
  - Material 素材文件夹已上传飞书
  - 终稿文档关键锚点已完成首轮素材回填
  - Rewrite 4 版已完成字数硬校验并推送飞书群
  - 发布前视频补充已完成并落盘：
    - `publish_video_supplement_report.md`
    - `publish_video_supplement_manifest.json`
  - `publish_decision.json` 已确认标题、封面、路由、发布时间

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

`intake -> brief -> draft -> material -> rewrite -> publish -> postmortem`
