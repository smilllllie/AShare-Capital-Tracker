import requests
import pandas as pd
import sys
import io

# 修复 Windows 控制台下打印乱码的问题
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 股票池：深市加sz，沪市加sh
symbols = [
    # 电池与新能源
    'sz300750', # 宁德时代 (电池王)
    'sz002594', # 比亚迪 (整车与电池)
    'sz300274', # 阳光电源 (储能逆变器)
    'sz300014', # 亿纬锂能 (二线电池龙头)
    'sh603659', # 璞泰来 (负极材料)
    'sz002709', # 天赐材料 (电解液)
    # AI硬件与PCB/CCL (根据你的量化分析策略补充)
    'sh601138', # 工业富联 (AI服务器)
    'sz002463', # 沪电股份 (AI服务器PCB)
    'sz300308', # 中际旭创 (光模块龙头)
    # 消费电子
    'sz002475'  # 立讯精密 (果链龙头)
]

url = "http://qt.gtimg.cn/q=" + ",".join(symbols)

try:
    print("正在通过腾讯财经底层API抓取量化指标...")
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
            pe_ttm = float(parts[39]) if parts[39] else 0.0 # 39是动态市盈率
            pb = float(parts[46]) if parts[46] else 0.0 # 46是市净率
            market_cap = float(parts[45]) # 45是总市值(亿)
            
            results.append({
                '代码': code,
                '名称': name,
                '最新价': price,
                '涨跌幅(%)': pct_change,
                '动态市盈率': pe_ttm,
                '总市值(亿)': market_cap,
                '市净率': pb
            })
            
    df = pd.DataFrame(results)
    
    # 区分高估和低估（简单粗暴加个判断，配合你的波段交易思路）
    df['估值状态'] = df['动态市盈率'].apply(lambda x: '低估' if 0 < x < 25 else ('高估' if x > 45 else '合理'))
    
    df = df.sort_values(by='涨跌幅(%)', ascending=False) # 按涨跌幅排序，看看今天谁最猛
    print("\n--- 成功抓取到实时量化数据截面 ---")
    print(df.to_markdown(index=False))
except Exception as e:
    print(f"抓取失败: {e}")
