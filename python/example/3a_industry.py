#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""行业分类：先查分类表，再做证券到行业、行业到证券的双向查询。

source='sw' 表示申万；date 决定历史分类，level=1/2/3 决定层级。
"""
from libfinance import get_industry_mapping, get_instrument_industry, get_industry

# [get_industry_mapping]
# [get_industry_mapping.1]
# 1. 有哪些行业代码和名称？返回分类表，不需要手写行业代码。
print(get_industry_mapping(source="sw").head())
# [/get_industry_mapping.1]

# [get_industry_mapping.2]
# 2. 做历史分类时，分类表和后面的成分查询使用同一天。
mapping = get_industry_mapping(source="sw", date="2024-06-28")
print(mapping.head())
# [/get_industry_mapping.2]
# [/get_industry_mapping]

# [get_instrument_industry]
# [get_instrument_industry.1]
# 同一组股票，一级行业用于大类分组，三级行业用于更细比较。
for level in (1, 3):
    print(get_instrument_industry(["000001.XSHE", "600000.XSHG"],
                                  date="2024-06-28", source="sw", level=level))
# [/get_instrument_industry.1]
# [/get_instrument_industry]

# [get_industry]
# [get_industry.1]
# 反向查询：从历史分类表选一个一级行业，取得当日成分证券列表。
mapping = get_industry_mapping(source="sw", date="2024-06-28")
if not mapping.empty:
    industry_code = str(mapping.iloc[0]["first_industry_code"])
    print(get_industry(industry_code, source="sw", date="2024-06-28"))
    print(get_industry(industry_code, source="sw"))  # 去掉 date，改查最新分类
# [/get_industry.1]
# [/get_industry]
