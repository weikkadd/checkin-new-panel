import urllib.request,urllib.parse
from datetime import datetime
from util import log
from cfg import *
def send_tg(msg,sn="",tt=""):
    if not TG_BOT or not TG_CHAT: return
    try:
        now=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # 截断消息防止超过 Telegram 4096 字符限制
        safe_msg = msg[:2000]
        safe_tt = tt[:500] if tt else ""
        safe_sn = sn[:50] if sn else ""
        t=f"Gaming4Free Pro\n服务器: {safe_sn}\n时间: {now}\n状态: {safe_msg}\n剩余: {safe_tt}\n模式: Renew-Pro v30"
        u=f"https://api.telegram.org/bot{TG_BOT}/sendMessage"
        # 只编码值部分，不编码整个 URL
        data = f"chat_id={urllib.parse.quote(TG_CHAT)}&text={urllib.parse.quote(t)}".encode()
        urllib.request.urlopen(urllib.request.Request(u,data=data,headers={"Content-Type":"application/x-www-form-urlencoded"}),timeout=10)
        log(f"TG 通知成功")
    except Exception as e:
        log(f"TG 失败: {e}")
