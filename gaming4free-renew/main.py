#!/usr/bin/env python3
"""
Gaming4Free 自动续期脚本
=====================
- CDP 方式注入 Cookie，避免页面加载超时
- Livewire API 精确调用 extend
- 多层降级策略：wire:id 查找 → 通用组件遍历 → JS 原生 click
- 广告监测 + 模拟真人活跃
"""
import os
import sys
import time
import re
import json
import traceback
import urllib.parse
import urllib.request
from datetime import datetime

try:
    from seleniumbase import SB
except ImportError:
    print("seleniumbase not installed. Run: pip install seleniumbase")
    sys.exit(1)

# ==================== 配置 ====================
def load_servers():
    """从环境变量加载服务器配置"""
    servers = []
    renew_url = os.environ.get("GAME4FREE_RENEW_URL", "").strip()
    cookie = os.environ.get("GAME4FREE_COOKIE", "").strip()

    if renew_url and cookie:
        server_name = "服务器"
        if "/server/" in renew_url:
            slug = renew_url.split("/server/")[1].split("/")[0]
            server_name = f"服务器-{slug[:8]}"
        servers.append((server_name, renew_url, cookie))

    # 多账号: 名称|||URL|||Cookie
    for line in os.environ.get("GAME4FREE_ACCOUNTS", "").split("\n"):
        line = line.strip()
        if not line:
            continue
        parts = line.split("|||")
        if len(parts) >= 3:
            servers.append((parts[0].strip(), parts[1].strip(), parts[2].strip()))

    return servers


TARGET_SECONDS = 45 * 3600
MAX_ROUNDS = 10
MAX_BROWSER_RETRIES = 3

# ==================== 工具函数 ====================
def log(msg):
    ts = datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
    print(f"{ts} {msg}", flush=True)


def parse_countdown(text):
    if not text:
        return 0
    m = re.match(r'(\d+):(\d+):(\d+)', text)
    if m:
        return int(m.group(1)) * 3600 + int(m.group(2)) * 60 + int(m.group(3))
    m = re.match(r'(\d+)\s*m', text, re.I)
    if m:
        return int(m.group(1)) * 60
    m = re.match(r'(\d+)\s*h', text, re.I)
    if m:
        return int(m.group(1)) * 3600
    return 0


def get_remaining_time(driver):
    try:
        page_text = driver.execute_script(
            "return document.body?document.body.innerText.substring(0,2000):'';"
        )
        if not page_text:
            return ("(未知)", 0)
        matches = re.findall(r'(\d{1,2}:\d{2}:\d{2})', page_text)
        if matches:
            lt = matches[0]
            return (lt, parse_countdown(lt))
        return ("(未找到)", 0)
    except Exception as e:
        log(f"获取时间失败: {e}")
        return ("(错误)", 0)


def check_button_cooldown(driver):
    try:
        page_text = driver.execute_script(
            "return document.body?document.body.innerText.substring(0,2000):'';"
        )
        if page_text:
            cd_match = re.search(r'(\d+):(\d+)\s+cd', page_text, re.I)
            if cd_match:
                mins = int(cd_match.group(1))
                secs = int(cd_match.group(2))
                remaining = mins * 60 + secs
                log(f"检测到冷却倒计时: {cd_match.group(0).strip()} ({remaining}秒)")
                return {"cooldown": True, "remaining": remaining}
        try:
            disabled = bool(driver.execute_script("""
                var btns = document.querySelectorAll('button');
                for (var i = 0; i < btns.length; i++) {
                    var txt = (btns[i].innerText || btns[i].textContent || '').trim();
                    if (txt.indexOf('90') !== -1 || txt.indexOf('+ 90') !== -1) {
                        return btns[i].disabled;
                    }
                }
                return false;
            """))
            if disabled:
                log("检测到按钮 disabled 状态")
                return {"cooldown": True, "remaining": 0}
        except Exception:
            pass
        return None
    except Exception as e:
        log(f"检查冷却失败: {e}")
        return None


