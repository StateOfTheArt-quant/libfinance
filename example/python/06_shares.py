#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""股本结构：全历史、日期截面与字段子集；所有股本字段的单位均为股。

get_shares(order_book_ids, start_date=None, end_date=None, fields=None)
返回以 (order_book_id, date) 为索引的 DataFrame。
"""
from libfinance import get_shares

# [get_shares]
# [get_shares.1]
# 1. 不传日期，从首个股本事件到最后一个股本事件，返回全部字段。
print(get_shares("600000.XSHG"))
# [/get_shares.1]

# [get_shares.2]
# 2. 多只股票、指定窗口，只取总股本与流通 A 股股本。
print(get_shares(["000001.XSHE", "600000.XSHG"], "2024-01-01", "2024-06-28",
                 fields=["total", "circulation_a"]))
# [/get_shares.2]

# [get_shares.3]
# 3. 开始日等于结束日，查询单日截面；自由流通股本与流通 A 股不是同一个字段。
print(get_shares(["000001.XSHE", "600000.XSHG"], "2024-06-28", "2024-06-28",
                 fields=["circulation_a", "free_circulation"]))
# [/get_shares.3]
# [/get_shares]
