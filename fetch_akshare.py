import akshare as ak
import pandas as pd
import time

tech_pool = ['立讯精密', '工业富联', '歌尔股份', '蓝思科技', '中微公司', '北方华创', '长电科技', '通富微电', '传音控股', '水晶光电']

print("正在连接开源量化接口，向远端服务器发起请求...")
for i in range(3):
    try:
        # 获取沪深A股实时行情数据
        df = ak.stock_zh_a_spot_em()
        
        # 过滤出我们关注的硬科技股票池
        df_pool = df[df['名称'].isin(tech_pool)].copy()
        
        # 提取核心指标
        df_pool = df_pool[['代码', '名称', '最新价', '涨跌幅', '市盈率-动态', '总市值']]
        
        # 按动态市盈率从小到大排序
        df_pool = df_pool.sort_values(by='市盈率-动态')
        
        # 格式化市值显示为“亿元”
        df_pool['总市值'] = (df_pool['总市值'] / 100000000).round(2).astype(str) + '亿'
        
        print("\n--- 成功抓取到实时量化数据截面 ---")
        print(df_pool.to_markdown(index=False))
        break
    except Exception as e:
        print(f"尝试 {i+1} 失败，可能触发反爬虫或网络异常，等待3秒后重试... 详情: {e}")
        time.sleep(3)
