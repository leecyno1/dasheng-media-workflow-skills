# 大圣daily 重构路线图

更新时间：`2026-03-28`

## 一、重构目标

当前项目里并存两套链路：

1. 旧 `dasheng-daily-*` 运行时工作流
2. 新的 7 阶段创作 SOP

重构目标不是推翻旧资产，而是完成三件事：

1. 让**新 7 阶段 SOP**成为唯一正式主链
2. 让旧 `dasheng-daily-*` 模块退居到底层执行层
3. 让后续所有流程修改都只改一套总控模板

## 二、当前完成度判断

### 已完成

- 已建立总控 Skill：`skills/dasheng-media-sop/SKILL.md`
- 已固化当前标准顺序：`intake -> brief -> draft -> material -> rewrite -> publish -> postmortem`
- 已形成 `rewrite` 参数矩阵与默认组合
- 已形成 `material + 补素材` 合并执行方式
- 已形成阶段接口文档与交付文档标准

### 半完成

- `intake`：项目链路已形成，但旧 `dasheng-daily-intake` 仍有模拟实现残留
- `brief`：项目链路成熟，但旧 `daily-brief / daily-clustering / phase2` 仍并行存在
- `publish`：模板与外部技能齐备，但尚未形成统一发布编排器
- `postmortem`：已有原型，但未接真实平台数据回流

### 未完成

- 旧链路与新链路的正式“保留 / 废弃 / 迁移”标记
- 发布层统一调度
- 复盘层真实数据闭环

## 三、重构分期

### Phase A｜统一认知层

目标：

- 只保留一套对外叙述
- 用总控 Skill 接管话语权

动作：

- 新建 `dasheng-media-sop`
- 更新控制中心 README
- 明确当前唯一标准主链

状态：**已完成**

### Phase B｜统一阶段语义

目标：

- 明确每阶段职责、交付物、人工干预位

动作：

- 固化 `STAGE_INTERFACES.md`
- 固化各阶段 prompt
- 明确 `draft / rewrite / material / publish` 的边界

状态：**已完成**

### Phase C｜统一模块归属

目标：

- 回答每个 `dasheng-daily-*` 到底是主入口、底层模块，还是历史遗留

动作：

- 编制迁移表
- 明确保留、合并、退出主链、归档四种状态

状态：**已完成**

### Phase D｜统一执行入口

目标：

- 以后只从 `dasheng-media-sop` 进入

动作：

- 给总控 Skill 增加“阶段 -> 模块”映射
- 将旧 Skill 标注为 `legacy` 或 `internal module`
- 收口旧的 `outline / final` 入口

状态：**进行中**

### Phase E｜统一发布与复盘闭环

目标：

- 打通 `publish -> postmortem -> 知识库回写`

动作：

- 发布调度器统一化
- 接真实平台数据
- 复盘结果回写 L1 / 风格库 / 标题库 / 素材偏好库

状态：**后续重点**

## 四、执行优先级

1. 先收口主入口
2. 再收口旧模块归属
3. 再做发布层统一
4. 最后做复盘数据闭环

## 五、重构判断标准

当满足以下条件时，视为 `dasheng-daily` 体系完成重构：

- 用户以后只需记住一个入口：`dasheng-media-sop`
- 所有阶段都有单一语义、单一交付接口
- 旧技能全部被标注为：保留模块 / 历史遗留 / 退出主链
- `publish` 与 `postmortem` 可真实落地
