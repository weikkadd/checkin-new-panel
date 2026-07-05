---
title: Checkin New Panel
emoji: 🎮
colorFrom: indigo
colorTo: purple
sdk: docker
app_port: 7860
pinned: false
license: mit
---

# Checkin New Panel 🎮

自动化签到续期管理平台 - 支持 gaming4free / host2play / katabump 等多个免费服务器自动续期。

## ✨ 功能特性

- 🔗 **链接签到**：fetch 模式，快速签到（适合 host2play 等）
- 🌐 **浏览器访问**：Playwright 模式，点击按钮续期（适合 gaming4free）
- 🍪 **Cookie 注入**：跳过登录，直接用 Cookie 访问
- 🔐 **账号密码登录**：自动填表 + 提交
- 🔁 **循环点击**：gaming4free +90min 按钮专用，4 分钟冷却循环点击，上限 45h
- 🤖 **Turnstile 验证**：增强反检测 + 真实鼠标点击 + 11 项指纹伪造
- ⏰ **Cron 定时**：每 6 小时自动续期，支持每任务独立 Cron
- 🔒 **任务级锁**：防止同一任务并发执行
- 📱 **TG 通知**：续期结果发到 Telegram 群，带功能按钮
- 🖥️ **Web 面板**：可视化任务管理（Cloudflare Pages 前端）
- 📊 **日志记录**：每次执行结果 + 截图 + 错误信息

## 🕵️ 引擎特性

- **反爬虫伪装**：5 种 UA 池 + 5 种视口 + 隐藏 navigator.webdriver + 伪造 plugins/languages/platform/chrome 对象
- **自动填表**：13+ 种用户名选择器 + 7+ 种密码选择器 + 14+ 种登录按钮选择器，覆盖绝大多数站点
- **结果检测**：中英文关键词识别（"密码错误"/"login failed" 等）
- **失败截图**：执行异常时也保存截图到数据库
- **自定义脚本**：支持 task.customScript 在浏览器上下文执行任意 JS
- **自动通知**：成功/失败都发送 Telegram 通知
- **完整日志**：taskId + taskName + success + errorMsg + duration + screenshot + createdAt

## 🏗️ 技术栈

- **后端**：Node.js 22 + Express + tRPC + Drizzle ORM + MySQL/TiDB
- **前端**：React 18 + Tailwind + tRPC client
- **浏览器自动化**：Playwright + playwright-extra + stealth
- **定时任务**：cron 库
- **通知**：Telegram Bot API

---

## 📦 部署教程

支持 7 种部署方式，详细教程请查看 👉 [**完整部署指南**](docs/DEPLOY-GUIDE.md)

