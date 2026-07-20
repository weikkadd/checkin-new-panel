#!/usr/bin/env python3
"""
Gaming4Free Renew Pro v14 - 修复版
=====================
- 修复：Cookie注入前先访问域名首页，避免超时
- 修复：Livewire 组件 ID 查找逻辑（querySelector不支持:contains）
- 增强：更多按钮查找策略 + 调试日志
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
RENEW_THRESHOLD_SECONDS = 45 * 3600
MAX_ROUNDS = 10


def _inject_cookies_via_cdp(driver, cookie_str, domain):
    """通过 CDP 方式注入 Cookie，不受当前页面域名限制"""
    cookies = []
    for item in cookie_str.split(";"):
        item = item.strip()
        if "=" in item:
            name, value = item.split("=", 1)
            cookies.append({
                "name": name.strip(),
                "value": value.strip(),
                "domain": domain,
                "path": "/",
            })
    for c in cookies:
        try:
            driver.execute_cdp_cmd("Network.setCookie", c)
        except Exception as e:
            log(f"  CDP Cookie 注入失败 [{c.get('name')}]: {e}")
    log(f"  CDP 方式注入 {len(cookies)} 个 Cookie 完成")


def _find_renew_button(driver):
    """找到 +90 续期按钮的 wire:id 和 Livewire component"""
    return driver.execute_script("""
        (function() {
            var btns = document.querySelectorAll('button');
            for (var i = 0; i < btns.length; i++) {
                var txt = (btns[i].innerText || btns[i].textContent || '').trim();
                if (txt.indexOf('90') !== -1 && btns[i].offsetParent !== null) {
                    var comp = btns[i];
                    while (comp && !comp.getAttribute('wire:id')) {
                        comp = comp.parentElement;
                    }
                    if (comp) {
                        return JSON.stringify({
                            wireId: comp.getAttribute('wire:id'),
                            btnText: txt,
                            btnDisabled: btns[i].disabled,
                        });
                    }
                    return JSON.stringify({wireId: null, btnText: txt, btnDisabled: btns[i].disabled});
                }
            }
            return JSON.stringify({wireId: null, btnText: null, btnDisabled: null});
        })();
    """)


def _call_livewire_extend(driver, wire_id):
    """通过 wire:id 调用 Livewire extend 方法"""
    result = driver.execute_script("""
        if (!window.Livewire) return 'no-livewire-global';
        var comp = window.Livewire.find(arguments[0]);
        if (!comp) return 'component-not-found';
        try {
            comp.call('extend');
            return 'called';
        } catch(e) {
            return 'error:' + e.message;
        }
    """, wire_id)
    return result


def _call_livewire_extend_generic(driver):
    """遍历所有 Livewire 组件尝试调用 extend"""
    return driver.execute_script("""
        if (!window.Livewire) return 'no-livewire';
        var comps = window.Livewire.all();
        for (var i = 0; i < comps.length; i++) {
            try {
                comps[i].call('extend');
                return 'called-' + i;
            } catch(e) {}
        }
        return 'no-match';
    """)


def _native_click_button(driver):
    """JS 原生点击包含 90 的按钮"""
    return driver.execute_script("""
        var btns = document.querySelectorAll('button');
        for (var i = 0; i < btns.length; i++) {
            var txt = (btns[i].innerText || btns[i].textContent || '').trim();
            if (txt.indexOf('90') !== -1) {
                btns[i].scrollIntoView({block: 'center'});
                btns[i].removeAttribute('disabled');
                btns[i].style.cssText += '; pointer-events:auto !important;';
                btns[i].click();
                return 'clicked:' + txt;
            }
        }
        return 'not-found';
    """)


def main():
    log("========== 开始处理服务器账号 (Pro v14 fix) ==========")
    if not SERVERS:
        log("未配置服务器信息")
        sys.exit(1)

    for server_name, server_url, server_cookie in SERVERS:
        log(f"\n准备执行账号操作: {server_name}")

        success_in_this_server = False
        for browser_attempt in range(MAX_BROWSER_RETRIES):
            if success_in_this_server:
                break

            try:
                log(f"启动浏览器 (第 {browser_attempt+1}/{MAX_BROWSER_RETRIES} 次尝试)...")
                with SB(uc=True, headless=False, browser='chrome',
                        agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36") as sb:
                    driver = sb.driver
                    driver.set_page_load_timeout(30)

                    # --- 修复1: 先访问域名首页再注入 Cookie ---
                    if server_cookie:
                        log("先访问域名首页准备注入 Cookie...")
                        try:
                            driver.get("https://control.gaming4free.net/")
                        except Exception:
                            log("域名首页加载超时，忽略继续...")
                        time.sleep(2)
                        log("通过 CDP 注入 Cookie...")
                        _inject_cookies_via_cdp(driver, server_cookie, ".gaming4free.net")
                        time.sleep(1)

                    log(f"访问页面: {server_url}")
                    try:
                        driver.get(server_url)
                    except Exception:
                        log("页面加载超时，尝试 JS 停止加载...")
                        driver.execute_script("window.stop();")
                    time.sleep(10)

                    # 验证登录状态
                    page_text = driver.execute_script(
                        "return document.body?document.body.innerText.substring(0,500):'';"
                    )
                    if "login" in page_text.lower() and "90" not in page_text:
                        log("未登录状态，Cookie 可能已过期")
                        send_tg("Cookie 已过期", server_name, "")
                        break

                    current_round = 0
                    while current_round < MAX_ROUNDS:
                        current_round += 1
                        log(f"\n--- 第 {current_round}/{MAX_ROUNDS} 轮续期 ---")

                        before_lt, before_ls = get_remaining_time(driver)
                        log(f"当前剩余时长: {before_lt} ({before_ls}秒)")

                        if before_ls >= RENEW_THRESHOLD_SECONDS:
                            log(f"目标时长已达标，停止续期")
                            success_in_this_server = True
                            break

                        # 检查冷却
                        try:
                            page_text = driver.execute_script(
                                "return document.body?document.body.innerText:'';"
                            )
                            if "05:00" in page_text and "cd" in page_text.lower():
                                log("侦测到 5 分钟冷却期，等待 310 秒...")
                                time.sleep(310)
                                driver.refresh()
                                time.sleep(10)
                                continue
                        except Exception:
                            pass

                        # --- 修复2: 三层续期策略 ---
                        renew_triggered = False

                        # 策略1: 通过 wire:id 精确调用 Livewire extend
                        btn_info_json = _find_renew_button(driver)
                        try:
                            btn_info = json.loads(btn_info_json)
                        except Exception:
                            btn_info = {}
                        log(f"按钮诊断: {btn_info}")

                        wire_id = btn_info.get("wireId")
                        if wire_id:
                            log(f"策略1: Livewire extend (wire:id={wire_id})...")
                            result = _call_livewire_extend(driver, wire_id)
                            log(f"  Livewire 调用结果: {result}")
                            if result == 'called':
                                renew_triggered = True
                        else:
                            log("未找到 wire:id，使用通用 Livewire 搜索...")
                            result = _call_livewire_extend_generic(driver)
                            log(f"  通用 Livewire 调用结果: {result}")
                            if result.startswith('called'):
                                renew_triggered = True

                        # 策略2: JS 原生 click
                        if not renew_triggered:
                            log("策略2: JS 原生 click...")
                            click_result = _native_click_button(driver)
                            log(f"  点击结果: {click_result}")
                            if click_result.startswith('clicked'):
                                renew_triggered = True

                        # 策略3: SeleniumBase 模拟点击
                        if not renew_triggered:
                            log("策略3: SeleniumBase 模拟点击...")
                            try:
                                sb.click('button:contains("90")', timeout=5)
                                renew_triggered = True
                                log("  SeleniumBase 点击成功")
                            except Exception:
                                try:
                                    sb.click(".rt-btn-free", timeout=3)
                                    renew_triggered = True
                                    log("  SeleniumBase .rt-btn-free 点击成功")
                                except Exception:
                                    log("  策略3也失败")

                        if not renew_triggered:
                            log("所有续期触发策略均失败，刷新重试...")
                            driver.refresh()
                            time.sleep(10)
                            continue

                        # 等待 Turnstile
                        time.sleep(5)
                        try:
                            if driver.find_elements('css selector', 'iframe[src*="challenges.cloudflare.com"]'):
                                log("等待 Turnstile 验证...")
                                for _ in range(30):
                                    if not driver.find_elements('css selector', 'iframe[src*="challenges.cloudflare.com"]'):
                                        log("Turnstile 已通过")
                                        break
                                    time.sleep(1)
                        except Exception:
                            pass

                        # 监测广告 + 模拟活跃
                        log("监测广告播放中...")
                        start_wait = time.time()
                        while time.time() - start_wait < 90:
                            driver.execute_script("window.dispatchEvent(new Event('mousemove'));")
                            try:
                                driver.execute_script("""
                                    var closeBtns = document.querySelectorAll('[aria-label="Close"], .modal-close');
                                    for(var i=0; i<closeBtns.length; i++) {
                                        if(closeBtns[i].offsetParent !== null) closeBtns[i].click();
                                    }
                                """)
                            except Exception:
                                pass
                            if (time.time() - start_wait) > 30 and int(time.time() - start_wait) % 15 == 0:
                                _, check_ls = get_remaining_time(driver)
                                if check_ls > before_ls + 3000:
                                    log("检测到时间已增加，广告提前结束")
                                    break
                            time.sleep(2)

                        # 刷新验证
                        log("刷新页面同步状态...")
                        driver.refresh()
                        time.sleep(12)
                        after_lt, after_ls = get_remaining_time(driver)
                        diff = after_ls - before_ls

                        if diff > 3000:
                            log(f"第 {current_round} 轮成功！新时间: {after_lt}")
                            send_tg(f"续期成功 (第{current_round}轮)", server_name, after_lt)
                            log("续期成功，进入 5 分钟冷却期 (310秒)...")
                            time.sleep(310)
                            driver.refresh()
                            time.sleep(10)
                        else:
                            log(f"第 {current_round} 轮失败，时间未增加 (diff={diff}s)")
                            try:
                                page_text = driver.execute_script(
                                    "return document.body?document.body.innerText:'';"
                                )
                                if "cd" in page_text.lower():
                                    log("检测到已处于冷却状态，等待 310 秒...")
                                    time.sleep(310)
                                    driver.refresh()
                                    time.sleep(10)
                            except Exception:
                                pass
                            try:
                                sb.uc_open_with_reconnect(server_url, reconnect_time=10)
                                time.sleep(10)
                            except Exception:
                                pass

                    log(f"账号 {server_name} 处理结束")
                    break

            except Exception as e:
                log(f"运行异常: {e}")
                traceback.print_exc()
                time.sleep(10)

    log("========== 所有服务器账号处理完成 ==========")


if __name__ == "__main__":
    main()
