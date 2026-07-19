#!/usr/bin/env python3
"""
Gaming4Free Renew Pro v10 - 自动续期脚本
拆分自单文件，避免 GitHub Actions autocrlf 压缩问题
"""
import os, sys, time, re, json, traceback, urllib.parse, urllib.request
from datetime import datetime

try:
    from seleniumbase import SB
except ImportError:
    print("seleniumbase not installed. Run: pip install seleniumbase")
    sys.exit(1)

from utils import log, screenshot, parse_countdown_seconds
from utils import get_remaining_time
from cooldown import check_button_cooldown
from tg_notify import send_tg
from config import SERVERS

MAX_BROWSER_RETRIES = 3

def main():
    log("========== 开始处理服务器账号 ==========")
    if not SERVERS:
        log("❌ 未配置 GAME4FREE_RENEW_URL + GAME4FREE_COOKIE 或 GAME4FREE_ACCOUNTS")
        log("请检查 Secrets 配置")
        sys.exit(1)
    
    for server_name, server_url, server_cookie in SERVERS:
        for browser_attempt in range(MAX_BROWSER_RETRIES):
            sb = None
            driver = None
            try:
                log(f"🚀 正在启动浏览器 (第 {browser_attempt+1}/{MAX_BROWSER_RETRIES} 次尝试)...")
                sb = SB(uc=True, headless=False, browser='chrome',
                        agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
                driver = sb.driver
                
                log(f"🌐 正在访问续期页面 (第 {browser_attempt+1}/{MAX_BROWSER_RETRIES} 次尝试): {server_url}")
                driver.get(server_url)
                log(f"📄 当前页面标题: {driver.title}")
                
                if server_cookie:
                    log("🍪 正在注入浏览器 Cookie 凭证...")
                    driver.add_cookie({"name":"XSRF-TOKEN","value":"%22eyJpdiI6IjJhQ2R6ZmVnM2R4a0RjV09zZ3B3V1E9PSIsInZhbHVlIjoia3Z0Q3N3cG10ZlV5TnRrN0R3Q1FkU0Z4VjNpQkVJYjJjQlB3a2xkSEJ2eGJYR3l1UzNkQm91UmxVUjNqR1JhS21yYjN4eFRlU0JnZUJhNlBGM2x5a0dVZnVnZ3h6ZjR2YjB3c0JhZjhYU1h3aEh5N0xhT2JxT3JFZG5hVzBZT3V2S1EiLCJtYWMiOiI1M2YwNjM0ZjBiMWQ4ZjIyZmM2NjQ1Y2IyY2RhZWI4N2U1OGIyZjI5NjI4ZjJmYjI2MjA5YmVjZjQ4YjBhNDcyIiwidGFnIjoiIn0%22","domain":".gaming4free.net","path":"/","secure":True})
                    driver.add_cookie({"name":"g4f_session", "value":server_cookie, "domain":".gaming4free.net", "path":"/", "secure":True})
                    log("✅ Cookie 凭证注入完成")
                
                log("🔄 刷新页面让 Cookie 生效...")
                driver.refresh()
                time.sleep(5)
                log(f"📄 刷新后页面标题: {driver.title}")
                
                log(f"🔑 准备执行账号操作: {server_name}")
                log("⏳ 等待页面组件完全加载 (最多15秒)...")
                time.sleep(15)
                
                log("⏳ 等待页面完全渲染以获取初始时间...")
                before_lt, before_ls = get_remaining_time(driver)
                log(f"⏱️ 续期前剩余时长: {before_lt} ({before_ls}秒)")
                
                cooldown_info = check_button_cooldown(driver)
                if cooldown_info and cooldown_info.get('cooldown'):
                    remaining = cooldown_info.get('remaining', 0)
                    log(f"⏳ 按钮冷却中，剩余 {remaining}秒，等待...")
                    time.sleep(min(remaining, 300))
                
                log("🖱️ 正在寻找并点击 +90 分钟续期按钮...")
                
                button_text = driver.execute_script("""
                    var btns = document.querySelectorAll('button, [role="button"]');
                    for (var i = 0; i < btns.length; i++) {
                        var txt = (btns[i].innerText || btns[i].textContent || '').trim();
                        if (txt.indexOf('90') !== -1 || txt.indexOf('+ 90') !== -1 || txt.indexOf('+90') !== -1) {
                            return txt;
                        }
                    }
                    return 'not-found';
                """)
                log(f"🎯 找到按钮: {button_text}")
                
                if button_text == 'not-found':
                    log("❌ 未找到 +90 min 按钮")
                    send_tg("❌ 未找到续期按钮", server_name, before_lt)
                    break
                
                click_result = driver.execute_script("""
                    var btns = document.querySelectorAll('button, [role="button"]');
                    for (var i = 0; i < btns.length; i++) {
                        var txt = (btns[i].innerText || btns[i].textContent || '').trim();
                        if (txt.indexOf('90') !== -1 || txt.indexOf('+ 90') !== -1 || txt.indexOf('+90') !== -1) {
                            btns[i].scrollIntoView({block: 'center'});
                            btns[i].removeAttribute('disabled');
                            btns[i].style.cssText += '; pointer-events:auto !important;';
                            btns[i].click();
                            return 'clicked:' + txt;
                        }
                    }
                    return 'not-found';
                """)
                log(f"🎯 点击结果: {click_result}")
                
                if 'clicked' in click_result:
                    log("⏳ 等待 Turnstile 验证...")
                    ts_detected = False
                    for tw in range(30):
                        try:
                            ts_present = bool(driver.execute_script("""
                                return !!document.querySelector('iframe[src*="challenges.cloudflare.com"]')
                                    || !!document.querySelector('.cf-turnstile')
                                    || (document.body && document.body.innerText.includes("请验证您是真人"));
                            """))
                        except:
                            ts_present = False
                        if ts_present:
                            log("🛡️ 检测到 Turnstile")
                            ts_detected = True
                            break
                        time.sleep(1)
                    
                    if ts_detected:
                        log("⏳ 等 Turnstile 通过 (最多 20 秒, 检测 iframe 消失)...")
                        for wait in range(20):
                            try:
                                gone = not bool(driver.execute_script("""
                                    return !!document.querySelector('iframe[src*="challenges.cloudflare.com"]')
                                        || !!document.querySelector('.cf-turnstile');
                                """))
                                if gone:
                                    log(f"✅ [{wait+1}秒] Turnstile 已通过 (iframe 消失)")
                                    break
                            except:
                                pass
                            time.sleep(1)
                        time.sleep(5)
                    else:
                        log("ℹ️ 未检测到 Turnstile，直接继续")
                        time.sleep(5)
                    
                    log("🔄 用 driver.refresh() 刷新页面验证续期结果...")
                    try:
                        driver.refresh()
                        time.sleep(5)
                    except Exception as e:
                        log(f"⚠️ refresh 失败: {e}")
                        time.sleep(10)
                    
                    after_lt, after_ls = get_remaining_time(driver)
                    diff = after_ls - before_ls
                    
                    log(f"⏱️ 续期后时间: {after_lt} ({after_ls}秒)，增加: {diff}秒")
                    
                    if diff > 0:
                        log(f"✅ 续期成功！时间增加 {diff}秒 ({before_lt} → {after_lt})")
                        send_tg(f"✅ Pro续期成功 (+{diff}s)", server_name, after_lt)
                    else:
                        log(f"❌ 续期失败！时间减少 {abs(diff)}秒 ({before_lt} → {after_lt})")
                        send_tg(f"❌ Pro续期失败 (-{abs(diff)}s)", server_name, after_lt)
                else:
                    log("❌ 点击按钮失败")
                    send_tg("❌ 点击按钮失败", server_name, before_lt)
            
            except Exception as e:
                log(f"❌ 服务器 '{server_name}' 执行异常: {e}")
                try:
                    screenshot(sb, "错误截图")
                except: pass
                send_tg(f"❌ 执行异常: {e}", server_name)
                break
            finally:
                if driver:
                    try:
                        driver.quit()
                    except: pass
                if sb:
                    try:
                        sb.quit()
                    except: pass

if __name__ == "__main__":
    main()
