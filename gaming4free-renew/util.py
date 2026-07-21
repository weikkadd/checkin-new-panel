import os,re,json
from datetime import datetime
def log(msg):
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}")
def scr(sb,name="s"):
    try:
        d=os.path.join(os.path.dirname(__file__),"debug_output")
        os.makedirs(d,exist_ok=True)
        sb.save_screenshot(os.path.join(d,f"{name}.png"))
    except: pass
def pars_s(ms):
    if not ms: return 0
    m=re.match(r'(\d+):(\d+):(\d+)',ms)
    if m: return int(m.group(1))*3600+int(m.group(2))*60+int(m.group(3))
    m=re.match(r'(\d+)\s*m',ms,re.I)
    if m: return int(m.group(1))*60
    m=re.match(r'(\d+)\s*h',ms,re.I)
    if m: return int(m.group(1))*3600
    return 0

# ============================================================
# Livewire v3/v4 组件遍历与方法调用的 JavaScript
# 使用普通字符串（非模板字串）避免 Python f-string 冲突
# ============================================================

_LW_DIAGNOSE_JS = """
var info = {};
try {
    info.livewire_exists = !!window.Livewire;
    info.has_components = !!(window.Livewire && window.Livewire.components);
    info.has_all = typeof window.Livewire.all === 'function';
    info.has_dispatch = typeof window.Livewire.dispatch === 'function';
    info.components_all_fn = typeof (window.Livewire && window.Livewire.components && window.Livewire.components.all) === 'function';

    // Livewire v3/v4 组件信息
    var compInfo = [];
    if (window.Livewire && window.Livewire.components && typeof window.Livewire.components.all === 'function') {
        var comps = window.Livewire.components.all();
        info.v3_comps_count = comps.length;
        for (var i = 0; i < comps.length; i++) {
            var c = comps[i];
            var ci = {
                idx: i,
                name: c.name || (c.__instance && c.__instance.name) || 'unknown',
                id: c.id || (c.__instance && c.__instance.id) || 'unknown',
                has_wire: !!c.$wire,
                wire_methods: [],
                data_keys: [],
                snapshot_keys: []
            };
            try {
                if (c.$wire) {
                    ci.wire_methods = Object.keys(c.$wire).filter(function(k){
                        return typeof c.$wire[k] === 'function';
                    }).slice(0, 20);
                }
                if (c.snapshot && c.snapshot.data) {
                    ci.data_keys = Object.keys(c.snapshot.data).slice(0, 20);
                }
                if (c.__instance && c.__instance.snapshot && c.__instance.snapshot.data) {
                    ci.snapshot_keys = Object.keys(c.__instance.snapshot.data).slice(0, 20);
                }
            } catch(e) {}
            compInfo.push(ci);
        }
    }
    info.components = compInfo;

    // 页面按钮信息
    var wireBtns = document.querySelectorAll('[wire\\\\:click]');
    info.wire_click_buttons = [];
    for (var i = 0; i < Math.min(wireBtns.length, 20); i++) {
        info.wire_click_buttons.push(wireBtns[i].getAttribute('wire:click'));
    }

    var allBtns = document.querySelectorAll('button, [role=button]');
    info.total_buttons = allBtns.length;
    info.button_texts = [];
    for (var i = 0; i < Math.min(allBtns.length, 20); i++) {
        var t = (allBtns[i].innerText || allBtns[i].textContent || '').trim();
        if (t) info.button_texts.push(t.substring(0, 80));
    }
} catch(e) {
    info.error = e.message;
}
return JSON.stringify(info);
"""

_LW_EXTEND_V3_JS = """
var result = 'fail';
try {
    if (window.Livewire && window.Livewire.components &&
        typeof window.Livewire.components.all === 'function') {
        var comps = window.Livewire.components.all();
        for (var i = 0; i < comps.length; i++) {
            var comp = comps[i];
            var compName = comp.name || (comp.__instance && comp.__instance.name) || 'unknown';
            try {
                // 方法1: $wire.$call (Livewire v3 标准)
                if (comp.$wire && typeof comp.$wire.$call === 'function') {
                    comp.$wire.$call('extend');
                    return 'v3_wire_call:' + compName;
                }
            } catch(e) {}
            try {
                // 方法2: $wire 上直接有 extend 方法
                if (comp.$wire && typeof comp.$wire.extend === 'function') {
                    comp.$wire.extend();
                    return 'v3_wire_extend:' + compName;
                }
            } catch(e) {}
            try {
                // 方法3: 组件实例上有 extend 方法
                if (typeof comp.extend === 'function') {
                    comp.extend();
                    return 'v3_direct:' + compName;
                }
            } catch(e) {}
        }
    }
} catch(e) {}
return result;
"""

