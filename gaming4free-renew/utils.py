import os, re
from datetime import datetime

def log(msg):
    ts = datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
    print(f"{ts} {msg}")

def screenshot(sb, name="screenshot"):
    try:
        out_dir = os.path.join(os.path.dirname(__file__), "debug_output")
        os.makedirs(out_dir, exist_ok=True)
        path = os.path.join(out_dir, f"{name}.png")
        sb.save_screenshot(path)
        log(f"📸 截图已保存至 {path}")
    except:
        pass

def parse_countdown_seconds(match_str):
    if not match_str:
        return 0
    m = re.match(r'(\d+):(\d+):(\d+)', match_str)
    if m:
        return int(m.group(1))*3600 + int(m.group(2))*60 + int(m.group(3))
    m = re.match(r'(\d+)\s*m', match_str, re.I)
    if m:
        return int(m.group(1)) * 60
    m = re.match(r'(\d+)\s*h', match_str, re.I)
    if m:
        return int(m.group(1)) * 3600
    return 0

def get_remaining_time(sb):
    try:
        page_text = sb.execute_script("return document.body?document.body.innerText.substring(0,2000):'';")
        if not page_text:
            return ("(未知)", 0)
        time_matches = re.findall(r'(\d{1,2}:\d{2}:\d{2})', page_text)
        if time_matches:
            lt = time_matches[0]
            ls = parse_countdown_seconds(lt)
            return (lt, ls)
        return ("(未找到)", 0)
    except Exception as e:
        log(f"⚠️ 获取时间失败: {e}")
        return ("(错误)", 0)
