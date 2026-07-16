import akshare as ak
import pandas as pd

def fetch_data():
    try:
        # 1. 获取“消费电子”板块的成分股
        print("正在获取东方财富“消费电子”板块成分股...")
        ce_stocks = ak.stock_board_industry_cons_em(symbol="消费电子")
        
        # 2. 获取A股所有股票的实时行情数据（包含动态市盈率等）
        print("正在获取全市场实时数据，进行数据融合...")
        all_stocks = ak.stock_zh_a_spot_em()
        
        # 3. 数据融合：将成分股与实时行情结合
        merged_df = pd.merge(ce_stocks[['代码', '名称']], all_stocks[['代码', '最新价', '涨跌幅', '市盈率-动态', '总市值']], on='代码', how='inner')
        
        # 4. 数据过滤与排序：剔除亏损（PE<=0），筛选出 PE 处于合理区间且较低的股票
        valid_stocks = merged_df[(merged_df['市盈率-动态'] > 0) & (merged_df['市盈率-动态'] < 100)].copy()
        
        # 转换总市值为亿元
        valid_stocks['总市值(亿)'] = round(valid_stocks['总市值'] / 100000000, 2)
        
        # 按市盈率从小到大排序，取前 10 名
        top_value_stocks = valid_stocks.sort_values(by='市盈率-动态', ascending=True).head(10)
        
        print("\n==================================================")
        print("【量化结果】消费电子板块 - 动态市盈率最低的 Top 10 公司")
        print("==================================================")
        # 格式化输出
        out_df = top_value_stocks[['代码', '名称', '最新价', '涨跌幅', '市盈率-动态', '总市值(亿)']]
        print(out_df.to_string(index=False))
        
    except Exception as e:
        print(f"数据获取失败: {e}")

if __name__ == "__main__":
    fetch_data()
