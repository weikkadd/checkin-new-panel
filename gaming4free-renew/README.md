# gaming4free 自动续期（GHA + WARP）

> 利用 GitHub Actions + Cloudflare WARP 出口 + seleniumbase UC mode 自动续期 gaming4free 服务器。
> 因为 WARP 是 Cloudflare 自家 IP，Turnstile 几乎必过。
> **支持多账号**、**TG 通知**、**自动恢复**。

## 🎯 原理对比

| 方案 | 出口 IP | Turnstile 通过率 | 费用 |
|---|---|---|---|
| VPS + playwright | 机房 IP（CF 黑名单） | ❌ 0% | VPS 月费 |
| **GHA + WARP** | CF 自家 IP | ✅ ~95% | **免费**（公开仓库） |

## ✨ 功能特性

- 🔗 **WARP 代理** — Cloudflare 自家 IP，过 Turnstile
- 🍪 **Cookie 注入** — 支持 Google OAuth 登录的站点
- 🖱️ **Selenium 真实点击** — 触发 wire:click + 广告播放
- 📺 **广告智能等待** — 检测 video ended/cooldown，不固定等
- ⏱️ **cooldown 检测** — 最可靠的成功判断
- 👥 **多账号支持** — matrix 策略，最多 3 账号串行跑
- 📱 **TG 通知** — 7 个通知点，北京时间，带账号标识
- 🔄 **自动恢复** — 异常自动重启最多 2 次
- 🛡️ **Cloudflare Turnstile 处理** — 多种点击方式

## 📁 文件结构

```
checkin-new-panel/
├── .github/workflows/
│   └── gaming4free.yml      # GitHub Actions 工作流（多账号 matrix）
├── gaming4free-renew/
│   ├── renew.py             # 续期主脚本
│   ├── requirements.txt     # Python 依赖
│   └── README.md            # 本文档
```

---

## 🚀 部署步骤（别人 fork 后照着做）

### 第 1 步：Fork 仓库

1. 访问 https://github.com/weikkadd/checkin-new-panel
2. 点右上角 **`Fork`** 按钮
3. 选择你的账号，fork 到自己的仓库

> ⚠️ **必须用公开仓库**（Public），私有仓库 GHA 每月只有 2000 分钟，不够用。

### 第 2 步：启用 GitHub Actions

1. 进入你 fork 的仓库
2. 点顶部 **`Actions`** tab
3. 如果提示 "Workflows aren't being run on this forked repository"，点 **`I understand my workflows, go ahead and enable them`**

### 第 3 步：配置 Secrets

进入你的仓库 → `Settings` → `Secrets and variables` → `Actions` → `New repository secret`

#### 账号 1（必填）

| Secret 名 | 说明 | 怎么获取 |
|---|---|---|
| `MC_USERNAME` | gaming4free 用户名 | 你登录用的用户名 |
| `GF_COOKIE` | gaming4free 的 cookie | 浏览器 F12 → Application → Cookies 复制 |
| `GF_SITE_URL` | 服务器控制台 URL | 登录后浏览器地址栏的 URL |
| `MC_PASSWORD` | 密码（可选） | 你的登录密码 |

#### 账号 2（可选，多账号）

| Secret 名 | 说明 |
|---|---|
| `MC_USERNAME_2` | 账号2 用户名 |
| `GF_COOKIE_2` | 账号2 的 cookie |
| `GF_SITE_URL_2` | 账号2 的服务器 URL |
| `MC_PASSWORD_2` | 账号2 密码（可选） |

#### 账号 3（可选）

| Secret 名 | 说明 |
|---|---|
| `MC_USERNAME_3` | 账号3 用户名 |
| `GF_COOKIE_3` | 账号3 的 cookie |
| `GF_SITE_URL_3` | 账号3 的服务器 URL |
| `MC_PASSWORD_3` | 账号3 密码（可选） |

#### TG 通知（可选，但推荐）

| Secret 名 | 说明 | 怎么获取 |
|---|---|---|
| `TG_BOT_TOKEN` | Telegram Bot Token | 找 @BotFather 创建 Bot |
| `TG_CHAT_ID` | 群组/用户 Chat ID | 给 Bot 发消息后访问 getUpdates 获取 |

### 第 4 步：获取 Cookie（关键步骤）

#### 4.1 登录 gaming4free

1. 浏览器打开 `https://control.gaming4free.net/`
2. 用 Google 登录到能看到 `+90 min` 按钮的页面

#### 4.2 复制 Cookie

**方法 A：浏览器开发者工具**

1. 按 **F12** 打开开发者工具
2. 切换到 **`Application`**（Chrome/Edge）或 **`存储`**（Firefox）
3. 左侧 **`Cookies`** → `https://control.gaming4free.net`
4. 把所有 cookie 按 `Name=Value; ` 格式拼接

**方法 B：Cookie-Editor 插件（推荐）**

- Chrome: https://chromewebstore.google.com/detail/cookie-editor/hlkenndednhfkekhfbcdfbcgmoabcnib
- Firefox: https://addons.mozilla.org/firefox/addon/cookie-editor/

