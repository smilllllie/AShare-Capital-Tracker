import requests
import pandas as pd

symbols = [
    'sz300308', # 中际旭创 (CPO)
    'sz300502', # 新易盛 (CPO)
    'sz300394', # 天孚通信 (CPO)
    'sh601698', # 中国卫通 (商业航天)
    'sh600118', # 中国卫星 (商业航天)
    'sh600879'  # 航天电子 (商业航天)
]

url = "http://qt.gtimg.cn/q=" + ",".join(symbols)

try:
    response = requests.get(url, timeout=5)
    data = response.text.strip().split(';')
    
    results = []
    for line in data:
        if not line: continue
        parts = line.split('=')[1].replace('"', '').split('~')
        if len(parts) > 40:
            name = parts[1]
            code = parts[2]
            price = float(parts[3])
            pct_change = float(parts[32])
            pe_ttm = float(parts[39]) if parts[39] else 0.0
            market_cap = float(parts[45])
            
            sector = "CPO光模块" if code in ['300308', '300502', '300394'] else "商业航天"
            
            results.append({
                '板块': sector,
                '代码': code,
                '名称': name,
                '最新价': price,
                '涨跌幅(%)': pct_change,
                '动态市盈率': pe_ttm,
                '总市值(亿)': market_cap
            })
            
    df = pd.DataFrame(results)
    df = df.sort_values(by=['板块', '动态市盈率'])
    print("\n--- CPO与商业航天板块核心标的量化数据 ---")
    print(df.to_markdown(index=False))
except Exception as e:
    print(f"Error: {e}")