def send_tg(message, server_name="", time_text=""):
    tg_token = os.environ.get("TG_BOT_TOKEN", "").strip()
    tg_chat_id = os.environ.get("TG_CHAT_ID", "").strip()
    if not tg_token or not tg_chat_id:
        return
    try:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        msg = (
            f"Gaming4Free\n"
            f"Server: {server_name}\n"
            f"Time: {now}\n"
            f"Status: {message}\n"
            f"Remaining: {time_text}"
        )
        url = f"https://api.telegram.org/bot{tg_token}/sendMessage"
        data = f"chat_id={tg_chat_id}&text={urllib.parse.quote(msg)}&parse_mode=HTML".encode()
        req = urllib.request.Request(url, data=data,
                                     headers={"Content-Type": "application/x-www-form-urlencoded"})
        urllib.request.urlopen(req, timeout=10)
        log("TG 通知成功")
    except Exception as e:
        log(f"TG 通知失败: {e}")


# ==================== 核心续期逻辑 ====================
def inject_cookies(driver, cookie_str, domain):
    """CDP 方式注入 Cookie"""
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
            log(f"  Cookie 注入失败 [{c.get('name')}]: {e}")
    log(f"  CDP 方式注入 {len(cookies)} 个 Cookie")


def find_wire_id(driver):
    """查找续期按钮的 wire:id"""
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
                            btnText: txt
                        });
                    }
                    return JSON.stringify({wireId: null, btnText: txt});
                }
            }
            return JSON.stringify({wireId: null, btnText: null});
        })();
    """)


def call_livewire_extend(driver, wire_id):
    """通过 wire:id 调用 Livewire extend"""
    return driver.execute_script("""
        if (!window.Livewire) return 'no-livewire';
        var comp = window.Livewire.find(arguments[0]);
        if (!comp) return 'component-not-found';
        try { comp.call('extend'); return 'called'; }
        catch(e) { return 'error:' + e.message; }
    """, wire_id)


def call_livewire_generic(driver):
    """遍历所有 Livewire 组件尝试 extend"""
    return driver.execute_script("""
        if (!window.Livewire) return 'no-livewire';
        var comps = window.Livewire.all();
        for (var i = 0; i < comps.length; i++) {
            try { comps[i].call('extend'); return 'called-' + i; }
            catch(e) {}
        }
        return 'no-match';
    """)


def native_click(driver):
    """JS 原生点击续期按钮"""
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


def trigger_renew(driver):
    """三层策略触发续期"""
    # 策略1: wire:id 精确调用
    btn_info_json = find_wire_id(driver)
    try:
        btn_info = json.loads(btn_info_json)
    except Exception:
        btn_info = {}
    log(f"按钮信息: wireId={btn_info.get('wireId')}, text={btn_info.get('btnText')}")

    wire_id = btn_info.get("wireId")
    if wire_id:
        log("策略1: Livewire extend (wire:id)")
        result = call_livewire_extend(driver, wire_id)
        log(f"  结果: {result}")
        if result == "called":
            return True

    # 策略2: 通用组件遍历
    log("策略2: Livewire 通用遍历")
    result = call_livewire_generic(driver)
    log(f"  结果: {result}")
    if result.startswith("called"):
        return True

    # 策略3: JS 原生 click
    log("策略3: JS 原生 click")
    result = native_click(driver)
    log(f"  结果: {result}")
    return result.startswith("clicked")


# ==================== 主流程 ====================
def main():
    servers = load_servers()
    log("========== Gaming4Free 自动续期 ==========")
    if not servers:
        log("未配置服务器信息，请设置环境变量 GAME4FREE_RENEW_URL + GAME4FREE_COOKIE")
        sys.exit(1)

    for server_name, server_url, server_cookie in servers:
        log(f"\n>>> 处理: {server_name}")

        done = False
        for attempt in range(MAX_BROWSER_RETRIES):
            if done:
                break
            try:
                log(f"启动浏览器 (第 {attempt+1}/{MAX_BROWSER_RETRIES} 次)...")
                with SB(uc=True, headless=False, browser="chrome",
                        agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36") as sb:
                    driver = sb.driver
                    driver.set_page_load_timeout(30)

                    # Cookie 注入
                    if server_cookie:
                        log("注入 Cookie...")
                        try:
                            driver.get("https://control.gaming4free.net/")
                        except Exception:
                            pass
                        time.sleep(2)
                        inject_cookies(driver, server_cookie, ".gaming4free.net")
                        time.sleep(1)

                    log(f"访问: {server_url}")
                    try:
                        driver.get(server_url)
                    except Exception:
                        driver.execute_script("window.stop();")
                    time.sleep(10)

                    # 登录状态检查
                    page_text = driver.execute_script(
                        "return document.body?document.body.innerText.substring(0,500):'';"
                    )
                    if "login" in page_text.lower() and "90" not in page_text:
                        log("Cookie 已过期，跳过")
                        send_tg("Cookie 已过期", server_name)
                        break

                    rnd = 0
                    while rnd < MAX_ROUNDS:
                        rnd += 1
                        log(f"\n--- 第 {rnd}/{MAX_ROUNDS} 轮 ---")

                        before_lt, before_ls = get_remaining_time(driver)
                        log(f"剩余时长: {before_lt} ({before_ls}秒)")

                        if before_ls >= TARGET_SECONDS:
                            log("目标时长已达标")
                            done = True
                            break

                        # 冷却检查
                        try:
                            pt = driver.execute_script("return document.body?document.body.innerText:'';")
                            if "05:00" in pt and "cd" in pt.lower():
                                log("冷却期 5 分钟，等待 310 秒...")
                                time.sleep(310)
                                driver.refresh()
                                time.sleep(10)
                                continue
                        except Exception:
                            pass

                        if not trigger_renew(driver):
                            log("所有触发策略失败，刷新重试...")
                            driver.refresh()
                            time.sleep(10)
                            continue

                        # 等待 Turnstile
                        time.sleep(5)
                        try:
                            for _ in range(30):
                                if not driver.find_elements("css selector",
                                                           'iframe[src*="challenges.cloudflare.com"]'):
                                    break
                                time.sleep(1)
                        except Exception:
                            pass

                        # 监测广告
                        log("监测广告...")
                        t0 = time.time()
                        while time.time() - t0 < 90:
                            driver.execute_script("window.dispatchEvent(new Event('mousemove'));")
                            try:
                                driver.execute_script("""
                                    document.querySelectorAll('[aria-label="Close"], .modal-close')
                                        .forEach(function(el) { if(el.offsetParent) el.click(); });
                                """)
                            except Exception:
                                pass
                            if time.time() - t0 > 30 and int(time.time() - t0) % 15 == 0:
                                _, ls = get_remaining_time(driver)
                                if ls > before_ls + 3000:
                                    log("时间已增加，提前结束等待")
                                    break
                            time.sleep(2)

                        # 刷新验证
                        log("刷新验证...")
                        driver.refresh()
                        time.sleep(12)
                        after_lt, after_ls = get_remaining_time(driver)
                        diff = after_ls - before_ls

                        if diff > 3000:
                            log(f"成功! {before_lt} -> {after_lt}")
                            send_tg(f"续期成功 (第{rnd}轮)", server_name, after_lt)
                            time.sleep(310)
                            driver.refresh()
                            time.sleep(10)
                        else:
                            log(f"失败, diff={diff}s")
                            try:
                                pt = driver.execute_script("return document.body?document.body.innerText:'';")
                                if "cd" in pt.lower():
                                    log("已进入冷却，等待 310 秒...")
                                    time.sleep(310)
                                    driver.refresh()
                                    time.sleep(10)
                            except Exception:
                                pass

                    log(f"账号 {server_name} 处理完成")
                    done = True

            except Exception as e:
                log(f"异常: {e}")
                traceback.print_exc()
                time.sleep(10)

    log("========== 全部完成 ==========")


if __name__ == "__main__":
    main()
