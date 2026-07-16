import os
import json
import datetime
import pandas as pd
import akshare as ak

# 我们定义的 18 个核心概念池（左侧为你想要的展示名称，右侧为东方财富对应的真实概念名称）
CONCEPT_MAPPING = {
    "PCB概念": "PCB概念",
    "创新药": "创新药",
    "共封装光学(CPO)": "共封装光学(CPO)",
    "商业航天": "商业航天",
    "存储芯片": "存储芯片",
    "人形机器人": "人形机器人",
    "光纤概念": "光纤概念",
    "先进封装": "先进封装",
    "算力租赁": "算力租赁",
    "消费电子": "消费电子概念",
    "白酒": "白酒",
    "低空经济": "低空经济",
    "人工智能": "人工智能",
    "半导体设备": "芯片概念",
    "黄金概念": "黄金概念",
    "CRO概念": "CRO概念",
    "液冷服务器": "液冷服务器",
    "AI应用": "AI应用"
}

def fetch_data():
    """通过 akshare 直连获取全市场概念板块资金净流向（绝对值，亿元）"""
    try:
        # 获取东方财富实时概念板块资金流向数据
        df = ak.stock_fund_flow_concept(symbol='即时')
    except Exception as e:
        print(f"数据抓取失败: {e}")
        return None
        
    concept_results = []
    
    for display_name, api_name in CONCEPT_MAPPING.items():
        # 在返回的 DataFrame 中匹配对应的概念名称
        row = df[df['行业'] == api_name]
        if not row.empty:
            # 提取 '净额' (亿元) 字段，处理 NaN 情况
            net_amount = row['净额'].values[0]
            if pd.isna(net_amount):
                net_amount = 0.0
            
            concept_results.append({
                "name": display_name,
                "value": round(float(net_amount), 2)
            })
        else:
            # 如果某个概念在 API 中未找到（比如周末或节假日数据缺失），默认给 0
            concept_results.append({
                "name": display_name,
                "value": 0.0
            })
            
    # 按资金净流入绝对值从高到低排序，直接全展示
    concept_results.sort(key=lambda x: x['value'], reverse=True)
    return concept_results

def update_history():
    history_file = 'concept_history.json'
    now = datetime.datetime.now()
    today_str = now.strftime("%Y-%m-%d")
    time_str = now.strftime("%H:%M")
    
    # 盘中运行验证限制 (测试期间可注释)
    # if not (9 <= now.hour <= 15): print("非交易时间"); return
    
    current_data = fetch_data()
    if not current_data:
        return
        
    history_data = []
    if os.path.exists(history_file):
        try:
            with open(history_file, 'r', encoding='utf-8') as f:
                history_data = json.load(f)
                # 跨日清空机制：如果发现 JSON 里的数据不是今天的，则清空重新开始记录
                if history_data and history_data[0].get('date') != today_str:
                    print("检测到新交易日，已清空昨日历史数据。")
                    history_data = []
        except:
            pass
            
    existing = [x for x in history_data if x['time'] == time_str]
    if existing:
        existing[0]['data'] = current_data
    else:
        history_data.append({
            "date": today_str,
            "time": time_str,
            "data": current_data
        })
        
    history_data.sort(key=lambda x: x['time'])
    
    with open(history_file, 'w', encoding='utf-8') as f:
        json.dump(history_data, f, ensure_ascii=False, indent=2)
        
    # 保存为 JS 便于前端离线加载
    with open('concept_history.js', 'w', encoding='utf-8') as f:
        f.write('window.HISTORY_DATA = ' + json.dumps(history_data, ensure_ascii=False) + ';')
        
    print(f"[{time_str}] 成功更新绝对资金流向！领涨板块: {current_data[0]['name']} ({current_data[0]['value']}亿)")

if __name__ == '__main__':
    update_history()
