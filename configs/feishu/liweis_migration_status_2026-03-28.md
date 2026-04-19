# 飞书机器人迁移状态：李维斯

- 日期：`2026-03-28`
- 旧应用：`贾维斯` / `cli_a93a0c3e72789bd4`
- 新应用：`李维斯` / `cli_a94d22306138dbc2`

## 已完成

- 已创建企业自建应用 `李维斯`
- 已确认旧应用与新应用的基本映射关系
- 已抓取旧应用机器人菜单与事件配置
- 已把本地脚本改为统一从 `feishu_api.conf` 读取飞书凭证，后续只需要改一处配置

## 已固化文件

- 机器人与事件配置：`/Volumes/PSSD/Projects/公众号文章/configs/feishu/liweis_bot_config.json`
- 现有最小权限包：`/Users/lichengyin/clawd/feishu-permissions.json`
- 主配置文件：`/Users/lichengyin/clawd/configs/feishu_api.conf`

## 当前阻塞

- 新应用凭证已经可用，但开放平台权限未补齐，当前阻塞在两类核心能力：
  - 发群消息：缺少 `im:message:send` / `im:message` / `im:message:send_as_bot`
  - 建文档与协作写入：缺少 `docx:document` / `docx:document:create`
- 如需继续复制旧机器人菜单、事件与完整权限集，仍然需要一个可操作的 `open.feishu.cn` 企业版浏览器会话。

## 切换范围

当前已经去除了以下脚本中的硬编码飞书凭证，后续切换只需要更新 `feishu_api.conf`：

- `/Users/lichengyin/clawd/scripts/dasheng_skill.py`
- `/Users/lichengyin/clawd/scripts/dasheng_skill_v2.py`
- `/Users/lichengyin/clawd/scripts/dasheng_skill_v3.py`
- `/Users/lichengyin/clawd/scripts/dasheng_skill_v4.py`
- `/Users/lichengyin/clawd/scripts/dasheng_skill_v5.py`
- `/Users/lichengyin/clawd/scripts/dasheng_skill_v6.py`
- `/Users/lichengyin/clawd/scripts/dasheng_skill_v7.py`
- `/Users/lichengyin/clawd/scripts/dasheng_xuanti.py`
- `/Users/lichengyin/clawd/scripts/daily_xuant.sh`

## 下一步

1. 在飞书开放平台给 `李维斯` 开通消息与文档权限
2. 发布新应用版本使权限生效
3. 用新应用重跑发消息 / 建文档 / 发群提醒验证
4. 继续迁移旧机器人的菜单、事件与完整权限集


## 2026-03-28 运行验证结果

- 本地运行凭证已切换到新应用：`cli_a94d22306138dbc2`
- 鉴权验证通过：`tenant_access_token/internal` 返回 `code=0`
- 发群消息验证失败：缺少权限 `im:message:send` / `im:message` / `im:message:send_as_bot`
- 建文档验证失败：缺少权限 `docx:document` / `docx:document:create`

### 直接开通链接

- 消息权限：`https://open.feishu.cn/app/cli_a94d22306138dbc2/auth?q=im:message:send,im:message,im:message:send_as_bot&op_from=openapi&token_type=tenant`
- 文档权限：`https://open.feishu.cn/app/cli_a94d22306138dbc2/auth?q=docx:document,docx:document:create&op_from=openapi&token_type=tenant`

### 结论

新应用的 `APP_ID` / `APP_SECRET` 已正式切换成功，但因为开放平台权限尚未补齐，当前还不能替代旧机器人执行发群消息、建文档、写协作文档等工作流动作。


## 2026-03-28 第二次迁移进展

- 新应用文档能力验证成功：`https://ccnokd2fmz4u.feishu.cn/docx/CIz3dVLpoosBFxxMpeTcboarnhd`
- 已在开放平台中为 `李维斯` 开通并发布以下能力：
  - `docx:document`
  - `docx:document:create`
  - `im:message`
  - `im:message:send_as_bot`
  - `im:message.p2p_msg:readonly`
  - `im:chat`
  - `im:chat.members:write_only`
- 已将事件订阅方式切换为“使用长连接接收事件”
- 已添加并发布以下事件：
  - `im.chat.access_event.bot_p2p_chat_entered_v1`
  - `im.message.receive_v1`
- 已创建并发布版本：`1.0.2`

### 当前剩余阻塞