_LW_DISPATCH_JS = """
var result = 'fail';
try {
    if (window.Livewire && typeof window.Livewire.dispatch === 'function') {
        window.Livewire.dispatch('extend');
        return 'dispatch_extend';
    }
} catch(e) {}
return result;
"""

_LW_V2_JS = """
var result = 'fail';
try {
    if (window.Livewire && typeof window.Livewire.all === 'function') {
        var comps = window.Livewire.all;
        if (comps && comps.length > 0) {
            for (var i = 0; i < comps.length; i++) {
                try {
                    comps[i].call('extend');
                    return 'v2_call:' + i;
                } catch(e) {}
            }
        }
    }
} catch(e) {}
return result;
"""

_LW_CLICK_JS = """
var result = 'fail';
try {
    // 查找所有带 wire:click 属性的元素
    var btns = document.querySelectorAll('[wire\\\\:click]');
    for (var i = 0; i < btns.length; i++) {
        var val = btns[i].getAttribute('wire:click');
        if (val && (val.indexOf('extend') !== -1 || val.indexOf('renew') !== -1 || val.indexOf('refresh') !== -1)) {
            btns[i].click();
            return 'wire_click:' + val;
        }
    }
    // 备用: 查找按钮文字包含 90 和 min 的元素
    var allBtns = document.querySelectorAll('button, [role=button], [class*="btn"], [class*="Btn"], a[href*="extend"], a[href*="renew"]');
    for (var i = 0; i < allBtns.length; i++) {
        var t = (allBtns[i].innerText || allBtns[i].textContent || '').trim();
        if (t.indexOf('90') !== -1 && t.indexOf('min') !== -1) {
            allBtns[i].click();
            return 'text_click:' + t.substring(0, 50);
        }
    }
} catch(e) {
    return 'click_err:' + e.message;
}
return result;
"""

_GET_TIME_JS = """
var result='';
try{
    // Livewire v3+: 使用 components.all()
    if(window.Livewire && window.Livewire.components && typeof window.Livewire.components.all === 'function'){
        var comps=window.Livewire.components.all();
        window._lw_comps_count=comps.length;
        for(var i=0;i<comps.length;i++){
            try{
                var c=comps[i];
                var data={};
                // 从 snapshot.data 获取
                if(c.snapshot && c.snapshot.data){
                    data=Object.assign({},data,c.snapshot.data);
                }
                // 从 __instance 获取
                if(c.__instance && c.__instance.snapshot && c.__instance.snapshot.data){
                    data=Object.assign({},data,c.__instance.snapshot.data);
                }
                var allKeys=Object.keys(data);
                // 调试: 存储第一个组件的所有键名
                if(i===0){
                    window._livewire_keys=allKeys.join(',');
                    window._lw_component_names=comps.map(function(x){
                        try{return x.name||(x.__instance&&x.__instance.name)||'?';}catch(e){return '?';}
                    }).join(',');
                }
                for(var j=0;j<allKeys.length;j++){
                    var k=allKeys[j].toLowerCase();
                    if(k.indexOf('expire')!==-1||k.indexOf('remain')!==-1||k.indexOf('time')!==-1||k.indexOf('duration')!==-1){
                        var v=data[allKeys[j]];
                        if(typeof v==='string'&&v.match(/\\d+:\\d+/)){
                            result=v;
                            window._lw_found_key=allKeys[j];
                            break;
                        }
                    }
                }
                if(result) break;
            }catch(e){
                window._lw_err='comp_err:'+e.message;
            }
        }
    }
    // Livewire v2 兼容
    if(!result && window.Livewire && typeof window.Livewire.all === 'function'){
        var c2=window.Livewire.all;
        if(c2){
            for(var i=0;i<c2.length;i++){
                try{
                    var data=c2[i].data;
                    if(data && data.expires){result=data.expires;break;}
                    if(data && data.remaining){result=data.remaining;break;}
                    if(data && data.server_time){result=data.server_time;break;}
                }catch(e){}
            }
        }
    }
}catch(e){
    window._lw_err='outer_err:'+e.message;
}
return result||'';
"""

