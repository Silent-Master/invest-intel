import sys
import urllib.request
import json

if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

def fetch_real_quotes():
    symbol_map = {
        'sh600519': {'id': '600519', 'market': 'A股', 'type': 'stock'},
        'sz300750': {'id': '300750', 'market': 'A股', 'type': 'stock'},
        'r_hk00700': {'id': '00700', 'market': '港股', 'type': 'stock'},
        'r_hk03690': {'id': '03690', 'market': '港股', 'type': 'stock'},
        'usNVDA': {'id': 'NVDA', 'market': '美股', 'type': 'stock'},
        'usMSFT': {'id': 'MSFT', 'market': '美股', 'type': 'stock'},
        'usTSM': {'id': 'TSM', 'market': '美股', 'type': 'stock'},
        'usQQQ': {'id': 'QQQ', 'market': '美股', 'type': 'stock'},
        's_sh000300': {'id': '000300', 'market': 'A股', 'type': 'index', 'name': '沪深300'},
        's_hkHSI': {'id': 'HSI', 'market': '港股', 'type': 'index', 'name': '恒生指数'},
        'us.IXIC': {'id': 'IXIC', 'market': '美股', 'type': 'index', 'name': '纳斯达克'},
        'whUSDCNY': {'id': 'USDCNY', 'market': '外汇', 'type': 'fx', 'name': '美元/人民币'}
    }

    url = 'http://qt.gtimg.cn/q=' + ','.join(symbol_map.keys())
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    
    with urllib.request.urlopen(req) as resp:
        raw = resp.read().decode('gbk', errors='ignore')

    results = {}
    for line in raw.strip().split(';'):
        line = line.strip()
        if not line or '=' not in line:
            continue
        var_name, val = line.split('=', 1)
        val = val.strip('\"')
        parts = val.split('~')
        code = var_name.replace('v_', '')
        if code not in symbol_map:
            continue
        
        meta = symbol_map[code]
        try:
            if meta['type'] == 'index':
                name = meta.get('name', parts[1])
                price = float(parts[3])
                if code.startswith('us'):
                    chg_amt = float(parts[31]) if len(parts) > 31 and parts[31] else 0.0
                    chg_pct = float(parts[32]) if len(parts) > 32 and parts[32] else 0.0
                else:
                    chg_amt = float(parts[4]) if len(parts) > 4 and parts[4] else 0.0
                    chg_pct = float(parts[5]) if len(parts) > 5 and parts[5] else 0.0
            elif meta['type'] == 'fx':
                name = meta.get('name', parts[1])
                price = float(parts[3])
                chg_amt = float(parts[12])
                chg_pct = float(parts[13])
            else:
                name = parts[1]
                price = float(parts[3])
                chg_amt = float(parts[31]) if len(parts) > 31 and parts[31] else 0.0
                chg_pct = float(parts[32]) if len(parts) > 32 and parts[32] else 0.0
            
            results[meta['id']] = {
                'raw_code': code,
                'name': name,
                'price': price,
                'chg_amt': chg_amt,
                'chg_pct': chg_pct,
                'market': meta['market'],
                'type': meta['type']
            }
        except Exception as e:
            print(f"Error parsing {code}: {e}")

    return results

if __name__ == '__main__':
    data = fetch_real_quotes()
    print(json.dumps(data, ensure_ascii=False, indent=2))
