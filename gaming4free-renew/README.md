# Gaming4Free 自动续期（GHA + GOST 代理 + Turnstile）

> 利用 GitHub Actions + GOST 代理 + SeleniumBase UC mode 自动续期 gaming4free 服务器。
> 通过 Turnstile 验证 + 投票 API 续期，每次 +90 分钟，上限 48 小时。
> **支持多账号**、**多代理交替**、**TG 通知**。

## ✨ 功能特性

- 🔗 **GOST 代理** — 支持多代理交替使用，避免 IP 被风控
- 🛡️ **Cloudflare Turnstile 处理** — 坐标点击 + token 监听 + 无感盾支持
- 📤 **投票 API 续期** — 直接调用 API 提交，成功率高
- 👥 **多账号支持** — 多服务器批量续期
- 🔄 **多轮续期** — 自动循环续期直到 48 小时上限
- 📱 **TG 通知** — 统一 emoji 格式

## 📁 文件结构

```
checkin-gaming4/
├── .github/workflows/
│   └── gaming4free.yml      # GitHub Actions 工作流
├── gaming4free-renew/
│   ├── renew.py             # 续期主脚本
│   ├── requirements.txt     # Python 依赖
│   └── README.md            # 本文档
```

---

## 🚀 部署步骤

### 第 1 步：注册新账号

> ⚠️ 如果之前的账号被封了，需要重新注册一个新账号。

1. 打开 https://control.gaming4free.net/
2. 用 Google 账号登录注册
3. 添加你的 Minecraft 服务器
4. 进入服务器详情页

### 第 2 步：获取续期 URL

1. 登录后进入你的服务器页面
2. 找到 **Vote** 按钮
3. 点击 Vote，复制浏览器地址栏的 URL
4. URL 格式：`https://control.gaming4free.net/server/xxxx/vote`

### 第 3 步：配置 Secrets

进入仓库 → `Settings` → `Secrets and variables` → `Actions` → `New repository secret`

#### `GAME4FREE_ACCOUNT`（必填）

格式：`服务器名,续期URL`（每行一个账号）

```
我的服务器1,https://control.gaming4free.net/server/abc123/vote
我的服务器2,https://control.gaming4free.net/server/def456/vote
```

#### `GAME4FREE_PROXY`（必填）

格式：`代理名,代理URL`（每行一个，建议配 2 条交替使用）

```
代理1,socks5://user:pass@host:port
代理2,http://host:port
```

支持格式：
- `socks5://host:port`
- `socks5://user:pass@host:port`
- `http://host:port`
- `http://user:pass@host:port`

#### `TG_BOT`（可选，推荐）

格式：`chat_id,bot_token`（逗号分隔，没有空格）

```
123456789,7890123456:ABCdefGHIjklMNOpqrsTUVwxyz
```

- `chat_id` = 你的 Telegram Chat ID
- `bot_token` = 你的 Telegram Bot Token

### 第 4 步：手动触发测试

1. 进入仓库 → `Actions` tab
2. 左侧选 **`Game4Free-Renew`**
3. 点 **`Run workflow`** → 选 `main` 分支 → 点绿色按钮
4. 等待 5-15 分钟
5. 点进运行详情看日志

### 第 5 步：自动续期

workflow 默认每天 UTC 01:00 自动运行。

想改频率？编辑 `.github/workflows/gaming4free.yml`：

```yaml
schedule:
  - cron: "0 1 * * *"      # 每天 UTC 01:00（默认）
  # - cron: "0 */6 * * *"  # 每 6 小时
  # - cron: "0 */2 * * *"  # 每 2 小时
```

---

## 📱 TG 通知示例

```
🎮Game4Free 续期通知
⏰运行时间: 2026-07-14 08:00:00
🖥️服务器: 我的服务器1
🔢利用期限: 48:00:00
📊续期结果: ✅续期成功！
```

---

## 🔧 配置参数

编辑 `gaming4free-renew/renew.py` 顶部：

```python
TARGET_SECONDS = 48 * 3600  # 48小时目标上限
```

---

## 🐛 故障排查

### 问题 1：Turnstile 过不了

**症状**：日志显示 `❌ 人机验证超时`

**解决**：
- 换代理 IP，住宅 IP 通过率高
- 多跑几次，Turnstile 有随机性

### 问题 2：续期失败率高

**症状**：`❌ 续期失败，接口提示`

**解决**：
- 检查续期 URL 是否正确
- 检查代理是否能访问 gaming4free.net
- 可能是冷却时间未到（每次续期间隔约 5 分钟）

### 问题 3：GHA 超时

**症状**：`Error: The operation was canceled`

**解决**：
- 减少账号数量
- 降低 TARGET_SECONDS 上限

### 问题 4：代理连接失败

**症状**：`❌ GOST 启动失败`

**解决**：
- 检查代理 URL 格式是否正确
- 检查代理是否可用
- 换一个代理试试

---

## ❓ 常见问题

### Q: 账号被封了怎么办？

**A**: 重新注册一个新账号，更新 `GAME4FREE_ACCOUNT` Secret 里的续期 URL。

### Q: 可以加更多账号吗？

**A**: 可以。在 `GAME4FREE_ACCOUNT` Secret 里每行加一个账号即可。

### Q: 需要配置 Cookie 吗？

**A**: 不需要。新版脚本通过 Vote API 续期，不需要登录 Cookie。

### Q: 代理必须配 2 条吗？

**A**: 不是必须，但建议配 2 条交替使用，避免单条代理 IP 被风控。

---

## 📞 技术支持

- 问题反馈：https://github.com/weikkadd/checkin-gaming4/issues
- 查看日志：仓库 → Actions → 点最新运行 → `运行续期脚本` 步骤
- 下载截图：运行详情页底部 → `debug-screenshots` artifact

## 📄 License

MIT
