#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from libfinance import instruments, all_instruments


stock_instrument_df = all_instruments(market="us")
stock_instrument_df = stock_instrument_df[stock_instrument_df["type"] == "EQTY"]
print(len(stock_instrument_df))
print(stock_instrument_df)

instrument_list = instruments(order_book_ids=["AAPL.US","NVDA.US"])
print(instrument_list)
print(instrument_list[1].__dict__)
