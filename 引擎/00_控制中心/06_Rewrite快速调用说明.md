# Rewrite 快速调用说明

以后进入 `rewrite` 环节，你只需要给出这三个参数：

- `DNA`
- `渠道`
- `情绪`

如果没有特别说明，我默认使用：

- 输入稿件：当前已确认的 `04_标准初稿.md`
- 输出：`改写稿 + 标题池 + 改写说明 + 素材锚点清单 + manifest`
- 素材锚点：默认开启

## 一、你可以直接这样说

### 最简调用

`按鲁迅DNA + B站 + 热烈改写`

### 带平台细分

`按 lemon DNA + 小红书图文 + 欢乐改写`

`按 表舅 DNA + 微信公众号文章 + 平时 改写`

`按 硬核姬 DNA + 抖音视频 + 愤怒 改写`

## 二、参数映射

### DNA

- `standard-neutral`
- `biaoshu`
- `hardcore-ji`
- `luxun`
- `lemon`

### 渠道

- `微信公众号文章` -> `wechat_article`
- `微信视频号` / `微信视频` -> `wechat_video`
- `小红书图文` / `小红书笔记` -> `xiaohongshu_note`
- `小红书视频` -> `xiaohongshu_video`
- `抖音` / `抖音视频` -> `douyin_video`
- `B站` / `B站视频` -> `bilibili_video`
- `视频号` -> `video_account_video`
- `微博图文` / `微博笔记` -> `weibo_note`
- `微博视频` -> `weibo_video`
- `X图文` / `X文字` -> `x_note`
- `X视频` -> `x_video`

### 情绪

- `欢乐` -> `joy`
- `热烈` -> `hot`
- `平时` -> `normal`
- `冷淡` -> `cool`
- `愤怒` -> `angry`

## 三、默认原则

- 先服从渠道
- 再执行 DNA
- 最后叠加情绪
- 不改事实边界
- 不新增证据
- 需要补充内容时，用素材锚点标注

## 四、输出目录

日常输出统一放到：

`/Users/lichengyin/Desktop/自媒体创作临时交付/<日期>/04_rewrite/`
