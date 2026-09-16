#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import pandas as pd
from libfinance import get_price


instrument_ids = ["000001.XSHE"]
start_date = "2026-01-01"
end_date = "2026-03-11"
frequency = "1d"

fields = ["close","volume"]

trading_data  = get_price(order_book_ids=instrument_ids,start_date=start_date, end_date=end_date, fields=fields, frequency=frequency)
print(trading_data)
print("------------------------------")


instrument_ids = ["000001.XSHE","600000.XSHG"]
start_date = "2026-03-01"
end_date = "2026-03-11"
frequency = "1d"
fields = ['open', 'high', 'low', 'close', 'volume']
trading_data  = get_price(order_book_ids=instrument_ids,start_date=start_date, end_date=end_date, fields=fields, frequency=frequency)
print(trading_data)


import datetime
from dateutil.relativedelta import relativedelta  # 可选，但这里用 timedelta 即可

# 动态获取今天的日期
today = datetime.date.today()
end_date = today.strftime("%Y-%m-%d")
# 计算10天前的日期（自然日）
start_date = (today - datetime.timedelta(days=10)).strftime("%Y-%m-%d")

instrument_ids = ["000001.XSHE","600000.XSHG"]
frequency = "1d"
fields = None
trading_data  = get_price(order_book_ids=instrument_ids,start_date=start_date, end_date=end_date, fields=fields, frequency=frequency)
print(trading_data)
