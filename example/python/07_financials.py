#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""基本面：报告季度回答哪一期，as_of 回答当时已经知道哪一版。

字段与因子名依赖服务端目录。以下使用 net_profit 和 net_profit_ttm。
返回 DataFrame；财报中的 info_date/if_adjusted 用于核对披露时间与修订。
"""
from libfinance import get_factor, get_pit_financials_ex

# [get_pit_financials_ex]
# [get_pit_financials_ex.1]
# 1. 最新可见版本：适用于今天研究历史季度，不等同于历史回测可见值。
print(get_pit_financials_ex("600000.XSHG", ["net_profit"], "2024q1", "2024q3"))
# [/get_pit_financials_ex.1]

# [get_pit_financials_ex.2]
# 2. 固定季度，加 as_of：只使用截至 2024-11-01 已披露的信息。
print(get_pit_financials_ex("600000.XSHG", ["net_profit"], "2024q1", "2024q3",
                           as_of="2024-11-01", statements="latest"))
# [/get_pit_financials_ex.2]

# [get_pit_financials_ex.3]
# 3. 同一个截止日，把 latest 改为 all，查看当时可见的全部修订版本。
print(get_pit_financials_ex(["600000.XSHG", "000001.XSHE"], ["net_profit"],
                           "2024q1", "2024q3", as_of="2024-11-01", statements="all"))
# [/get_pit_financials_ex.3]
# [/get_pit_financials_ex]

# [get_factor]
# [get_factor.1]
# 1. TTM 等衍生指标用 get_factor，原始报表项目用 get_pit_financials_ex。
print(get_factor("600000.XSHG", ["net_profit_ttm"], "2024q1", "2024q3"))
# [/get_factor.1]

# [get_factor.2]
# 2. 多只股票、同一知识截止日，供同一回测截面的比较使用。
print(get_factor(["600000.XSHG", "000001.XSHE"], ["net_profit_ttm"],
                 "2024q1", "2024q3", as_of="2024-11-01"))
# [/get_factor.2]
# [/get_factor]
