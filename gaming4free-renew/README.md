# Gaming4Free 自动续期

GitHub Actions + SeleniumBase UC mode + Cloudflare Turnstile 验证。

面板地址：<https://control.gaming4free.net/>

## 文件结构

```
gaming4free-renew/
├── main.py           # 主脚本 (单文件, 无外部模块依赖)
├── requirements.txt  # Python 依赖
└── README.md         # 说明文档
```

## 部署步骤

### 1. 配置 Secrets

| Secret 名 | 必填 | 说明 |
|---|---|---|
| `GAME4FREE_RENEW_URL` | 单账号 | 续期页面 URL |
| `GAME4FREE_COOKIE` | 单账号 | Cookie 字符串 |
| `GAME4FREE_ACCOUNTS` | 多账号 | 每行 `名称\|\|\|URL\|\|\|Cookie` |
| `TG_BOT_TOKEN` | 否 | Telegram Bot Token |
| `TG_CHAT_ID` | 否 | Telegram Chat ID |

### 2. 获取 Cookie

1. 浏览器登录 <https://control.gaming4free.net>
2. F12 -> Application -> Cookies -> 复制全部 Cookie

### 3. 运行

```bash
xvfb-run --auto-servernum --server-args="-screen 0 1920x1080x24" python main.py
```

## 工作原理

1. CDP 方式注入 Cookie (绕过页面超时)
2. SeleniumBase UC mode 启动 Chrome
3. 三层续期策略: wire:id 精确调用 -> 通用组件遍历 -> JS 原生 click
4. 广告监测 + 模拟真人活跃
5. 刷新页面比对剩余时间验证

## License

MIT
