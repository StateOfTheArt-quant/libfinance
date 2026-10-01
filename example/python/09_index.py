#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""指数：证券属于哪些指数、指数包含哪些证券、成分各占多少。

指数以 order_book_id（000300.XSHG、SPX.US）命名，目录是 all_instruments(type="index")；
source 是指数发布机构（CSI、SPDJI）；as_of 是那一天的事实。权重是比例，不是百分数。
"""
from libfinance import get_index_constituents, get_index_weights, get_instrument_indices

# [get_instrument_indices]
# [get_instrument_indices.1]
# 一只 A 股、一只美股在当日所属的指数；related_order_book_id 就是指数代码。
print(get_instrument_indices(["600000.XSHG", "AAPL.US"], as_of="2024-06-28"))
# 只看中证指数公司发布的指数。
print(get_instrument_indices("600000.XSHG", source="CSI", as_of="2024-06-28"))
# [/get_instrument_indices.1]
# [/get_instrument_indices]

# [get_index_constituents]
# [get_index_constituents.1]
# 沪深300 在 2024-06-28 的成分；去掉 as_of 取已确认的最新日期。
members = get_index_constituents("000300.XSHG", as_of="2024-06-28")
print(len(members), members[:5])
print(get_index_constituents("SPX.US")[:5])
# [/get_index_constituents.1]
# [/get_index_constituents]

# [get_index_weights]
# [get_index_weights.1]
# 同一指数、同一天的权重；每行都带 methodology，说明权重是怎么来的。
weights = get_index_weights("000300.XSHG", as_of="2024-06-28")
print(weights.head())
print(weights["weight"].sum())  # 检查权重和
# [/get_index_weights.1]
# [/get_index_weights]
