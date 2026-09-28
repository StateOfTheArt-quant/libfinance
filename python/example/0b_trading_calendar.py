#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""交易日历：市场、日期区间与交易日偏移。

日期接受日期字符串；market 默认 cn，美股传 us。
区间查询包含两端；前后偏移不包含输入日；截至某日的窗口包含该日（若为交易日）。
"""
from libfinance import (
    get_calendar_coverage, get_all_trading_dates, get_trading_dates,
    is_trading_date, get_previous_trading_date, get_next_trading_date,
    get_n_trading_dates_until, count_trading_dates,
)

# [get_calendar_coverage]
# [get_calendar_coverage.1]
# 日历确认到哪天？这不是行情已更新到哪天。超出范围会抛 CalendarCoverageError。
print(get_calendar_coverage(market="cn"))
# [/get_calendar_coverage.1]

# [get_calendar_coverage.2]
print(get_calendar_coverage(market="us"))
# [/get_calendar_coverage.2]
# [/get_calendar_coverage]

# [get_all_trading_dates]
# [get_all_trading_dates.1]
# 获取当前日历包含的全部交易日，返回 DatetimeIndex。
print(get_all_trading_dates(market="cn"))
# [/get_all_trading_dates.1]
# [/get_all_trading_dates]

# [get_trading_dates]
# [get_trading_dates.1]
# 相同自然日区间，切换市场后交易日可能不同。
print(get_trading_dates("2024-01-01", "2024-01-31", market="cn"))
# [/get_trading_dates.1]

# [get_trading_dates.2]
print(get_trading_dates("2024-01-01", "2024-01-31", market="us"))
# [/get_trading_dates.2]
# [/get_trading_dates]

# [is_trading_date]
# [is_trading_date.1]
# 判断某天是否开市，返回 bool；不要把周末简单等同于所有非交易日。
print(is_trading_date("2024-01-08", market="cn"))
# [/is_trading_date.1]

# [is_trading_date.2]
print(is_trading_date("2024-01-07", market="cn"))
# [/is_trading_date.2]
# [/is_trading_date]

# [get_previous_trading_date]
# [get_previous_trading_date.1]
# 严格早于输入日；n=3 表示第三个交易日，不是减三天。
print(get_previous_trading_date("2024-01-08"))
# [/get_previous_trading_date.1]

# [get_previous_trading_date.2]
print(get_previous_trading_date("2024-01-08", n=3))
# [/get_previous_trading_date.2]
# [/get_previous_trading_date]

# [get_next_trading_date]
# [get_next_trading_date.1]
# 严格晚于输入日；用 n 调整结算或调仓的交易日偏移。
print(get_next_trading_date("2024-01-05"))
# [/get_next_trading_date.1]

# [get_next_trading_date.2]
print(get_next_trading_date("2024-01-05", n=3))
# [/get_next_trading_date.2]
# [/get_next_trading_date]

# [get_n_trading_dates_until]
# [get_n_trading_dates_until.1]
# 截至周一的最近 5 个交易日包含周一；截至周日则从此前最近交易日结束。
print(get_n_trading_dates_until("2024-01-08", n=5))
# [/get_n_trading_dates_until.1]

# [get_n_trading_dates_until.2]
print(get_n_trading_dates_until("2024-01-07", n=5))
# [/get_n_trading_dates_until.2]
# [/get_n_trading_dates_until]

# [count_trading_dates]
# [count_trading_dates.1]
# 只需要样本数时直接计数，不用拿自然日天数代替交易日天数。
print(count_trading_dates("2024-01-01", "2024-01-31", market="cn"))
# [/count_trading_dates.1]
# [/count_trading_dates]
