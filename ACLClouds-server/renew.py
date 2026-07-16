#!/usr/bin/env python3
"""
AclClouds 卡卡项目自动续期脚本 v3
- Cookie 注入（绕过 Google OAuth 封锁）
- 自动定位"卡卡"项目
- 到期前 2 天点击续期按钮
- TG 通知 + 每步截图
"""

import os, time, random, asyncio, sys

GOOGLE_EMAIL    = os.environ.get("KAKA_GOOGLE_EMAIL", "").strip()
GOOGLE_PASSWORD = ***"KAKA_GOOGLE_PASSWORD", "").strip()
ACL_TOKEN       = os.environ.get("ACL_TOKEN", "").strip()  # dash.aclclouds.com 的 Cookie
TG_CHAT_ID      = os.environ.get("TG_CHAT_ID", "").strip()
TG_TOKEN        = ***"TG_BOT_TOKEN", "").strip()

BASE_URL      = "https://dash.aclclouds.com"
PROJECTS_URL  = f"{BASE_URL}/projects"

SCREENSHOT_DIR = "/tmp/aclclouds-debug"

def rand_sleep(lo=0.5, hi=3.0):
    time.sleep(random.uniform(lo, hi))


def tg(title, msg):
    if not TG_TOKEN or not TG_CHAT_ID:
        return
    import urllib.request, urllib.parse
    text = f"<b>{title}</b>\n{msg}"
    try:
        urllib.request.urlopen(
            f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage",
            data=urllib.parse.urlencode({"chat_id": TG_CHAT_ID, "text": text, "parse_mode": "HTML"}).encode(),
            timeout=10
        )
    except Exception as e:
        print(f"[TG] {e}")


async def screenshot(page, name):
    os.makedirs(SCREENSHOT_DIR, exist_ok=True)
    path = f"{SCREENSHOT_DIR}/{name}.png"
    await page.screenshot(path=path, full_page=True)
    print(f"[截图] {path}")