| 方式 | 平台 | 费用 | 内存 | 说明 |
|------|------|------|------|------|
| 1 | [Docker](docs/DEPLOY-GUIDE.md#方式-1vps-部署最稳定推荐) | 自费 | 1GB+ | 推荐，一键部署 |
| 2 | [VPS](docs/DEPLOY-GUIDE.md#方式-2docker-部署) | 自费 | 1GB+ | 最稳定，7x24 运行 |
| 3 | [zo.computer](docs/DEPLOY-GUIDE.md#方式-3zocomputer-部署免费) | 免费 | 4GB | 需 CF Worker 保活 |
| 4 | [DCDeploy](docs/DEPLOY-GUIDE.md#方式-4dcdeploy-部署付费按量计费) | ~$4/月 | 1GB+ | 按量计费 |
| 5 | [HuggingFace Spaces](docs/DEPLOY-GUIDE.md#方式-5huggingface-spaces-部署免费-16gb) | 免费 | 16GB | 48h 休眠 |
| 6 | [Cloudflare Pages](docs/DEPLOY-GUIDE.md#方式-6cloudflare-pages-前端部署) | 免费 | - | 前端面板 |
| 7 | [CF Worker 保活](docs/DEPLOY-GUIDE.md#方式-7cf-worker-保活服务) | 免费 | - | 防休眠 |

> 点击上方链接查看对应部署方式的详细步骤。

---

## ⚙️ 环境变量

### 必需

| 变量 | 说明 | 示例 |
|------|------|------|
| `DATABASE_URL` | TiDB/MySQL 数据库连接串 | `mysql://user:pass@host:4000/db?ssl=...` |
| `AUTH_TOKEN` | API 鉴权 token | `simple-token-ok` |

### 可选

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `TG_BOT_TOKEN` | Telegram Bot Token | - |
| `TG_CHAT_ID` | Telegram Chat ID | - |
| `PORT` | 服务端口 | `3000`（HuggingFace 用 `7860`） |
| `GLOBAL_CRON` | 全局 Cron 表达式 | `0 0 */6 * * *` |
| `TG_API_PROXY` | TG API 代理 | `https://api.telegram.org` |

## 🗄️ 数据库表结构

### tasks 表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | int | 主键 |
| name | varchar | 任务名称 |
| url | text | 站点地址 |
| taskType | varchar | 任务类型：link/login/cookie/browser |
| renewButtonText | varchar | 续期按钮文字（如 +90 min）|
| cookies | text | 登录 Cookie |
| customScript | text | 自定义脚本（LOOP_MODE 等）|
| cronExpr | varchar | 独立 Cron 表达式 |
| execMode | int | 执行模式：1=自动+手动, 2=仅手动, 3=仅自动 |
| enabled | boolean | 是否启用 |

### customScript 配置示例

#### gaming4free 循环点击模式

```
LOOP_MODE:1
COOLDOWN_SEC:240
CAP_HOURS:45
MAX_CLICKS:35
```

#### 成功关键词

```
SUCCESS_KEYWORD:续期成功|renewed|已续期|Renew server
```

## 🎯 任务类型说明

### 🔗 link（链接签到）
- 仅访问 URL，用 fetch
- 最快最省资源
- 适合 host2play / hax 等

### 🌐 browser（浏览器访问）
- Playwright 打开页面 + 点击按钮
- 可选循环点击模式
- 适合 gaming4free（+90 min 按钮）

### 🍪 cookie（Cookie 注入）
- Playwright + Cookie 跳过登录
- 适合 Discord/Google OAuth 站点

### 🔐 login（账号密码登录）
- Playwright 自动填表 + 提交
- 适合普通登录站点

## 🔧 管理命令

### pm2（VPS）

```bash
pm2 start dist/server/index.js --name checkin-api   # 启动
pm2 restart checkin-api                               # 重启
pm2 logs checkin-api                                  # 看日志
pm2 list                                              # 看状态
```

### supervisord（zo.computer）

```bash
supervisorctl -c /etc/zo/supervisord-user.conf restart checkin-api   # 重启
supervisorctl -c /etc/zo/supervisord-user.conf status                # 看状态
tail -f /dev/shm/checkin-api.log                                     # 看日志
```

### Docker

```bash
docker logs checkin-api          # 看日志
docker restart checkin-api       # 重启
docker stop checkin-api          # 停止
```

### 更新代码

```bash
cd /项目目录
git pull origin main
npm install
npx tsc
# 然后重启服务（pm2 restart / supervisorctl restart / docker restart）
```

### API 接口

```bash
# 健康检查
curl http://localhost:3000/ping

# 触发任务
curl -X POST http://localhost:3000/trpc/task.runNow?batch=1 \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer simple-token-ok" \
  -d '{"0":{"json":{"taskId":1}}}'

# 查看任务日志
curl "http://localhost:3000/trpc/task.getLogs?input=%7B%22json%22%3A%7B%22taskId%22%3A1%2C%22limit%22%3A5%7D%7D" \
  -H "Authorization: Bearer simple-token-ok"
```

## 📱 TG 通知功能

- ✅ 续期成功通知（带剩余时间）
- ❌ 续期失败告警
- 🔘 群内按钮：自动续期 / 手动签到 / 测试通知 / 查看日志 / 编辑任务 / 打开面板

## 📄 License

MIT

## 👤 Author

weikkadd (weimei)
