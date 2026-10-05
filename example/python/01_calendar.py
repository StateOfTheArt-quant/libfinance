"""交易日历：A 股与美股的交易日、日期偏移与日历覆盖范围。"""
import libfinance as lf

# A 股日历确认到哪天（不是行情更新到哪天）
print(lf.get_calendar_coverage(market="cn"))

# 美股日历的覆盖范围
print(lf.get_calendar_coverage(market="us"))

# 当前日历包含的全部交易日
dates = lf.get_all_trading_dates(market="cn")
print(len(dates), dates[0], dates[-1])

# 区间内的 A 股交易日
print(lf.get_trading_dates("2024-01-01", "2024-01-31", market="cn"))

# 同一区间换成美股，交易日不同
print(lf.get_trading_dates("2024-01-01", "2024-01-31", market="us"))

# 周一开市
print(lf.is_trading_date("2024-01-08", market="cn"))

# 周日休市
print(lf.is_trading_date("2024-01-07", market="cn"))

# 严格早于输入日的上一个交易日
print(lf.get_previous_trading_date("2024-01-08"))

# n=3：往前第三个交易日，不是减三天
print(lf.get_previous_trading_date("2024-01-08", n=3))

# 严格晚于输入日的下一个交易日
print(lf.get_next_trading_date("2024-01-05"))

# n=3：往后第三个交易日
print(lf.get_next_trading_date("2024-01-05", n=3))

# 截至周一（含）的最近 5 个交易日
print(lf.get_n_trading_dates_until("2024-01-08", n=5))

# 截至周日：从此前最近的交易日往回数
print(lf.get_n_trading_dates_until("2024-01-07", n=5))

# 只要样本数时直接计数
print(lf.count_trading_dates("2024-01-01", "2024-01-31", market="cn"))
