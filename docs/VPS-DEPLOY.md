# VPS 部署详细教程

## 适用场景
有自己 VPS（1GB+ 内存）的用户，7x24 稳定运行，不休眠。

## 要求
- VPS 内存 ≥ 1GB（推荐 2GB+）
- 系统：Ubuntu 22.04 / Debian 12
- 已安装 Node.js 22+

---

## 第 1 步：SSH 连接 VPS

```bash
ssh root@你的VPS_IP -p 端口号
```

## 第 2 步：安装 Node.js 22 和 Git

```bash
curl -fsSL https://deb.nodesource.com/setup_22.x | bash -
apt install -y nodejs git
```

验证：
```bash
node -v   # 应显示 v22.x.x
npm -v    # 应显示 10.x.x
git --version
```

## 第 3 步：克隆代码

```bash
cd /home
git clone https://github.com/weikkadd/checkin-new-panel.git
cd checkin-new-panel
```

## 第 4 步：安装依赖

```bash
npm install
```

## 第 5 步：安装 Playwright + Chromium

```bash
npx playwright install chromium
npx playwright install-deps chromium
```

> 这会下载 Chromium（约 150MB）和系统依赖库。

## 第 6 步：配置环境变量

```bash
cat > .env << 'EOF'
DATABASE_URL=mysql://oNCXBbppX5TiGz2.root:S1R54YaG5GUEt4GZ@gateway01.ap-southeast-1.prod.aws.tidbcloud.com:4000/checkin_db?ssl=%7B%22rejectUnauthorized%22%3Atrue%7D
TG_BOT_TOKEN=8644834310:AAE6rSjWQnleoVoK591aECEZss60aMqS5dw
TG_CHAT_ID=-1003957460883
AUTH_TOKEN=simple-token-ok
PORT=3000
GLOBAL_CRON=0 0 */6 * * *
EOF
```

## 第 7 步：编译 TypeScript

```bash
npx tsc
```

> 如果没有报错，说明编译成功。

## 第 8 步：测试运行

```bash
node dist/server/index.js
```

应该看到：
```
[DB] 连接 TiDB: ...
[DB] ✅ 数据库连接测试成功
全局签到定时任务已启动
服务运行在端口: 3000
```

按 `Ctrl+C` 停止。

## 第 9 步：安装 pm2 守护进程

```bash
npm install -g pm2
```

## 第 10 步：用 pm2 启动服务

```bash
cd /home/checkin-new-panel
pm2 start dist/server/index.js --name checkin-api
```

验证：
```bash
pm2 list
```

应该看到 `checkin-api` 状态 `online`。

## 第 11 步：测试服务

```bash
curl -s http://localhost:3000/ping
```

应该返回 `ok`。

## 第 12 步：设置开机自启

```bash
pm2 save
pm2 startup
```

> `pm2 startup` 会输出一条命令（类似 `sudo env PATH=... pm2 startup ...`），**复制并执行那条命令**。

## 第 13 步（可选）：配置 Nginx 反向代理 + HTTPS

```bash
apt install -y nginx certbot python3-certbot-nginx
```

创建 Nginx 配置：
```bash
cat > /etc/nginx/sites-available/checkin-api << 'EOF'
server {
    listen 80;
    server_name your-domain.com;  # 换成你的域名或 IP

    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }
}
EOF
```

启用配置：
```bash
ln -s /etc/nginx/sites-available/checkin-api /etc/nginx/sites-enabled/
nginx -t
systemctl reload nginx
```

配置 HTTPS（如果有域名）：
```bash
certbot --nginx -d your-domain.com
```

## 第 14 步（可选）：配置 UptimeRobot 监控

虽然 VPS 不会休眠，但可以用 UptimeRobot 监控服务是否在线：
- URL: `http://你的VPS_IP:3000/ping`
- Interval: 5 minutes

---

## 常用管理命令

```bash
# 重启服务
pm2 restart checkin-api

# 停止服务
pm2 stop checkin-api

# 查看日志
pm2 logs checkin-api

# 更新代码
cd /home/checkin-new-panel
git pull origin main
npm install
npx tsc
pm2 restart checkin-api
```

---

## 注意事项

1. **内存要求**：Playwright + Chromium 至少需要 500MB 内存，建议 VPS 内存 ≥ 1GB
2. **防火墙**：确保 3000 端口（或 Nginx 的 80/443 端口）已开放
3. **Cookie 更新**：gaming4free 的 Cookie 一般 7-14 天过期，过期后需要重新提取并更新
4. **更新代码**：每次 `git pull` 后需要重新 `npx tsc` 编译 + `pm2 restart`
