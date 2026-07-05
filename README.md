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

### 方式 1：Docker 部署（推荐）

适合有 Docker 环境的用户，一键部署。

```bash
# 1. 克隆代码
git clone https://github.com/weikkadd/checkin-new-panel.git
cd checkin-new-panel

# 2. 构建镜像
docker build -t checkin-new-panel .

# 3. 启动容器
docker run -d --name checkin-api -p 3000:3000 \
  -e DATABASE_URL="mysql://用户名:密码@主机:4000/数据库名?ssl=%7B%22rejectUnauthorized%22%3Atrue%7D" \
  -e TG_BOT_TOKEN="你的TG机器人Token" \
  -e TG_CHAT_ID="你的TG群ID" \
  -e AUTH_TOKEN="simple-token-ok" \
  -e PORT=3000 \
  -e GLOBAL_CRON="0 0 */6 * * *" \
  checkin-new-panel

# 4. 验证
docker logs checkin-api
curl -s http://localhost:3000/ping  # 应返回 ok
```

或者用 Docker Compose：

```yaml
# docker-compose.yml
version: '3'
services:
  checkin-api:
    build: .
    ports:
      - "3000:3000"
    environment:
      - DATABASE_URL=mysql://用户名:密码@主机:4000/数据库名?ssl=%7B%22rejectUnauthorized%22%3Atrue%7D
      - TG_BOT_TOKEN=你的TG机器人Token
      - TG_CHAT_ID=你的TG群ID
      - AUTH_TOKEN=simple-token-ok
      - PORT=3000
      - GLOBAL_CRON=0 0 */6 * * *
    restart: unless-stopped
```

```bash
docker-compose up -d
```

---

### 方式 2：VPS 部署（最稳定，需 1GB+ 内存）

适合有自己 VPS 的用户，7x24 稳定运行，不休眠。

```bash
# 1. SSH 连接 VPS
ssh root@你的VPS_IP -p 端口

# 2. 安装 Node.js 22 和 Git
curl -fsSL https://deb.nodesource.com/setup_22.x | bash -
apt install -y nodejs git

# 3. 克隆代码
cd /home
git clone https://github.com/weikkadd/checkin-new-panel.git
cd checkin-new-panel

# 4. 安装依赖
npm install
npx playwright install chromium
npx playwright install-deps chromium

# 5. 配置环境变量
cat > .env << 'EOF'
DATABASE_URL=mysql://用户名:密码@主机:4000/数据库名?ssl=%7B%22rejectUnauthorized%22%3Atrue%7D
TG_BOT_TOKEN=你的TG机器人Token
TG_CHAT_ID=你的TG群ID
AUTH_TOKEN=simple-token-ok
PORT=3000
GLOBAL_CRON=0 0 */6 * * *
EOF

# 6. 编译
npx tsc

# 7. 测试运行
node dist/server/index.js
# 看到 [DB] ✅ 数据库连接测试成功 后按 Ctrl+C 停止

# 8. 用 pm2 守护进程（7x24 运行）
npm install -g pm2
pm2 start dist/server/index.js --name checkin-api
pm2 save
pm2 startup  # 设置开机自启（按提示执行输出的命令）

# 9. 验证
curl -s http://localhost:3000/ping  # 应返回 ok
```

---

### 方式 3：zo.computer 部署（免费 4GB）

适合没有 VPS 的用户，免费 4GB 内存，但会休眠（需配合 CF Worker 保活）。

```bash
# 1. 注册 zo.computer，打开终端

# 2. 克隆代码
cd /home/workspace
git clone https://github.com/weikkadd/checkin-new-panel.git
cd checkin-new-panel

# 3. 安装依赖
npm install
npx playwright install chromium
npx playwright install-deps chromium

# 4. 配置环境变量
cat > .env << 'EOF'
DATABASE_URL=mysql://用户名:密码@主机:4000/数据库名?ssl=%7B%22rejectUnauthorized%22%3Atrue%7D
TG_BOT_TOKEN=你的TG机器人Token
TG_CHAT_ID=你的TG群ID
AUTH_TOKEN=simple-token-ok
PORT=3000
GLOBAL_CRON=0 0 */6 * * *
EOF

# 5. 编译并启动
npx tsc
node dist/server/index.js

# 6. 用 supervisord 守护进程
# zo.computer 自带 supervisord，配置文件在 /etc/zo/supervisord-user.conf
supervisorctl -c /etc/zo/supervisord-user.conf restart checkin-api
```

> **注意**：zo.computer 免费版会休眠，必须配合 CF Worker 保活（见方式 7）。

---

### 方式 4：DCDeploy 部署（付费，按量计费）

印度 PaaS 平台，不休眠，按量计费（DCD-3 1GB ~$4/月）。

1. 注册 https://dash.dcdeploy.com
2. 开通「优点」套餐
3. 点「创造环境」，配置：
   - 名称：`checkin-api`
   - 来源：GitHub
   - 存储库：`https://github.com/weikkadd/checkin-new-panel`
   - 参考资料：`main`
   - Dockerfile Name：`./Dockerfile`
   - 端口：`3000`
   - 机器类型：DCD-3（1GB）或 DCD-4（2GB）
4. 添加环境变量（见下方环境变量说明）
5. 点 CONTINUE 部署

---

### 方式 5：HuggingFace Spaces 部署（免费 16GB）

免费 16GB 内存，48 小时不访问才休眠。

1. 打开 https://huggingface.co/new-space
2. 配置：Space name = `checkin-api`，SDK = Docker，Hardware = CPU basic (16GB)，Public
3. 推送代码：

```bash
git clone https://github.com/weikkadd/checkin-new-panel.git
cd checkin-new-panel
git remote add hf https://用户名:Token@huggingface.co/spaces/用户名/checkin-api
git push hf main --force
```

4. 在 Space Settings → Variables 里添加环境变量（注意 PORT = 7860）
5. 配置 UptimeRobot 每 5 分钟 ping `/ping` 防休眠

> **注意**：HuggingFace 可能检测到 Playwright 并暂停 Space。

---

### 方式 6：Cloudflare Pages 前端部署

前端面板部署在 Cloudflare Pages，连接后端 API。

1. Cloudflare Dashboard → Workers & Pages → Create Pages → Connect to Git
2. 选择仓库 `weikkadd/checkin-new-panel`
3. 配置：
   - Build command：`cd client && npm install && npm run build`
   - Build output directory：`client/dist`
4. 在 Settings → Environment variables 里添加：
   - `VITE_API_URL` = `https://你的后端地址/trpc`
5. 部署后访问 `https://checkin-new-panel.pages.dev`

---

### 方式 7：CF Worker 保活服务

防止 zo.computer / HuggingFace Spaces 休眠。

1. Cloudflare Dashboard → Workers & Pages → Create Worker → 名称 `checkin-keepalive`
2. 粘贴代码（见 `scripts/cf-worker-keepalive.js`）
3. 添加环境变量：
   - `PING_URL` = `https://你的后端地址/trpc/task.getAll?batch=1&input=%7B%220%22%3A%7B%22json%22%3Anull%7D%7D`
   - `TG_BOT_TOKEN` = `你的TG机器人Token`
   - `TG_CHAT_ID` = `你的TG群ID`
4. 添加 Cron Trigger：`*/3 * * * *`（每 3 分钟执行）

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
