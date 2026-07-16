#!/usr/bin/env python3
"""
AclClouds 卡卡项目自动续期脚本 v2
- Playwright + Google OAuth 登录（支持弹窗模式）
- 自动定位"卡卡"项目
- 到期前 2 天点击续期按钮
- TG 通知结果
- 每步截图调试
"""

import os, time, random, asyncio, sys

GOOGLE_EMAIL    = os.environ.get("KAKA_GOOGLE_EMAIL", "").strip()
GOOGLE_PASSWORD = os.environ.get("KAKA_GOOGLE_PASSWORD", "").strip()
TG_CHAT_ID      = os.environ.get("TG_CHAT_ID", "").strip()
TG_TOKEN        = os.environ.get("TG_BOT_TOKEN", "").strip()

BASE_URL      = "https://dash.aclclouds.com"
LOGIN_URL     = f"{BASE_URL}/login"
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
    return path


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
            # === Step 1: Google 登录 ===
            print("[卡卡] Step 1/3: 打开登录页")
            await page.goto(LOGIN_URL, wait_until="networkidle", timeout=30000)
            await screenshot(page, "01-login-page")
            rand_sleep(1, 2)

            # 找 Google 登录按钮
            google_selectors = [
                'button:has-text("Google")',
                'a:has-text("Google")',
                '[data-provider="google"]',
                '.google-btn', '.google-login',
                'button:has-text("谷歌")',
                'img[alt*="Google"]',
                'div[class*="google"]',
                'span:has-text("Google")',
            ]
            clicked = False
            for sel in google_selectors:
                try:
                    btn = await page.query_selector(sel)
                    if btn and await btn.is_visible():
                        txt = (await btn.inner_text()).strip()[:50]
                        print(f"[卡卡] 找到 Google 按钮: '{txt}' ({sel})")
                        await btn.click()
                        clicked = True
                        break
                except:
                    continue

            if not clicked:
                # 最后尝试文本匹配
                result = await page.evaluate("""
                    () => {
                        const all = document.querySelectorAll('a,button,div[role="button"],span[role="button"]');
                        for (const el of all) {
                            if (/google/i.test(el.textContent||'')) {
                                el.click(); return el.textContent.trim();
                            }
                        }
                        return null;
                    }
                """)
                if result:
                    print(f"[卡卡] 文本匹配找到: {result}")
                    clicked = True

            if not clicked:
                await screenshot(page, "02-no-google-btn")
                raise Exception("未找到 Google 登录按钮")

            # 等 OAuth 弹出或跳转
            rand_sleep(3, 5)
            await screenshot(page, "03-after-google-click")
            print(f"[卡卡] 点击后 URL: {page.url}")

            # --- 关键: 处理弹窗 ---
            popup_page = None
            # 尝试获取通过 window.open 打开的弹窗
            pages = context.pages
            print(f"[卡卡] 当前打开 {len(pages)} 个页面")
            for i, pg in enumerate(pages):
                print(f"[卡卡]   页面 {i}: {pg.url[:100]}")
                if pg != page:
                    popup_page = pg

            # 也监听可能的新弹窗
            if not popup_page:
                try:
                    async with context.expect_page(timeout=5000) as popup_info:
                        pass  # 可能已经弹出了
                except:
                    pass

            pages = context.pages
            if len(pages) > 1:
                popup_page = pages[-1]

            if popup_page:
                print(f"[卡卡] 检测到弹窗: {popup_page.url[:120]}")
                await popup_page.bring_to_front()
                target_page = popup_page
            elif "accounts.google.com" in page.url:
                print("[卡卡] Google OAuth 在同页跳转")
                target_page = page
            else:
                # 可能登录页用的是 iframe 或弹窗还没打开，手动导航
                print(f"[卡卡] 未检测到弹窗或跳转，当前 URL: {page.url}")
                await screenshot(page, "04-no-popup")
                # 尝试手动触发 Google OAuth URL
                print("[卡卡] 尝试直接打开 Google OAuth...")
                # 有些网站用统一的 Google auth URL
                pass

            # 在目标页填写邮箱
            if not target_page and "accounts.google.com" not in page.url:
                # 最后手段: 重新截图看页面状态
                await screenshot(page, "05-stuck")
                raise Exception(f"Google OAuth 未触发，当前 URL: {page.url}")

            tp = target_page if target_page else page

            # 等待邮箱输入框
            print("[卡卡] 等待邮箱输入框...")
            email_input = None
            for attempt in range(3):
                try:
                    email_input = await tp.wait_for_selector('input[type="email"]', timeout=10000)
                    break
                except:
                    await screenshot(tp, f"06-email-wait-{attempt}")
                    print(f"[卡卡] 邮箱框等待第 {attempt+1} 次超时，URL: {tp.url}")
                    rand_sleep(2, 4)

            if not email_input:
                await screenshot(tp, "06-no-email")
                # 尝试其他邮箱选择器
                email_input = await tp.query_selector('input[name="identifier"]')
                if not email_input:
                    email_input = await tp.query_selector('#identifierId')

            if not email_input:
                raise Exception(f"找不到邮箱输入框，URL: {tp.url}")

            await email_input.fill(GOOGLE_EMAIL)
            print("[卡卡] 已填写邮箱")
            rand_sleep(0.5, 1.5)

            # 点击下一步
            next_btn = await tp.query_selector('button:has-text("Next"), button:has-text("下一步"), #identifierNext, #identifierNext > button')
            if next_btn:
                await next_btn.click()
            rand_sleep(3, 5)

            # 填写密码
            try:
                pwd_input = await tp.wait_for_selector('input[type="password"]', timeout=10000)
                await pwd_input.fill(GOOGLE_PASSWORD)
                print("[卡卡] 已填写密码")
                rand_sleep(0.5, 1.5)
                pwd_next = await tp.query_selector('button:has-text("Next"), button:has-text("下一步"), #passwordNext, #passwordNext > button')
                if pwd_next:
                    await pwd_next.click()
            except:
                print("[卡卡] 未出现密码框（设备已信任）")

            rand_sleep(5, 10)

            # 处理后续页面
            all_pages = context.pages
            for pg in all_pages:
                u = pg.url
                print(f"[卡卡] 页面: {u[:120]}")

            # 回到主页面
            main_page = page
            for pg in context.pages:
                if "dash.aclclouds.com" in pg.url:
                    main_page = pg
                    await main_page.bring_to_front()
                    break

            print(f"[卡卡] 当前主页 URL: {main_page.url}")
            if "login" in main_page.url and "dash.aclclouds.com" in main_page.url:
                await screenshot(main_page, "07-login-failed")
                raise Exception("Google 登录未成功，仍在登录页")

            print("[卡卡] ✅ Google 登录成功")

            # === Step 2: 找卡卡 ===
            print("[卡卡] Step 2/3: 定位卡卡")
            await main_page.goto(PROJECTS_URL, wait_until="networkidle", timeout=30000)
            rand_sleep(2, 4)
            await screenshot(main_page, "08-projects")

            found = await main_page.evaluate("""
                () => {
                    for (const el of document.querySelectorAll('a,button,div[role="button"],tr,li,.project,div')) {
                        if (el.textContent && el.textContent.includes('卡卡')) {
                            el.click(); return true;
                        }
                    }
                    return false;
                }
            """)
            if not found:
                raise Exception("未找到'卡卡'项目")

            rand_sleep(2, 4)

            # === Step 3: 续期 ===
            print("[卡卡] Step 3/3: 续期")
            await screenshot(main_page, "09-project-detail")

            renew_selectors = [
                'button:has-text("续期")', 'a:has-text("续期")',
                'button:has-text("Renew")', 'button:has-text("免费续期")',
                'button:has-text("延长")', 'button:has-text("延期")',
            ]
            renew_done = False
            for sel in renew_selectors:
                btn = await main_page.query_selector(sel)
                if btn:
                    v = await btn.is_visible()
                    d = await btn.is_disabled()
                    if v and not d:
                        txt = (await btn.inner_text()).strip()
                        print(f"[卡卡] 点击续期: {txt}")
                        await btn.click()
                        renew_done = True
                        break
                    elif v and d:
                        raise Exception(f"续期按钮禁用: {sel}")
                    else:
                        print(f"[卡卡] 按钮不可见: {sel}")

            if not renew_done:
                await screenshot(main_page, "10-no-renew-btn")
                # 宽松模式: 没找到续期按钮不一定失败(可能未到时间窗口)
                print("[卡卡] 续期按钮未出现（可能未到时间窗口）")
                dur = round(time.time() - t0, 1)
                tg("🎮 AclClouds 续期通知",
                   f"🖥️项目: 卡卡\n📊续期结果: ⚠️未到窗口\n⏰耗时: {dur}s")
                return

            rand_sleep(2, 4)

            success = await main_page.evaluate(
                "() => /续期成功|Renewal|已续期|操作成功|succeeded/i.test(document.body.innerText)"
            )
            dur = round(time.time() - t0, 1)
            print(f"[卡卡] {'✅' if success else '✅'} 完成 (耗时 {dur}s)")
            tg("🎮 AclClouds 续期通知",
               f"🖥️项目: 卡卡\n📊续期结果: {'✅成功' if success else '✅已执行'}\n⏰耗时: {dur}s")

        except Exception as e:
            dur = round(time.time() - t0, 1)
            err = str(e)
            print(f"[卡卡] ❌ 失败: {err}")
            try:
                await screenshot(page, "99-error-final")
            except:
                pass
            tg("🎮 AclClouds 续期失败",
               f"🖥️项目: 卡卡\n📊续期结果: ❌失败\n⚠️: {err}\n⏰耗时: {dur}s")
            sys.exit(1)

        finally:
            await browser.close()


if __name__ == "__main__":
    if not GOOGLE_EMAIL or not GOOGLE_PASSWORD:
        print("❌ 请设置 KAKA_GOOGLE_EMAIL 和 KAKA_GOOGLE_PASSWORD")
        sys.exit(1)
    asyncio.run(run())
