#!/usr/bin/env python3
import os, time, urllib.request, urllib.parse, re
from seleniumbase import SB

TG_CHAT_ID = os.environ.get("TG_CHAT_ID", "").strip()
TG_TOKEN = os.environ.get("TG_BOT_TOKEN", "").strip()

raw_accounts = os.environ.get("GAME4FREE_ACCOUNT", "").strip().splitlines()
ACCOUNTS = []
for line in raw_accounts:
    line = line.strip()
    if not line: continue
    parts = line.split(",", 1)
    if len(parts) == 2: ACCOUNTS.append((parts[0].strip(), parts[1].strip()))

AD_WAIT_SEC = 100
SCREENSHOT_DIR = "/tmp/g4f-debug"
POLLING_METHODS = ('$refresh', 'refresh', 'poll', '$poll')

def log(msg): print(f"{msg}", flush=True)

def screenshot(sb, name):
    try:
        os.makedirs(SCREENSHOT_DIR, exist_ok=True)
        sb.save_screenshot(f"{SCREENSHOT_DIR}/{name}.png")
    except: pass

def send_tg(result, server_name="", expiry=""):
    if not TG_TOKEN or not TG_CHAT_ID: return
    import datetime
    msg = f"🎮Game4Free 续期通知\n⏰运行时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n🖥️服务器: {server_name}\n"
    if expiry: msg += f"🔢剩余时间: {expiry}\n"
    msg += f"📊续期结果: {result}"
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    data = urllib.parse.urlencode({"chat_id": TG_CHAT_ID, "text": msg}).encode()
    try:
        req = urllib.request.Request(url, data=data, method="POST")
        with urllib.request.urlopen(req, timeout=15): log("📨 TG推送成功")
    except Exception as e: log(f"⚠️ TG推送失败: {e}")

def parse_countdown_seconds(text):
    if not text: return 0
    text = text.strip()
    parts = text.split(":")
    if len(parts) == 3:
        try: return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
        except: pass
    h = re.search(r'(\d+)\s*h', text, re.I)
    m = re.search(r'(\d+)\s*m', text, re.I)
    total = 0
    if h: total += int(h.group(1)) * 3600
    if m: total += int(m.group(1)) * 60
    return total

def get_remaining_time(sb):
    try:
        selectors = ['[class*="timer"]', '[class*="remaining"]', '[class*="countdown"]', '#sd-timer']
        for sel in selectors:
            try:
                text = sb.execute_script(f"var el=document.querySelector('{sel}'); return el?el.textContent.trim():'';")
                if text and len(text) < 30:
                    secs = parse_countdown_seconds(text)
                    if secs > 0: return text, secs
            except: continue
        page_text = sb.execute_script("return document.body?document.body.innerText:'';")
        if page_text:
            match = re.search(r'(\d{1,2}:\d{2}:\d{2})', page_text)
            if match: return match.group(1), parse_countdown_seconds(match.group(1))
            match = re.search(r'(\d+h\s*\d+m)', page_text, re.I)
            if match: return match.group(1), parse_countdown_seconds(match.group(1))
    except: pass
    return "", 0

def close_modals(sb):
    sels = ['button:contains("Maybe later")', '.modal-close', '[aria-label="Close"]']
    for sel in sels:
        try:
            if sb.execute_script(f"return !!document.querySelector('{sel}');"):
                sb.click(sel); log(f"🛡️ 已关闭弹窗: {sel}"); time.sleep(1)
        except: continue

def check_button_cooldown(sb):
    js = """(function(){var btns=document.querySelectorAll('button');for(var i=0;i<btns.length;i++){var t=btns[i].innerText||'';if(t.indexOf('90')!==-1){var d=btns[i].disabled;var c=btns[i].className||'';var cd=c.indexOf('disabled')!==-1||c.indexOf('cursor-not-allowed')!==-1||d;var w=t.match(/Wait\\s*(\\d+)/i)||t.match(/(\\d+)\\s*s/);if(w)return{cooldown:true,remaining:parseInt(w[1]),text:t.trim()};if(cd)return{cooldown:true,disabled:true,text:t.trim()};return{cooldown:false,text:t.trim()}}}return null})();"""
    try: return sb.execute_script(js)
    except: return None

def handle_turnstile(sb, max_retries=3):
    for attempt in range(max_retries):
        try:
            if sb.find_elements('iframe[src*="cloudflare"]') or sb.find_elements('iframe[src*="turnstile"]'):
                log(f"🛡️ 检测到 Turnstile (尝试 {attempt+1}/{max_retries})")
                screenshot(sb, f"turnstile-{attempt}")
                try:
                    sb.uc_gui_click_captcha(); log("✅ uc_gui_click_captcha 已执行"); time.sleep(5); return True
                except Exception as e: log(f"⚠️ uc_gui_click_captcha 失败: {e}")
        except: pass
        time.sleep(2)
    return False

def read_alpine_state(sb):
    js = """(function(){var btn=null;var all