async def run():
    from playwright.async_api import async_playwright

    t0 = time.time()
    os.makedirs(SCREENSHOT_DIR, exist_ok=True)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=[
            "--disable-blink-features=AutomationControlled",
            "--no-sandbox",
            "--disable-setuid-sandbox",
            "--disable-dev-shm-usage",
        ])
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080},
            locale="zh-CN",
        )
        page = await context.new_page()

        try:
            # === Step 0: Cookie 注入 ===
            print("[卡卡] Step 0: Cookie 注入")
            if ACL_TOKEN:
                # 注入 Cookie
                cookies = []
                for pair in ACL_TOKEN.split(";"):
                    pair = pair.strip()
                    if not pair:
                        continue
                    parts = pair.split("=", 1)
                    if len(parts) == 2:
                        cookies.append({
                            "name": parts[0].strip(),
                            "value": parts[1].strip(),
                            "domain": ".aclclouds.com",
                            "path": "/",
                        })
                if cookies:
                    await context.add_cookies(cookies)
                    print(f"[卡卡] 注入 {len(cookies)} 个 Cookie")
                else:
                    print("[卡卡] ⚠️ Cookie 格式无效")
            else:
                print("[卡卡] ⚠️ 未设置 ACL_TOKEN，尝试无 Cookie 访问")

            # === Step 1: 验证登录状态 ===
            print("[卡卡] Step 1/3: 验证登录")
            await page.goto(PROJECTS_URL, wait_until="networkidle", timeout=30000)
            rand_sleep(1, 2)
            await screenshot(page, "01-projects-page")

            current_url = page.url
            print(f"[卡卡] 当前 URL: {current_url}")

            # 检查是否被重定向到登录页
            if "/login" in current_url or "sign_in" in current_url.lower():
                await screenshot(page, "02-redirected-to-login")
                raise Exception("Cookie 已过期，请更新 ACL_TOKEN")

            # 检查页面内容是否像项目列表
            page_text = await page.evaluate("() => document.body ? document.body.innerText.substring(0, 500) : ''")
            if "登录" in page_text and "卡卡" not in page_text:
                await screenshot(page, "03-not-logged-in")
                raise Exception("未登录状态，请更新 ACL_TOKEN")

            print("[卡卡] ✅ 登录状态正常")

            # === Step 2: 找卡卡项目 ===
            print("[卡卡] Step 2/3: 定位卡卡项目")
            await screenshot(page, "04-project-list")

            # 查找"卡卡"并点击
            found = await page.evaluate("""
                () => {
                    const els = document.querySelectorAll('a, button, div[role="button"], tr, li, .project, .card');
                    for (const el of els) {
                        if (el.textContent && el.textContent.includes('卡卡')) {
                            el.click();
                            return true;
                        }
                    }
                    return false;
                }
            """)

            if not found:
                # 尝试更广泛的搜索
                found = await page.evaluate("""
                    () => {
                        const all = document.querySelectorAll('*');
                        for (const el of all) {
                            if (el.children.length === 0 && el.textContent && el.textContent.includes('卡卡')) {
                                let parent = el;
                                for (let i = 0; i < 5; i++) {
                                    parent = parent.parentElement;
                                    if (!parent) break;
                                    if (parent.tagName === 'A' || parent.tagName === 'BUTTON' || parent.getAttribute('role') === 'button') {
                                        parent.click();
                                        return true;
                                    }
                                }
                                el.click();
                                return true;
                            }
                        }
                        return false;
                    }
                """)

            if not found:
                await screenshot(page, "05-no-kaka")
                # 打印页面所有文本帮助调试
                print(f"[卡卡] 页面文本前500字: {page_text[:500]}")
                raise Exception("未找到'卡卡'项目")

            print("[卡卡] 找到卡卡项目，进入详情")
            rand_sleep(2, 4)
            await screenshot(page, "06-kaka-detail")

            # === Step 3: 点击续期 ===
            print("[卡卡] Step 3/3: 查找续期按钮")

            renew_selectors = [
                'button:has-text("续期")',
                'a:has-text("续期")',
                'button:has-text("Renew")',
                'button:has-text("免费续期")',
                'button:has-text("延长")',
                'button:has-text("延期")',
                'button:has-text("renew")',
                'a:has-text("renew")',
            ]

            renew_done = False
            for sel in renew_selectors:
                btn = await page.query_selector(sel)
                if btn:
                    v = await btn.is_visible()
                    d = await btn.is_disabled()
                    if v and not d:
                        txt = (await btn.inner_text()).strip()
                        print(f"[卡卡] 点击续期按钮: {txt}")
                        await btn.click()
                        renew_done = True
                        break
                    elif v and d:
                        print(f"[卡卡] 续期按钮已禁用: {sel}")
                        # 按钮在但禁用 = 未到续期窗口
                        dur = round(time.time() - t0, 1)
                        await screenshot(page, "07-renew-disabled")
                        # 读取到期时间信息
                        expiry_info = await page.evaluate("""
                            () => {
                                const txt = document.body.innerText;
                                const m = txt.match(/到期[时间]*[：:]\s*([^\n]{5,30})/);
                                return m ? m[0] : '';
                            }
                        """)
                        tg("🎮 AclClouds 续期通知",
                           f"🖥️项目: 卡卡\n📊续期结果: ⚠️未到续期窗口\n"
                           f"{'⏰' + expiry_info if expiry_info else ''}\n⏱耗时: {dur}s")
                        return
                    else:
                        print(f"[卡卡] 按钮不可见: {sel}")

            if not renew_done:
                # 可能续期按钮确实不存在（未到时间窗口）
                await screenshot(page, "08-no-renew-btn")

                # 检查页面是否有到期时间信息
                expiry_info = await page.evaluate("""
                    () => {
                        const txt = document.body.innerText;
                        const m = txt.match(/(?:到期|expire|剩余|remaining)[^\n]{0,50}/i);
                        return m ? m[0] : '';
                    }
                """)
                print(f"[卡卡] 页面到期信息: {expiry_info}")
                print("[卡卡] 续期按钮未出现（可能未到续期时间窗口）")

                dur = round(time.time() - t0, 1)
                tg("🎮 AclClouds 续期通知",
                   f"🖥️项目: 卡卡\n📊续期结果: ⚠️续期按钮未出现\n"
                   f"{'📋' + expiry_info if expiry_info else '可能未到续期窗口'}\n⏱耗时: {dur}s")
                # 不报错退出，因为这不是真正的错误
                return

            rand_sleep(2, 4)
            await screenshot(page, "09-after-renew")

            # 检查续期结果
            success = await page.evaluate("""
                () => /续期成功|Renewal|已续期|操作成功|succeeded|success/i.test(
                    document.body.innerText
                )
            """)

            # 读取续期后的到期时间
            new_expiry = await page.evaluate("""
                () => {
                    const txt = document.body.innerText;
                    const m = txt.match(/(?:到期|expire|剩余|remaining)[^\n]{0,50}/i);
                    return m ? m[0] : '';
                }
            """)

            dur = round(time.time() - t0, 1)
            result = "✅续期成功" if success else "✅续期已执行"
            print(f"[卡卡] {result} (耗时 {dur}s)")
            if new_expiry:
                print(f"[卡卡] 到期信息: {new_expiry}")

            tg("🎮 AclClouds 续期通知",
               f"🖥️项目: 卡卡\n📊续期结果: {result}\n"
               f"{'📋' + new_expiry if new_expiry else ''}\n⏱耗时: {dur}s")

        except Exception as e:
            dur = round(time.time() - t0, 1)
            err = str(e)
            print(f"[卡卡] ❌ 失败: {err}")
            try:
                await screenshot(page, "99-error")
            except:
                pass
            tg("🎮 AclClouds 续期失败",
               f"🖥️项目: 卡卡\n📊续期结果: ❌失败\n⚠️: {err}\n⏱耗时: {dur}s")
            sys.exit(1)

        finally:
            await browser.close()


if __name__ == "__main__":
    if not ACL_TOKEN:
        print("❌ 请设置环境变量 ACL_TOKEN")
        print("   获取方法:")
        print("   1. 浏览器登录 https://dash.aclclouds.com")
        print("   2. F12 → Application → Cookies → 复制所有 Cookie")
        print("   3. 格式: key1=value1; key2=value2; ...")
        sys.exit(1)
    asyncio.run(run())
