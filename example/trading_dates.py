#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#from libfinance.api.calendar import _get_all_trading_dates
import libfinance
from libfinance import get_trading_dates, get_previous_trading_date

start_date = "2023-12-25"
end_date = "2024-01-11"


#all_trading_dates = _get_all_trading_dates()
#print(all_trading_dates)


trading_dates = get_trading_dates(start_date, end_date)
print(trading_dates)

prev_date = get_previous_trading_date(date="2024-02-19",n=1)
print(prev_date)