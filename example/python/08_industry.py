#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""行业：证券属于哪些行业、行业包含哪些证券、成分各占多少。

行业以 order_book_id（``<分类代码>.<分类体系>``，如 801780.SW）命名；source 是分类体系
（SW、GICS），level 是层级；as_of 是那一天的事实。
"""
from libfinance import get_industry_constituents, get_industry_weights, get_instrument_industry

# [get_instrument_industry]
# [get_instrument_industry.1]
# 同一组股票在申万体系里的一级与三级行业；related_order_book_id 就是行业代码。
for level in (1, 3):
    print(get_instrument_industry(["000001.XSHE", "600000.XSHG"],
                                  source="SW", level=level, as_of="2024-06-28"))
# [/get_instrument_industry.1]
# [/get_instrument_industry]

# [get_industry_constituents]
# [get_industry_constituents.1]
# 反向查询：从证券的行业拿到行业代码，再取当日的成分证券。
industries = get_instrument_industry(["600000.XSHG"], source="SW", level=1, as_of="2024-06-28")
if not industries.empty:
    industry = industries.iloc[0]["related_order_book_id"]
    print(get_industry_constituents(industry, as_of="2024-06-28"))
    print(get_industry_constituents(industry))  # 去掉 as_of，取已确认的最新日期
# [/get_industry_constituents.1]
# [/get_industry_constituents]

# [get_industry_weights]
# [get_industry_weights.1]
# 行业成分的权重；每行都带 methodology，说明权重是怎么来的。
print(get_industry_weights("801780.SW", as_of="2024-06-28"))
# [/get_industry_weights.1]
# [/get_industry_weights]
