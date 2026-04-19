# 大圣daily 模块迁移表

更新时间：`2026-03-28`

## 一、总表

| 模块 | 当前状态 | 后续定位 | 处理建议 |
| --- | --- | --- | --- |
| `dasheng-media-sop` | 新增 | 总控主入口 | 保留并持续更新 |
| `dasheng-daily-intake` | 可用 | Intake 执行层 | 保留，后续替换模拟采集 |
| `dasheng-daily-phase2` | 可用 | Brief 执行层 | 保留 |
| `dasheng-daily-clustering` | 薄封装 | Brief 子模块 | 合并语义，不单独对外 |
| `dasheng-daily-brief` | 旧 Brief 实现 | Brief 子模块 | 合并语义，不单独对外 |
| `dasheng-daily-material` | 可用 | Material 执行层 | 保留 |
| `dasheng-daily-draft` | 偏旧 | Draft 历史模块 | 暂不删除，退出主链 |
| `dasheng-daily-outline` | 旧链路中间层 | 历史模块 | 退出主链 |
| `dasheng-daily-final` | 旧强化层 | 历史模块 | 退出主链 |
| `dasheng-daily-postmortem` | 原型可用 | Postmortem 执行层 | 保留并增强 |
| `dasheng-daily-shared` | 基础设施 | 运行时共享层 | 必须保留 |
| `dasheng-caiji` | 历史技能 | legacy | 归档 |
| `dasheng-clustering` | 历史技能 | legacy | 归档 |
| `dasheng-xuanti` | 历史技能 | legacy | 归档 |
| `dasheng-xuanti-skill` | 历史技能 | legacy | 归档 |
| `dasheng-intake-brief-prod` | 过渡技能 | legacy | 归档 |
| `dasheng-brief-builder` | 过渡技能 | legacy | 归档 |

## 二、现阶段实际主链

当前真正应执行的是：

`dasheng-media-sop`

内部调用语义应映射为：

- `intake` -> `dasheng-daily-intake` / 项目脚本
- `brief` -> `dasheng-daily-phase2`
- `draft` -> 项目级 Draft 方案
- `rewrite` -> 控制中心 + 改写模板 + DNA 配置
- `material` -> `material_execute_pack.py` + `material_merge_from_rewrite.py`
- `publish` -> 待统一发布编排
- `postmortem` -> `dasheng-daily-postmortem`

## 三、立即执行项

### 1. 不再把以下模块当作主入口

- `dasheng-daily-outline`
- `dasheng-daily-final`
- `dasheng-daily-brief`
- `dasheng-daily-clustering`

### 2. 保留但降级为内部模块

- `dasheng-daily-intake`
- `dasheng-daily-phase2`
- `dasheng-daily-material`
- `dasheng-daily-postmortem`

### 3. 已完成 / 待完成动作

- 已完成：在旧 Skill 的 `SKILL.md` 中增加 `legacy` / `historical module` / `internal module` 标记
- 已完成：在控制中心与总控 Skill 中加入统一入口映射引用
- 待完成：为 `publish` 新建正式执行器
