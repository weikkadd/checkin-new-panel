# Checkin New Panel 🎮

gaming4free 自动续期 — 基于 GitHub Actions + Cloudflare WARP + Seleniumbase UC Mode。

> ✨ **推荐使用 GHA 方案**（免费、稳定、过 Turnstile），详见下方 [gaming4free 自动续期](#gaming4free-自动续期gha--warp)。

---

## gaming4free 自动续期（GHA + WARP）

利用 GitHub Actions + Cloudflare WARP 出口 + seleniumbase UC mode 自动续期 gaming4free 服务器。

### 🎯 为什么用 GHA + WARP？

| 方案 | 出口 IP | Turnstile 通过率 | 费用 |
|---|---|---|---|
| VPS + playwright | 机房 IP（CF 黑名单） | ❌ 0% | VPS 月费 |
| **GHA + WARP** | CF 自家 IP | ✅ ~95% | **免费**（公开仓库） |

### ✨ 功能特性

- 🔗 **WARP 代理** — Cloudflare 自家 IP，过 Turnstile
- 🍪 **Cookie 注入** — 支持 Google OAuth 登录的站点
- 🖱️ **Selenium 真实点击** — 触发 wire:click + 广告播放
- 📺 **广告智能等待** — 检测 video ended/cooldown，不固定等
- ⏱️ **cooldown 检测** — 最可靠的成功判断
- 👥 **多账号支持** — matrix 策略，最多 3 账号串行跑
- 📱 **TG 通知** — 7 个通知点，北京时间，带账号标识
- 🔄 **自动恢复** — 异常自动重启最多 2 次
- 🛡️ **Cloudflare Turnstile 处理** — 多种点击方式

### 📁 文件位置

- `.github/workflows/gaming4free.yml` — GitHub Actions 工作流（多账号 matrix）
- `gaming4free-renew/renew.py` — 续期主脚本
- `gaming4free-renew/requirements.txt` — Python 依赖
- [`gaming4free-renew/README.md`](gaming4free-renew/README.md) — **完整部署文档**

### 🚀 快速部署

1. **Fork 本仓库**（必须公开仓库，私有仓库 GHA 分钟数不够）
2. **配置 Secrets**（仓库 → Settings → Secrets and variables → Actions）：
   - `MC_USERNAME` — gaming4free 用户名
   - `GF_COOKIE` — gaming4free 的 cookie
   - `GF_SITE_URL` — 服务器控制台 URL
   - `TG_BOT_TOKEN` / `TG_CHAT_ID` — TG 通知（可选，推荐）
3. **手动触发测试**：Actions → `gaming4free 自动续期` → Run workflow
4. **自动续期**：默认每 2 小时跑一次

> 详细步骤见 👉 [`gaming4free-renew/README.md`](gaming4free-renew/README.md)

---

## 📄 License

MIT

## 👤 Author

weikkadd (weimei)