装好后：
1. 在 gaming4free 页面点插件图标
2. 点 **`Export`** → **`Header String`**
3. 自动复制到剪贴板

#### 4.3 填到 GitHub Secret

- Name: `GF_COOKIE`
- Secret: 粘贴上面的 cookie 字符串

### 第 5 步：手动触发测试

1. 进入你 fork 的仓库 → `Actions` tab
2. 左侧选 **`gaming4free 自动续期`**
3. 点 **`Run workflow`** → 选 `main` 分支 → 点绿色按钮
4. 等待 5-15 分钟
5. 点进运行详情，下载 `screenshots-*` artifact 看截图

### 第 6 步：自动续期

workflow 默认 `cron: "13 */2 * * *"`（每 2 小时跑一次）。

想改频率？编辑 `.github/workflows/gaming4free.yml`：

```yaml
schedule:
  - cron: "13 */2 * * *"   # 每 2 小时（默认）
  # - cron: "13 */4 * * *" # 每 4 小时（省 GHA 分钟）
  # - cron: "13 */6 * * *" # 每 6 小时
```

---

## 📱 TG 通知示例

跑起来后你会收到这些通知（北京时间）：

```
🎮 gaming4free [账号1]
🚀 续期启动
⏰ 2026-07-07 16:35:25 (北京时间)
👤 用户: your_username
🌐 WARP: 已就绪

🎮 gaming4free [账号1]
📊 当前剩余时间
⏳ 25h 32m
🎯 上限: 46h

🎮 gaming4free [账号1]
✅ 续期成功 #1
⏰ 16:40:25 (北京)
⏳ 剩余: 25h 32m → 27h 1m
➕ 增加: 1h 29m
📊 累计: 1 次

🎮 gaming4free [账号1]
🏁 续期完成
⏰ 2026-07-07 17:10:00 (北京时间)
✅ 成功点击: 8 次
⏳ 最终剩余: 33h 30m
🎯 上限: 46h
```

---

## 🔧 配置参数

编辑 `gaming4free-renew/renew.py` 顶部：

```python
MAX_HOURS      = 46    # 续期上限 46 小时（gaming4free cap 48h，留 2h 缓冲）
ADD_MINUTES    = 90    # 每次点击 +90 分钟
COOLDOWN_SEC   = 285   # 冷却 4 分 45 秒
MAX_CLICKS     = 30    # 单次运行最大点击次数
```

---

## 🐛 故障排查

### 问题 1：Cookie 失效

**症状**：日志显示 `⚠️ cookie 注入后仍是登录页`

**解决**：重新复制 cookie 更新 `GF_COOKIE` Secret（cookie 有效期一般 7-30 天）

### 问题 2：找不到续期按钮

**症状**：日志显示 `❌ rt-btn-free 按钮不存在`

**解决**：
1. 下载 `screenshots-*` artifact 看截图
2. 确认 `GF_SITE_URL` 是服务器控制台 URL（不是登录页）
3. 正确格式：`https://control.gaming4free.net/server/xxx/console`

### 问题 3：Turnstile 过不了

**症状**：日志显示 `⚠️ Turnstile 90s 未通过`

**解决**：
- WARP IP 偶尔被识别，多重跑几次
- 或加大 `TURNSTILE_WAIT`（renew.py 第 40 行）

### 问题 4：续期失败率高

**症状**：`⚠️ 时间未增加，判定失败`

**解决**：
- 这是正常现象（成功率约 50-70%）
- cron 每 2h 跑一次，完全够维持 46h 上限
- 不用担心，会自动重试

### 问题 5：GHA 超时

**症状**：`Error: The operation was canceled`

**解决**：
- workflow 已设置 `timeout-minutes: 120`
- 如果还超时，降低 `MAX_CLICKS` 或减少账号数

---

## ❓ 常见问题

### Q: 必须用公开仓库吗？

**A**: 是的。私有仓库 GHA 每月只有 2000 分钟，3 账号每 2h 跑约需 3600 分钟/月，不够用。公开仓库无限。

### Q: Cookie 多久过期？

**A**: 一般 7-30 天。建议每周更新一次。如果 TG 通知收到 `cookie 注入后仍是登录页`，就需要更新。

### Q: 可以加更多账号吗？

**A**: 可以。编辑 `.github/workflows/gaming4free.yml`：
```yaml
matrix:
  account: [1, 2, 3, 4, 5]  # 加到 5 个账号
```
然后添加对应的 `MC_USERNAME_4`、`GF_COOKIE_4` 等 Secret。

### Q: 会封号吗？

**A**: 不会。gaming4free 的 +90 min 按钮就是给用户点的，每 5 分钟点一次是正常使用频率。

### Q: GHA 会不会跑着跑着停了？

**A**: 不会。脚本有自动恢复机制，异常自动重启最多 2 次。

---

## 📞 技术支持

- 问题反馈：https://github.com/weikkadd/checkin-new-panel/issues
- 查看日志：仓库 → Actions → 点最新运行 → `运行续期脚本` 步骤
- 下载截图：运行详情页底部 → `screenshots-*` artifact

## 📄 License

MIT
