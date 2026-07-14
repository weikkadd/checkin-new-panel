# Gaming4Free 自动续期

> GitHub Actions + sing-box 代理 + SeleniumBase UC mode + Turnstile 验证 + 投票 API 续期。

## 📁 文件结构

```
checkin-gaming4/
├── .github/workflows/gaming4free.yml
├── gaming4free-renew/
│   ├── renew.py
│   └── README.md
```

## 🚀 部署步骤

### 1. 配置 Secrets

进入仓库 → `Settings` → `Secrets and variables` → `Actions` → `New repository secret`

| Secret 名 | 必填 | 说明 |
|---|---|---|
| `GAME4FREE_ACCOUNT` | ✅ | 格式：`服务器名,续期URL`（英文逗号分隔） |
| `PROXY_URL` | ✅ | sing-box 节点链接（tuic/vless/vmess/trojan/hysteria2/socks5） |
| `TG_BOT_TOKEN` | ❌ | Telegram Bot Token |
| `TG_CHAT_ID` | ❌ | Telegram Chat ID |

#### `GAME4FREE_ACCOUNT` 示例

```
我的服务器,https://control.gaming4free.net/server/247d3700/console
```

#### `PROXY_URL` 示例

```
tuic://uuid:password@host:port?insecure=1
```

复用其他续期仓库的同一个节点即可。

### 2. 手动触发测试

Actions → `Game4Free-Renew` → `Run workflow`

### 3. 自动续期

默认每天 UTC 01:00 自动运行。

## 📱 TG 通知示例

```
🎮Game4Free 续期通知
⏰运行时间: 2026-07-14 08:00:00
🖥️服务器: 我的服务器
🔢利用期限: 48:00:00
📊续期结果: ✅续期成功！
```
