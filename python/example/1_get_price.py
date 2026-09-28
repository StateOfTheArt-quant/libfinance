#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""日频行情：标的数量、字段、复权方式与查询窗口。

get_price(order_book_ids, start_date, end_date, frequency='1d', fields=None,
          skip_suspended=False, include_now=True, adjust_type='pre', adjust_orig=None)
返回以 (order_book_id, datetime) 为索引的 DataFrame。
"""
from libfinance import get_price, get_price_coverage, get_n_trading_dates_until

# [get_price]
# [get_price.1]
# 1. 单只股票只取收盘价与成交量，缩小返回列数。默认前复权。
one = get_price("000001.XSHE", "2024-03-01", "2024-03-11",
                fields=["close", "volume"])
print(one)
# [/get_price.1]

# [get_price.2]
# 2. 改为多只股票和 OHLC 字段，结果仍是同样的双层索引。
many = get_price(["000001.XSHE", "600000.XSHG"], "2024-03-01", "2024-03-11",
                 fields=["open", "high", "low", "close"])
print(many)
# [/get_price.2]

# [get_price.3]
print(many["close"].unstack("order_book_id"))  # 转为日期 × 证券的收盘价矩阵
# [/get_price.3]

# [get_price.4]
# 3. 固定标的与日期，只改变 adjust_type，比较原始价、前复权与后复权。
# fields 中成交额叫 turnover；volume 随复权缩放，turnover 不随复权缩放。
for adjustment in ("none", "pre", "post"):
    print(adjustment)
    print(get_price("000001.XSHE", "2024-03-01", "2024-03-11",
                    fields=["close", "volume", "turnover"], adjust_type=adjustment))
# [/get_price.4]

# [get_price.5]
# 4. 排除停牌行，用于只统计有交易的观测；没有停牌时两种设置结果相同。
print(get_price("000001.XSHE", "2024-03-01", "2024-03-11",
                fields=["close"], skip_suspended=True))
# [/get_price.5]
# [/get_price]

# [get_price_coverage]
# [get_price_coverage.1]
# 最近 5 个已覆盖的交易日：先问行情上界，再从日历回溯，不能直接把今天当上界。
coverage = get_price_coverage(market="cn")
print(coverage)
# [/get_price_coverage.1]

# [get_price_coverage.2]
end = coverage["XSHE"]["end"]
dates = get_n_trading_dates_until(end, n=5, market="cn")
print(get_price("000001.XSHE", dates[0], dates[-1], fields=["close"]))
# [/get_price_coverage.2]
# [/get_price_coverage]
