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

from libfinance import get_price_coverage

# 「最近 N 天」不能拿今天当 end_date：行情只到**最后一个已收盘交易日**，而交易日历是
# 提前发布的（能到年底）。两者覆盖范围不同，拿今天去查会被服务端拒绝：
#   "a date this release does not reach is not a date with no trading"
# 先问一句覆盖到哪天，再往前数。
coverage = get_price_coverage()
print("行情覆盖:", coverage)
end_date = min(v["end"] for v in coverage.values())
start_date = (
    datetime.date.fromisoformat(end_date) - datetime.timedelta(days=10)
).strftime("%Y-%m-%d")
print("查询区间:", start_date, "..", end_date)

instrument_ids = ["000001.XSHE","600000.XSHG"]
frequency = "1d"
fields = None
trading_data  = get_price(order_book_ids=instrument_ids,start_date=start_date, end_date=end_date, fields=fields, frequency=frequency)
print(trading_data)
