"""财务：季度报表的 point-in-time 视图与逐交易日的财务衍生指标。"""
import libfinance as lf

# 最新可见版本
print(lf.get_pit_financials_ex("600000.XSHG", ["total_operating_revenue", "net_income_parent"], "2024q1", "2024q3"))

# as_of：只用截至那天已披露的信息
print(lf.get_pit_financials_ex("600000.XSHG", ["net_income_parent"], "2024q1", "2024q3",
                               as_of="2024-11-01", statements="latest"))

# statements="all"：当时可见的全部修订版本
print(lf.get_pit_financials_ex(["600000.XSHG", "AAPL.US"], ["net_income_parent"], "2024q1", "2024q3",
                               as_of="2024-11-01", statements="all"))

# 逐交易日的指标：在公告日跳变，其间持平
print(lf.get_financial_metrics("600519.XSHG", ["roe_lf", "revenue_ttm"], "2024-10-28", "2024-11-01"))

# A 股与美股同一套公式；省略日期取最近一个交易日
print(lf.get_financial_metrics(["600519.XSHG", "AAPL.US"], ["net_profit_growth_lyr", "debt_to_assets_lf"]))
