import akshare as ak
import pandas as pd

try:
    df = ak.stock_zh_a_hist(symbol='002475', period='daily', start_date='20260601', adjust='qfq')
    print('--- Price Data ---')
    print(df.tail(10).to_string())
except Exception as e:
    print('Error fetching price data:', e)

try:
    ind = ak.stock_a_indicator_lg(symbol='002475')
    print('\n--- Valuation ---')
    print(ind.tail(1).to_string())
except Exception as e:
    print('Error fetching valuation:', e)
