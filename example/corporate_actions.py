#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""公司行动：日期窗口筛选事件，as_of 限制已知信息。

四个函数均接受 (order_book_ids, start_date=None, end_date=None,
               fields=None, as_of=None)，返回事件 DataFrame。
市场由代码推断，支持已提供相应能力的混合市场查询。
空表表示没有匹配事件；分拆仅支持美股代码。
"""
from libfinance import get_dividends, get_splits, get_allotments, get_spinoffs

# [get_dividends]
# [get_dividends.1]
# 1. 单只证券全部分红事件。
print(get_dividends("600000.XSHG"))
# [/get_dividends.1]

# [get_dividends.2]
# 2. 多只证券、限定事件日期和返回字段。
print(get_dividends(["600000.XSHG", "000001.XSHE"], "2024-01-01", "2024-06-28",
                    fields=["ex_date", "cash_per_share"]))
# [/get_dividends.2]

# [get_dividends.3]
# 3. 同样的事件窗口，只取截至指定时点已知的信息。
print(get_dividends("600000.XSHG", "2024-01-01", "2024-06-28",
                    as_of="2024-06-28"))
# [/get_dividends.3]
# [get_dividends.4]
# 4. 混合市场批量查询：代码已包含市场信息，不需要 market 参数。
print(get_dividends(["600000.XSHG", "AAPL.US"], "2024-01-01", "2024-12-31",
                    fields=["ex_date", "cash_per_share"]))
# [/get_dividends.4]
# [/get_dividends]

# [get_splits]
# [get_splits.1]
# 拆股/送转事件用于解释股数和价格变化；ratio_from 股变为 ratio_to 股。
print(get_splits("600000.XSHG", "2020-01-01", "2024-12-31"))
# [/get_splits.1]

# [get_splits.2]
print(get_splits("NVDA.US", "2024-01-01", "2024-12-31"))
# [/get_splits.2]
# [/get_splits]

# [get_allotments]
# [get_allotments.1]
# 配股是独立事件，不应与现金分红混为一谈；缩小日期范围可能得到空表。
print(get_allotments("600000.XSHG"))
# [/get_allotments.1]

# [get_allotments.2]
print(get_allotments("600000.XSHG", "2024-01-01", "2024-12-31"))
# [/get_allotments.2]
# [/get_allotments]

# [get_spinoffs]
# [get_spinoffs.1]
# 美股分拆：保留全部字段，同时查看 valuation_price/basis/source 的估值口径。
print(get_spinoffs("MMM.US", "2024-01-01", "2024-12-31"))
# [/get_spinoffs.1]
# [/get_spinoffs]
