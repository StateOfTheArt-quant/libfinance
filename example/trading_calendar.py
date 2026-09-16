#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from libfinance import (
    get_all_trading_dates,
    get_calendar_coverage,
    get_trading_dates,
)

# release 确认到哪一天。超出这个区间的查询会抛 CalendarCoverageError，
# 而不是悄悄返回一个变短的结果。
print(get_calendar_coverage())

all_trading_dates = get_all_trading_dates()
print(all_trading_dates)

start_date = "2024-01-01"
end_date = "2024-02-27"

trading_dates = get_trading_dates(start_date, end_date)
print(trading_dates)

# 美股：同一套函数，换个 market
print(get_trading_dates("2024-01-01", "2024-02-27", market="us"))
