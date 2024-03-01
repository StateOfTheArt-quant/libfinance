#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import pandas as pd
from libfinance.api.get_price import history_bars

dt = "2023-12-23"

instrument_ids = ["000001.XSHE"]

bar_count = 10

frequency = "1d"

fields = ["close","volume"]



trading_data  = history_bars(order_book_ids=instrument_ids, bar_count=bar_count, frequency=frequency, fields=fields, datetime=dt)
print(trading_data)
print("------------------------------")


instrument_ids = ["000001.XSHE","600000.XSHG"]

trading_data  = history_bars(order_book_ids=instrument_ids, bar_count=bar_count, frequency=frequency, fields=fields, datetime=dt)
print(trading_data)
