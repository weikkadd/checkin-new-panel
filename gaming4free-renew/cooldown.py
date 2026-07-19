def check_button_cooldown(sb):
    try:
        page_text = sb.execute_script("return document.body?document.body.innerText.substring(0,2000):'';")
        if not page_text:
            return None
        import re
        exp_no_ampm = re.search(r'expires\s+(\d{1,2}:\d{2})(?!\s*[APap][Mm])', page_text, re.I)
        if exp_no_ampm:
            hhmm = exp_no_ampm.group(1)
            parts = hhmm.split(':')
            if len(parts) == 2:
                hours = int(parts[0])
                minutes = int(parts[1])
                remaining_sec = hours * 3600 + minutes * 60
                log(f"⏳ 检测到冷却 (expires): {hhmm} (剩余 {remaining_sec}秒)")
                return {'cooldown': True, 'remaining': remaining_sec, 'text': hhmm}
        cd_match = re.search(r'(\d+):(\d+)\s+cd', page_text, re.I)
        if cd_match:
            mins = int(cd_match.group(1))
            secs = int(cd_match.group(2))
            remaining_sec = mins * 60 + secs
            log(f"⏳ 检测到按钮冷却倒计时: {cd_match.group(0).strip()} (剩余 {remaining_sec}秒)")
            return {'cooldown': True, 'remaining': remaining_sec, 'text': cd_match.group(0).strip()}
        try:
            disabled = bool(sb.execute_script("""
                var btns = document.querySelectorAll('button');
                for (var i = 0; i < btns.length; i++) {
                    var txt = (btns[i].innerText || btns[i].textContent || '').trim();
                    if (txt.indexOf('90') !== -1 || txt.indexOf('+ 90') !== -1 || txt.indexOf('+90') !== -1) {
                        return btns[i].disabled;
                    }
                }
                return false;
            """))
            if disabled:
                log("⏳ 检测到按钮 disabled 状态")
                return {'cooldown': True, 'remaining': 0, 'text': 'disabled'}
        except:
            pass
        return None
    except Exception as e:
        log(f"⚠️ 检查按钮冷却失败: {e}")
        return None