- 发群消息不再是权限问题，而是群成员关系问题：机器人 `李维斯` 当前不在目标群 `oc_975d43c5704bf8c755bb9e32bf7c3922` 中
- 通过 OpenAPI 的 `me_join` 尝试自动入群时，返回 `232008`：该群当前不支持这种自加入方式
- 机器人自定义菜单仍未完整迁移，当前只验证了 UI 可编辑并开始录入，尚未形成完整五组菜单树并保存发布

### 建议动作

1. 先在飞书客户端中把 `李维斯` 手动拉入目标群
2. 我随后立即重跑发群消息验证
3. 再完成机器人自定义菜单的完整迁移与发布

## 2026-03-28 第三次迁移进展（完成）

- 已通过开放平台页面内接口，成功把旧机器人菜单结构完整迁移到 `李维斯`
- 菜单配置已写入并回读验证成功，当前保存结构为 5 组主菜单：
  - `/status`
  - `压缩`：`/stop`、`/new`、`/compact`
  - `汇报进度`
  - `操作`：`将以上的工作流总结成skill，并放入库，进行命名，供以后类似工作流调用`、`将上述对话写入日志记录，并将重要事项写入memory`
  - `自媒体`：`采集话题：调用大圣skills采集过去24小时的素材`
- 菜单展示策略已成功保存为 `botMenuDisplayStrategy=3`
- 已新建并发布版本：`1.0.3`
- 发布结果状态：`已发布 / 审核结果=通过`
- 新应用群消息链路验证成功：
  - 目标群：`oc_975d43c5704bf8c755bb9e32bf7c3922`
  - 测试消息 ID：`om_x100b534fb7df20a0b48274094eac98a`
- 文档链路已保持可用：
  - 验证文档：[CIz3dVLpoosBFxxMpeTcboarnhd](https://ccnokd2fmz4u.feishu.cn/docx/CIz3dVLpoosBFxxMpeTcboarnhd)

### 当前结论

- `李维斯` 已可替代旧机器人 `贾维斯` 承接当前飞书消息、文档、事件订阅与自定义菜单工作流
- 主配置文件 `/Users/lichengyin/clawd/configs/feishu_api.conf` 已指向新应用，无需再回切旧凭证

### 建议后续动作

1. 后续所有飞书自动化默认使用 `李维斯`
2. 将旧机器人视为历史备份对象，不再继续追加新配置
3. 下一步可开始把前五个内容工作流环节的飞书文档创建、群通知、素材回填逻辑全部绑定到 `李维斯`

## 2026-03-28 第四次迁移进展（前五环节飞书同步）

- 已验证当前前五环节执行层可用：
  - `rewrite` 文档创建成功
  - `rewrite` 报告创建成功
  - 群消息通知成功
- 已新增推荐包装入口：
  - `/Volumes/PSSD/Projects/公众号文章/scripts/feishu_stage_sync.py`
- 包装入口会把同步摘要落到：
  - `skills/dasheng-daily-shared/runtime-data/runs/<run_id>/bridge/feishu-sync-summary.json`
  - `skills/dasheng-daily-shared/runtime-data/runs/<run_id>/bridge/feishu-sync-summary.md`

### 当前新增阻塞

- 共享目录日期文件夹 / 阶段文件夹创建仍被飞书权限卡住
- live 执行返回的缺失权限为：
  - `drive:drive`
  - `space:folder:create`
- 已额外申请：
  - `docx:document.block:convert`
  - `drive:drive`
  - `space:folder:create`
- 已创建并提交版本：`1.0.4`
- 当前状态：`企业管理员审核中`

### 当前判断

- 这不是本地代码阻塞，而是飞书企业侧权限审批阻塞
- 在 `1.0.4` 审核通过前：
  - 文档与群通知仍可继续跑
  - 但无法把文档自动归档进指定共享目录层级

## 2026-03-28 第五次迁移进展（审批通过并复跑成功）

- `1.0.4` 已审核通过并发布生效
- 已重新验证代表性 run：
  - `2026-03-28_074500`：`rewrite` 样本 `9/9` 全部完成
  - `2026-03-26_141800`：全流程样本 `19/19` 全部完成
- 当前已验证能力：
  - 共享目录日期文件夹创建
  - 五个阶段子目录创建
  - 阶段主文档 / 报告文档创建与写入
  - 群消息发送
  - Material 素材目录上传

### 本轮代码修复

- 已为飞书目录创建与文件上传加入瞬时错误重试
- 根因是飞书 `createFolder` / 上传接口会偶发返回 `500 + 1061001 unknown error`
- 通过重试后，全流程样本已恢复稳定