def get_time(dr):
    """从页面提取服务器到期时间（秒）和显示字符串"""
    try:
        # 方法1: 尝试从 Livewire 组件数据中获取
        pt=dr.execute_script(_GET_TIME_JS)
        if pt:
            secs=pars_s(pt)
            if secs>0:
                h,m,s=secs//3600,(secs%3600)//60,secs%60
                log(f"✅ 从 Livewire 数据获取: {pt} ({secs}s)")
                return(f"{h:02d}:{m:02d}:{s:02d}",secs)
        
        # 诊断：打印 Livewire 键名
        lk=dr.execute_script("return window._livewire_keys||'';")
        if lk: log(f"🔑 Livewire data keys: {lk}")
        # 诊断：组件数量
        cc=dr.execute_script("return window._lw_comps_count||'';")
        if cc: log(f"🔧 Livewire 组件数量: {cc}")
        # 诊断：组件名称
        cn=dr.execute_script("return window._lw_component_names||'';")
        if cn: log(f"🔧 Livewire 组件名称: {cn}")
        # 诊断：错误信息
        er=dr.execute_script("return window._lw_err||'';")
        if er: log(f"⚠️ Livewire 诊断错误: {er}")
        
        # 方法2: 从页面文本中提取
        pt=dr.execute_script("return document.body?document.body.innerText.substring(0,3000):'';")
        if not pt: return("(未知",0)
        
        # 找包含 "remaining" 的行（这是服务器到期时间）
        for line in pt.split('\n'):
            ll=line.lower()
            if 'remaining' in ll:
                lt=re.findall(r'(\d{1,2}:\d{2}:\d{2})',line)
                if lt:
                    log(f"✅ remaining 行: {lt[0]} (行: {line.strip()[:100]})")
                    return(lt[0],pars_s(lt[0]))
        
        # 回退: 找第一个 >= 1小时的时间（过滤短倒计时如 00:03:00）
        tm=re.findall(r'(\d{1,2}:\d{2}:\d{2})',pt)
        valid=[t for t in tm if pars_s(t)>=3600]
        if valid:
            best=max(valid,key=pars_s)
            log(f"🔍 所有匹配时间: {tm}, 选中最大有效: {best} ({pars_s(best)}s)")
            for line in pt.split('\n'):
                if best in line:
                    log(f"📍 时间上下文: [{line.strip()}]")
                    break
            return(best,pars_s(best))
        
        log(f"⚠️ 未找到有效时间, 所有匹配: {tm}")
        return("(未找到)",0)
    except Exception as e:
        log(f"❌ get_time 错误: {e}")
        return("(错误)",0)

def livewire_extend(dr, su=None):
    """
    尝试通过 Livewire 调用 extend/renew 方法。
    支持 Livewire v3/v4 和 v2 两种 API。
    四层策略:
      1. Livewire v3 $wire.$call / $wire.extend
      2. Livewire.dispatch 全局事件
      3. Livewire v2 c.call('extend')
      4. wire:click 按钮点击 / 文字匹配点击
    返回 (success: bool, method_used: str)
    """
    # 第一层: Livewire v3/v4 $wire.$call
    lr = dr.execute_script(_LW_EXTEND_V3_JS)
    if lr.startswith('v3_'):
        log(f"✅ Livewire v3 extend 成功: {lr}")
        return (True, lr)

    # 第二层: Livewire.dispatch 全局事件
    lr2 = dr.execute_script(_LW_DISPATCH_JS)
    if lr2 == 'dispatch_extend':
        log(f"✅ Livewire dispatch 成功: {lr2}")
        return (True, lr2)

    # 第三层: Livewire v2 API (兼容旧版本)
    lr3 = dr.execute_script(_LW_V2_JS)
    if lr3.startswith('v2_'):
        log(f"✅ Livewire v2 extend 成功: {lr3}")
        return (True, lr3)

    # 第四层: wire:click 按钮点击 / 文字匹配
    lr4 = dr.execute_script(_LW_CLICK_JS)
    if lr4.startswith('wire_click:') or lr4.startswith('text_click:'):
        log(f"✅ 按钮点击成功: {lr4}")
        return (True, lr4)

    # 全部失败: 打印详细诊断信息
    diag_raw = dr.execute_script(_LW_DIAGNOSE_JS)
    try:
        d = json.loads(diag_raw)
        log(f"🔍 诊断: Livewire存在={d.get('livewire_exists')}, "
            f"v3_components={d.get('v3_comps_count',0)}, "
            f"dispatch={d.get('has_dispatch')}, "
            f"wire:click按钮={d.get('wire_click_buttons',[])}")
        log(f"🔍 诊断: 总按钮数={d.get('total_buttons',0)}, "
            f"按钮文字={d.get('button_texts',[])}")
        if d.get('components'):
            for c in d['components']:
                log(f"🔍 诊断: 组件[{c['idx']}] name={c['name']}, "
                    f"has_wire={c['has_wire']}, wire方法={c['wire_methods']}, "
                    f"data_keys={c['data_keys']}")
    except:
        log(f"🔍 诊断原始: {diag_raw[:500]}")

    return (False, lr4)
