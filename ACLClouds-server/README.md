# AclClouds 卡卡项目 自动续期

> GitHub Actions + Playwright + Cookie 注入 + 自动续期 + TG 通知

## 📁 文件结构

```
checkin-gaming4/
├── .github/workflows/aclclouds-kaka.yml
├── ACLClouds-server/
│   ├── renew.py
│   ├── requirements.txt
│   └── README.md
```

## 🔧 工作原理

1. Playwright 打开 Chrome → 注入 Cookie 绕过登录
2. 访问 `dash.aclclouds.com/projects` → 找到"卡卡"项目
3. 进入项目详情 → 查找续期按钮（到期前 2 天出现）
4. 点击续期 → 检查结果 → TG 推送通知

> ⚠️ ~~Google OAuth~~ 在 GitHub Actions 环境会被 Google 封锁，改用 Cookie 注入。

## 🚀 部署步骤

### 1. 获取 Cookie

1. 浏览器登录 https://dash.aclclouds.com
2. 按 `F12` → `Application` → `Cookies` → `https://dash.aclclouds.com`
3. 把所有 Cookie 复制成 `key1=value1; key2=value2; ...` 格式

### 2. 配置 Secrets

仓库 → `Settings` → `Secrets and variables` → `Actions` → `New repository secret`

| Secret 名 | 必填 | 说明 |
|---|---|---|
| `ACL_TOKEN` | ✅ | dash.aclclouds.com 的 Cookie 字符串 |
| `TG_BOT_TOKEN` | ❌ | Telegram Bot Token |
| `TG_CHAT_ID` | ❌ | Telegram Chat ID |

### 3. 手动触发测试

Actions → `AclClouds-Kaka-Renew` → `Run workflow`

### 4. 自动续期

默认每天 UTC 01:00（北京时间 09:00）自动运行。

> Cookie 会过期，如果通知报"Cookie 已过期"，重复步骤 1-2 更新 `ACL_TOKEN`。

## 📱 TG 通知示例

```
🎮 AclClouds 续期通知
🖥️项目: 卡卡
📊续期结果: ✅续期成功
📋到期: 3天 7小时
⏱耗时: 15.3s
```

## ⚠️ 注意事项

- 续期按钮在**到期前 2 天**才会出现，未到窗口时脚本正常退出不报错
- Cookie 有效期通常 7-30 天，过期后需要更新
- 如果 Google 账号有 2FA，Cookie 方式不受影响
