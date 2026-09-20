#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""财务数据：PIT 财报与衍生因子。

两个接口都带 ``as_of`` —— 财报会被追溯修订，回测里不传它就会用到当时还没披露的
修订值。``statements="all"`` 能看到同一季度的全部版本，``if_adjusted`` 标出哪些是修订。
"""
import os

import libfinance

# 默认连公网服务；本地自建时用环境变量覆盖：
#   LIBFINANCE_HOST=127.0.0.1 python example/financials.py
libfinance.init_client(host=os.environ.get("LIBFINANCE_HOST", "libfinance.tech"),
                       port=int(os.environ.get("LIBFINANCE_PORT", "8080")))

from libfinance import get_factor, get_pit_financials_ex

code = "600000.XSHG"

print("净利润 TTM：")
print(get_factor(code, ["net_profit_ttm"], "2024q1", "2025q4"))

print("\nPIT 财报（全部修订版本）：")
print(get_pit_financials_ex(code, ["net_profit"], "2024q1", "2025q4", statements="all"))
