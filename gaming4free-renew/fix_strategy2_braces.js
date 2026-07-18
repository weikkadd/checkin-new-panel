const fs = require('fs');
const path = 'C:\\Users\\ASUS\\Documents\\AgnesCode\\checkin-xuqi\\gaming4free-renew\\renew.py';
let c = fs.readFileSync(path, 'utf8');
c = c.replace(/\r\n/g, '\n');

// 找到策略2的JS块并修复：把三引号字符串里的 {{ }} 替换为 { }
// 因为这是普通字符串不是 f-string，{{ }} 不会被转义

const oldJs = `    js = \"\"\"
    (function() {{
        var btns = document.querySelectorAll('button');
        for (var i = 0; i < btns.length; i++) {{
            var text = btns[i].innerText || '';
            if (text.indexOf('90') !== -1) {{
                var disabled = btns[i].disabled || btns[i].getAttribute('aria-disabled') === 'true';
                var classes = btns[i].className || '';
                var isCooldown = classes.indexOf('disabled') !== -1 || classes.indexOf('cursor-not-allowed') !== -1 || disabled;
                var waitMatch = text.match(/Wait\\\\s*(\\\\d+)/i) || text.match(/(\\\\d+)\\\\s*s/);
                if (waitMatch) return {{cooldown: true, remaining: parseInt(waitMatch[1]), text: text.trim()}};
                if (isCooldown) return {{cooldown: true, disabled: true, text: text.trim()}};
                return {{cooldown: false, text: text.trim()}};
            }}
        }}
        return null;
    }})();
    \"\"\"`;

const newJs = `    js = \"\"\"
    (function() {
        var btns = document.querySelectorAll('button');
        for (var i = 0; i < btns.length; i++) {
            var text = btns[i].innerText || '';
            if (text.indexOf('90') !== -1) {
                var disabled = btns[i].disabled || btns[i].getAttribute('aria-disabled') === 'true';
                var classes = btns[i].className || '';
                var isCooldown = classes.indexOf('disabled') !== -1 || classes.indexOf('cursor-not-allowed') !== -1 || disabled;
                var waitMatch = text.match(/Wait\\\\s*(\\\\d+)/i) || text.match(/(\\\\d+)\\\\s*s/);
                if (waitMatch) return {cooldown: true, remaining: parseInt(waitMatch[1]), text: text.trim()};
                if (isCooldown) return {cooldown: true, disabled: true, text: text.trim()};
                return {cooldown: false, text: text.trim()};
            }
        }
        return null;
    })();
    \"\"\"`;

if (c.includes(oldJs)) {
    c = c.replace(oldJs, newJs);
    fs.writeFileSync(path, c, 'utf8');
    console.log('✅ Fixed strategy2 JS braces');
} else {
    console.log('❌ Pattern not found, trying regex approach');
    // Fallback: replace {{ and }} in the check_button_cooldown JS block
    const startIdx = c.indexOf('=== 策略2: 检查按钮本身的 disabled 状态 ===');
    const endIdx = c.indexOf('\"\"\"', startIdx + 500);
    if (startIdx >= 0 && endIdx >= 0) {
        const before = c.substring(0, startIdx);
        const jsBlock = c.substring(startIdx, endIdx + 3);
        const after = c.substring(endIdx + 3);
        // Replace {{ with { and }} with } only in the JS content
        const fixedJs = jsBlock.replace(/\\{\\{/g, '{').replace(/\\}\\}/g, '}');
        c = before + fixedJs + after;
        fs.writeFileSync(path, c, 'utf8');
        console.log('✅ Fixed via regex fallback');
    } else {
        console.log('Could not find boundaries');
    }
}
