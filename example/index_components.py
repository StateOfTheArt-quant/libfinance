#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import pandas as pd
from libfinance import get_instrument_industry, get_index_weights


order_book_ids = ["000001.XSHE","600000.XSHG"]
instrument_industry = get_instrument_industry(order_book_ids=order_book_ids, date="2022-09-20")
print(instrument_industry)

    
index_weight = get_index_weights(index_id="000300.XSHG", date="2022-09-20")
print(index_weight)

    
index_weight = get_index_weights(index_id="000300.XSHG", date="2022-07-20")
print(index_weight)


