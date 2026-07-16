import akshare as ak
import pandas as pd
import warnings
warnings.filterwarnings('ignore')

try:
    print("正在拉取底层数据，请稍候...\n")
    
    # 1. 获取消费电子板块成分股
    sector_stocks = ak.stock_board_industry_cons_em(symbol="消费电子")
    sector_codes = sector_stocks['代码'].tolist()
    
    # 2. 获取实时行情（包含动态市盈率）
    spot_data = ak.stock_zh_a_spot_em()
    spot_data = spot_data[spot_data['代码'].isin(sector_codes)]
    spot_data = spot_data[['代码', '名称', '最新价', '市盈率-动态', '总市值']]
    
    # 3. 获取最近一期业绩报表 (2026年一季报)
    try:
        yj_data = ak.stock_yjbb_em(date="20260331")
    except:
        try:
            yj_data = ak.stock_yjbb_em(date="20251231")
        except:
            yj_data = pd.DataFrame(columns=['股票代码', '净利润-同比增长'])
            
    if not yj_data.empty:
        yj_data = yj_data[['股票代码', '净利润-同比增长']]
        yj_data.rename(columns={'股票代码': '代码'}, inplace=True)
        
        # 4. 合并数据
        merged = pd.merge(spot_data, yj_data, on='代码', how='inner')
        
        # 5. 数据清洗与排序：市盈率在0-40之间（估值不虚高），按净利润增长排序
        merged['市盈率-动态'] = pd.to_numeric(merged['市盈率-动态'], errors='coerce')
        merged['净利润-同比增长'] = pd.to_numeric(merged['净利润-同比增长'], errors='coerce')
        
        # 过滤
        valid_stocks = merged[(merged['市盈率-动态'] > 0) & (merged['市盈率-动态'] <= 40)].copy()
        
        # 按利润增速降序排列
        top_growth = valid_stocks.sort_values(by='净利润-同比增长', ascending=False).head(3)
        
        print("【消费电子板块：低估值 + 业绩反转 Top 3 标的客观数据】")
        print("数据提取时间：最新实时")
        print("-" * 50)
        print(top_growth.to_markdown(index=False))
        print("-" * 50)
    else:
        print("未获取到业绩数据。")

except Exception as e:
    print(f"数据抓取失败: {e}")
