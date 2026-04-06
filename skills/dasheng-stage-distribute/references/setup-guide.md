# 平台发布认证配置指南

首次运行 distribute 阶段前，各平台需要完成一次性配置。完成后凭证持久化，后续无需重复操作。

---

## 1. 微信公众号（wechat-multi-publisher）

**认证方式**：API 凭证（AppID + AppSecret）

**配置步骤**：
1. 登录微信公众号后台：https://mp.weixin.qq.com
2. 左侧菜单 → 设置 → 开发者设置 → 查看 AppID 和 AppSecret
3. 配置环境变量：
   ```bash
   export WECHAT_APP_ID="wx_your_appid"
   export WECHAT_APP_SECRET="your_appsecret"
   export WECHAT_AUTHOR="你的署名"
   
   # 或写入 ~/.openclaw/dasheng.env：
   echo 'WECHAT_APP_ID=wx_your_appid' >> ~/.openclaw/dasheng.env
   echo 'WECHAT_APP_SECRET=your_appsecret' >> ~/.openclaw/dasheng.env
   ```
4. 验证：
   ```bash
   cd ~/.openclaw/skills/baoyu-post-to-wechat
   npx -y bun scripts/check-permissions.ts
   ```

**注意**：微信 API 只能保存草稿，**不能自动发布**。草稿需要到微信后台手动发布。

---

## 2. 微博（weibo-manager）

**认证方式**：Cookie（浏览器 Session）

**配置步骤**：
1. 在 Chrome 中登录 weibo.com
2. 安装 Cookie Editor 扩展（或用开发者工具）
3. 导出 weibo.com 的所有 Cookie 为 JSON
4. 保存到：`~/.openclaw/skills/weibo-manager/cookies.json`
5. 配置飞书审批渠道：
   ```bash
   export DASHENG_FEISHU_CHAT_ID="oc_your_chat_id"
   ```
6. 验证（手动运行一次测试请求）：
   ```bash
   cd ~/.openclaw/skills/weibo-manager
   node src/request_publish.js "${DASHENG_FEISHU_CHAT_ID}" "测试发布，请忽略" 
   ```

**注意**：Cookie 有效期约30天，过期后需重新导出。

---

## 3. X / Twitter（baoyu-post-to-x）

**认证方式**：Chrome 浏览器 Session（CDP 连接）

**配置步骤**：
1. 首次运行时会自动打开 Chrome 并导航到 x.com
2. 在浏览器中手动登录 X 账号
3. 登录状态会被 bun 脚本持久化
4. 后续运行无需重新登录（除非 Session 过期）

**系统权限**（macOS）：
- 系统设置 → 隐私与安全 → 辅助功能 → 允许终端（或 iTerm2）

**验证**：
```bash
cd ~/.openclaw/skills/baoyu-post-to-x
npx -y bun scripts/x-browser.ts "测试推文，请忽略" --dry-run
```

---

## 4. 小红书（xiaohongshu-auto）

**认证方式**：浏览器 Session（OpenClaw 内置浏览器）

**配置步骤**：
1. 启动 OpenClaw 内置浏览器，打开 xiaohongshu.com
2. 手动登录小红书账号
3. Session 会自动保存到：`~/.openclaw/workspace/skills/xiaohongshu-auto/session.json`
4. 配置账号设置（可选）：
   ```json
   // ~/.openclaw/workspace/skills/xiaohongshu-auto/config.json
   {
     "daily_post_limit": 5,
     "min_delay_minutes": 5,
     "max_delay_minutes": 30,
     "account_name": "你的账号名"
   }
   ```

**注意**：
- 每日最多发5篇（平台硬限制）
- 账号需要达到一定活跃度才能发视频
- 新账号建议先手动发几篇，再使用自动发布

---

## 5. 抖音（douyin-upload-skill）

**认证方式**：OAuth 2.0

**配置步骤**：
1. 申请抖音开放平台开发者账号：https://open.douyin.com
2. 创建应用，获取 Client Key 和 Client Secret
3. 配置环境变量：
   ```bash
   export DOUYIN_CLIENT_KEY="your_client_key"
   export DOUYIN_CLIENT_SECRET="your_client_secret"
   export DOUYIN_REDIRECT_URI="http://localhost:3000/callback"
   
   # 可选（用于语音转字幕）：
   export DOUYIN_ASR_MODE="whisper-cpu"
   export DOUYIN_WHISPER_BIN="/usr/local/bin/whisper"
   ```
4. 首次授权：
   ```bash
   cd ~/.openclaw/skills/douyin-upload-skill
   node scripts/douyin.js doctor  # 先检查环境
   node scripts/douyin.js auth    # OAuth 授权流程
   ```

**注意**：
- 抖音 API 发布权限需要单独申请，审核可能需要数天
- 未获得发布权限时，视频会导出到"草稿箱"供手动发布（fallback 模式）

---

## 凭证检查脚本

在每次 distribute 阶段开始前，运行以下检查：

```bash
# 微信 API
echo "=== WeChat ===" && \
  [ -n "$WECHAT_APP_ID" ] && echo "✓ AppID 已配置" || echo "✗ AppID 未配置"

# 微博 Cookie
echo "=== Weibo ===" && \
  [ -f ~/.openclaw/skills/weibo-manager/cookies.json ] && \
  echo "✓ Cookie 文件存在" || echo "✗ Cookie 文件不存在"

# 抖音环境变量
echo "=== Douyin ===" && \
  [ -n "$DOUYIN_CLIENT_KEY" ] && echo "✓ Client Key 已配置" || echo "✗ Client Key 未配置"
```

---

## 常见问题

### Cookie 过期怎么办？
微博和小红书的 Cookie 有效期约30天。过期表现为发布返回"未登录"错误。
解决：重新登录对应平台，重新导出/刷新 Cookie。

### 抖音发布失败？
检查是否有发布权限：`node scripts/douyin.js doctor`
如果显示 "permission denied"，使用 fallback 模式（视频导出到草稿箱，手动发布）。

### 小红书被限流？
减少日发布量（每日 ≤3篇），增大发布间隔（15-30分钟），
避免在平台敏感时段（凌晨12点-6点）发布。
