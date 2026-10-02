#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""基本面：报告季度回答哪一期，as_of 回答当时已经知道哪一版；衍生指标按交易日给出。

财报字段是统一概念 id（total_operating_revenue、net_income_parent、assets……），CN 与 US 同一套；
指标名来自 financialmetrics 的目录（roe_lf、revenue_ttm、net_profit_growth_lyr、debt_to_assets_lf……）。
"""
from libfinance import get_financial_metrics, get_pit_financials_ex

# [get_pit_financials_ex]
# [get_pit_financials_ex.1]
# 1. 最新可见版本：适用于今天研究历史季度，不等同于历史回测可见值。
print(get_pit_financials_ex("600000.XSHG", ["total_operating_revenue", "net_income_parent"], "2024q1", "2024q3"))
# [/get_pit_financials_ex.1]

# [get_pit_financials_ex.2]
# 2. 固定季度，加 as_of：只使用截至 2024-11-01 已披露的信息。
print(get_pit_financials_ex("600000.XSHG", ["net_income_parent"], "2024q1", "2024q3",
                            as_of="2024-11-01", statements="latest"))
# [/get_pit_financials_ex.2]

# [get_pit_financials_ex.3]
# 3. 同一个截止日，把 latest 改为 all，查看当时可见的全部修订版本；CN 与 US 同一套字段。
print(get_pit_financials_ex(["600000.XSHG", "AAPL.US"], ["net_income_parent", "assets"],
                            "2024q1", "2024q3", as_of="2024-11-01", statements="all"))
# [/get_pit_financials_ex.3]
# [/get_pit_financials_ex]

# [get_financial_metrics]
# [get_financial_metrics.1]
# 1. 每个交易日的值来自那天收盘后可见的最新报告：在公告日跳变，其间持平。
print(get_financial_metrics("600519.XSHG", ["roe_lf", "revenue_ttm"], "2024-10-28", "2024-11-01"))
# [/get_financial_metrics.1]

# [get_financial_metrics.2]
# 2. 多只股票、CN 与 US 同一套公式；省略日期取最近一个交易日。
print(get_financial_metrics(["600519.XSHG", "AAPL.US"], ["net_profit_growth_lyr", "debt_to_assets_lf"]))
# [/get_financial_metrics.2]
# [/get_financial_metrics]
