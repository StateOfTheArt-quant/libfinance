"""公司行动：分红、拆股与送转、配股、分拆。"""
import libfinance as lf

# 一只股票的全部分红事件
print(lf.get_dividends("600000.XSHG").head())

# 多只股票、限定日期与字段
print(lf.get_dividends(["600000.XSHG", "000001.XSHE"], "2024-01-01", "2024-06-28",
                       fields=["ex_date", "cash_per_share"]))

# as_of：只看截至那天已知的事件
print(lf.get_dividends("600000.XSHG", "2024-01-01", "2024-06-28", fields=["ex_date", "cash_per_share"],
                       as_of="2024-06-28"))

# A 股与美股混在一批
print(lf.get_dividends(["600000.XSHG", "AAPL.US"], "2024-01-01", "2024-12-31",
                       fields=["ex_date", "cash_per_share"]))

# 一只 A 股的全部拆股事件：ratio_from 股变为 ratio_to 股
print(lf.get_splits("600000.XSHG"))

# 拆股（美股）
print(lf.get_splits("NVDA.US", "2024-01-01", "2024-12-31"))

# 一只股票的配股事件
print(lf.get_allotments("600000.XSHG"))

# 窗口内没有配股时返回空表
print(lf.get_allotments("600000.XSHG", "2024-01-01", "2024-12-31"))

# 美股分拆及其估值口径
print(lf.get_spinoffs("MMM.US", "2024-01-01", "2024-12-31"))
