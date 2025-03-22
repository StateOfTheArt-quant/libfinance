#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import pandas as pd
from libfinance.api.get_price import get_price


instrument_ids = ["000001.XSHE"]
start_date = "2024-01-01"
end_date = "2024-03-11"
frequency = "1d"

fields = ["close","volume"]

trading_data  = get_price(order_book_ids=instrument_ids,start_date=start_date, end_date=end_date, fields=fields, frequency=frequency)
print(trading_data)
print("------------------------------")


instrument_ids = ["000001.XSHE","600000.XSHG"]
start_date = "2024-03-01"
end_date = "2024-03-11"
frequency = "1d"
fields = ['open', 'high', 'low', 'close', 'volume']
trading_data  = get_price(order_book_ids=instrument_ids,start_date=start_date, end_date=end_date, fields=fields, frequency=frequency)
print(trading_data)
