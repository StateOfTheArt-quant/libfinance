#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from libfinance import instruments, all_instruments


stock_instrument_df = all_instruments(type="CS")
print(len(stock_instrument_df))
print(stock_instrument_df)

instrument_list = instruments(order_book_ids=["000001.XSHE","000300.XSHG"])
print(instrument_list)