"""公司行动：分红、拆股与送转、配股、分拆。"""
import libfinance as lf

# [get_dividends.1] 一只股票的全部分红事件
print(lf.get_dividends("600000.XSHG").head())
# [/get_dividends.1]

# [get_dividends.2] 多只股票、限定日期与字段
print(lf.get_dividends(["600000.XSHG", "000001.XSHE"], "2024-01-01", "2024-06-28",
                       fields=["ex_date", "cash_per_share"]))
# [/get_dividends.2]

# [get_dividends.3] as_of：只看截至那天已知的事件
print(lf.get_dividends("600000.XSHG", "2024-01-01", "2024-06-28", fields=["ex_date", "cash_per_share"],
                       as_of="2024-06-28"))
# [/get_dividends.3]

# [get_dividends.4] A 股与美股混在一批
print(lf.get_dividends(["600000.XSHG", "AAPL.US"], "2024-01-01", "2024-12-31",
                       fields=["ex_date", "cash_per_share"]))
# [/get_dividends.4]

# [get_splits.1] 一只 A 股的全部拆股事件：ratio_from 股变为 ratio_to 股
print(lf.get_splits("600000.XSHG"))
# [/get_splits.1]

# [get_splits.2] 拆股（美股）
print(lf.get_splits("NVDA.US", "2024-01-01", "2024-12-31"))
# [/get_splits.2]

# [get_allotments.1] 一只股票的配股事件
print(lf.get_allotments("600000.XSHG"))
# [/get_allotments.1]

# [get_allotments.2] 窗口内没有配股时返回空表
print(lf.get_allotments("600000.XSHG", "2024-01-01", "2024-12-31"))
# [/get_allotments.2]

# [get_spinoffs.1] 美股分拆及其估值口径
print(lf.get_spinoffs("MMM.US", "2024-01-01", "2024-12-31"))
# [/get_spinoffs.1]
