#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""指数成分：最新锚点与指定交易日的权重。

get_index_weights(index_code, date=None, market=None) -> DataFrame
返回 index_code/date/order_book_id/weight；权重是比例，不是百分数。
"""
from libfinance import get_index_weights

# [get_index_weights]
# [get_index_weights.1]
# 1. 省略 date，查询最新一期锚点。
print(get_index_weights("000300.XSHG"))
# [/get_index_weights.1]

# [get_index_weights.2]
# 2. 指定交易日：非锚点日由最近的历史锚点按复权收益率推算。
weights = get_index_weights("000300.XSHG", date="2024-06-28")
print(weights.head())
# [/get_index_weights.2]

# [get_index_weights.3]
print(weights["weight"].sum())  # 检查同一指数、同一天的权重和
# [/get_index_weights.3]

# [get_index_weights.4]
# 3. 保持日期不变，改变指数，构造另一组研究样本。
print(get_index_weights("000905.XSHG", date="2024-06-28"))
# [/get_index_weights.4]
# [/get_index_weights]
