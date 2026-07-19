#!/usr/bin/env python3
"""
Gaming4Free Renew Pro v11 - 自动续期脚本 (Manus 优化版)
=====================
- 增强：加入广告观看等待 (60-90秒)，确保奖励发放
- 增强：支持连续续期循环，直到剩余时间达到 45h 阈值
- 增强：优化 Turnstile 验证后的浏览器重连逻辑
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
# 续期阈值: 剩余 < 45 小时才触发续期
RENEW_THRESHOLD_SECONDS = 45 * 3600
# 最大续期轮次
MAX_ROUNDS = 10

def main():
    log("========== 开始处理服务器账号 ==========")
    if not SERVERS:
        log("❌ 未配置 GAME4FREE_RENEW_URL + GAME4FREE_COOKIE 或 GAME4FREE_ACCOUNTS")
        sys.exit(1)

    for server_name, server_url, server_cookie in SERVERS:
        log(f"\n🔑 准备执行账号操作: {server_name}")
        
        for browser_attempt in range(MAX_BROWSER_RETRIES):
            try:
                log(f"🚀 正在启动浏览器 (第 {browser_attempt+1}/{MAX_BROWSER_RETRIES} 次尝试)...")
                with SB(uc=True, headless=False, browser='chrome',
                        agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36") as sb:
                    driver = sb.driver

                    log(f"🌐 正在访问续期页面: {server_url}")
                    driver.get(server_url)
                    
                    if server_cookie:
                        log("🍪 正在注入浏览器 Cookie...")
                        injected = 0
                        for item in server_cookie.split(";"):
                            item = item.strip()
                            if "=" in item:
                                name, value = item.split("=", 1)
                                try:
                                    driver.add_cookie({"name": name.strip(), "value": value.strip(), "domain": ".gaming4free.net", "path": "/"})
                                    injected += 1
                                except: pass
                        log(f"✅ 注入 {injected} 个 Cookie，刷新页面...")
                        driver.refresh()
                        time.sleep(8)

                    current_round = 0
                    while current_round < MAX_ROUNDS:
                        current_round += 1
                        log(f"\n🔄 --- 第 {current_round}/{MAX_ROUNDS} 轮续期 ---")
                        
                        # 获取当前时间
                        before_lt, before_ls = get_remaining_time(driver)
                        log(f"⏱️ 当前剩余时长: {before_lt} ({before_ls}秒)")
                        
                        if before_ls >= RENEW_THRESHOLD_SECONDS:
                            log(f"✅ 目标时长已达标 ({RENEW_THRESHOLD_SECONDS//3600}小时)，停止续期")
                            break

                        # 检查冷却
                        cooldown_info = check_button_cooldown(driver)
                        if cooldown_info and cooldown_info.get('cooldown'):
                            remaining = cooldown_info.get('remaining', 120)
                            log(f"⏳ 按钮冷却中，等待 {remaining} 秒...")
                            time.sleep(remaining + 5)
                            driver.refresh(); time.sleep(8)
                            before_lt, before_ls = get_remaining_time(driver)

                        # 点击按钮
                        log("🖱️ 寻找并点击续期按钮...")
                        click_done = False
                        try:
                            from selenium.webdriver.common.by import By
                            xpath_candidates = [
                                "//button[contains(., 'watch ad') and contains(., '90')]",
                                "//button[contains(., '+ 90 min')]",
                                "//button[contains(., '90 min')]"
                            ]
                            for xpath in xpath_candidates:
                                btns = driver.find_elements(By.XPATH, xpath)
                                for btn in btns:
                                    if btn.is_displayed() and btn.is_enabled():
                                        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
                                        time.sleep(0.5); btn.click()
                                        click_done = True; break
                                if click_done: break
                        except: pass

                        if not click_done:
                            log("❌ 未找到续期按钮，尝试刷新...")
                            driver.refresh(); time.sleep(8); continue

                        # 处理验证码
                        log("⏳ 等待 Turnstile 验证...")
                        time.sleep(5)
                        ts_iframe = driver.find_elements(By.CSS_SELECTOR, 'iframe[src*="challenges.cloudflare.com"]')
                        if ts_iframe:
                            log("🛡️ 检测到 Turnstile，等待自动通过...")
                            for _ in range(20):
                                if not driver.find_elements(By.CSS_SELECTOR, 'iframe[src*="challenges.cloudflare.com"]'):
                                    log("✅ Turnstile 已通过")
                                    break
                                time.sleep(1)
                        
                        # 重要：观看广告等待
                        log("🎬 正在模拟观看广告，请等待 70 秒以确保奖励发放...")
                        time.sleep(70)

                        # 刷新并验证
                        log("🔄 刷新页面验证结果...")
                        driver.refresh()
                        time.sleep(8)
                        
                        after_lt, after_ls = get_remaining_time(driver)
                        diff = after_ls - before_ls
                        
                        if diff > 3000: # 增加了至少 50 分钟
                            log(f"✅ 第 {current_round} 轮续期成功！新时间: {after_lt}")
                            send_tg(f"✅ 续期成功 (第{current_round}轮)", server_name, after_lt)
                        else:
                            log(f"⚠️ 第 {current_round} 轮时间未显著增加，可能广告未完成或验证失败")
                            # 如果连续两轮失败，尝试重连浏览器
                            try: sb.uc_open_with_reconnect(server_url, reconnect_time=10); time.sleep(8)
                            except: pass

                    log(f"🏁 账号 {server_name} 处理结束")
                    break # 跳出重试循环

            except Exception as e:
                log(f"❌ 运行异常: {e}")
                time.sleep(10)

if __name__ == "__main__":
    main()
