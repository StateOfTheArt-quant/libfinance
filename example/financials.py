#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""财务数据：PIT 财报与衍生因子。

两个接口都带 ``as_of`` —— 财报会被追溯修订，回测里不传它就会用到当时还没披露的
修订值。``statements="all"`` 能看到同一季度的全部版本，``if_adjusted`` 标出哪些是修订。
"""
from libfinance import get_factor, get_pit_financials_ex

code = "600000.XSHG"

print("净利润 TTM：")
print(get_factor(code, ["net_profit_ttm"], "2024q1", "2025q4"))

print("\nPIT 财报（全部修订版本）：")
print(get_pit_financials_ex(code, ["net_profit"], "2024q1", "2025q4", statements="all"))
