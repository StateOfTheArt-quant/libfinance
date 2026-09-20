#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import pandas as pd
from libfinance import get_price


order_book_ids = ["AAPL.US"]
start_date = "2026-01-01"
end_date = "2026-03-11"
frequency = "1d"

fields = ["close","volume"]

trading_data  = get_price(order_book_ids=order_book_ids,start_date=start_date, end_date=end_date, fields=fields, frequency=frequency)
print(trading_data)
print("------------------------------")


order_book_ids = ["AAPL.US","NVDA.US"]
start_date = "2026-03-01"
end_date = "2026-03-11"
frequency = "1d"
fields = ['open', 'high', 'low', 'close', 'volume']
trading_data  = get_price(order_book_ids=order_book_ids,start_date=start_date, end_date=end_date, fields=fields, frequency=frequency)
print(trading_data)


import datetime

from libfinance import get_price_coverage


order_book_ids = ["AAPL.US","NVDA.US"]
frequency = "1d"
fields = None
trading_data  = get_price(order_book_ids=order_book_ids,start_date=start_date, end_date=end_date, fields=fields, frequency=frequency)
print(trading_data)
