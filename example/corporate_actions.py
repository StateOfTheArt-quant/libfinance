#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""公司行动：分红、拆股、配股 —— 除权因子的成因。"""
from libfinance import get_dividends, get_splits, get_allotments

code = "600000.XSHG"

print("分红：")
print(get_dividends(code, start_date="2024-01-01", end_date="2026-09-01"))

print("\n拆股（送转）：")
print(get_splits(code, start_date="2000-01-01", end_date="2026-09-01"))

print("\n配股：")
print(get_allotments(code, start_date="2000-01-01", end_date="2026-09-01"))
