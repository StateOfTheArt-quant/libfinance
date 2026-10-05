"""日频行情：股票与指数、字段、复权方式与查询窗口。"""
import libfinance as lf

# 单只股票的收盘价与成交量（默认前复权）
print(lf.get_price("000001.XSHE", "2024-03-01", "2024-03-11", fields=["close", "volume"]))

# 股票与指数混在一批
print(lf.get_price(["000001.XSHE", "000300.XSHG"], "2024-03-01", "2024-03-05",
                   fields=["open", "high", "low", "close"]))

# 复权方式：不复权、前复权、后复权
for adjust_type in ("none", "pre", "post"):
    print(adjust_type)
    print(lf.get_price("600519.XSHG", "2024-03-01", "2024-03-05",
                       fields=["close", "volume"], adjust_type=adjust_type))

# 排除停牌日
print(lf.get_price("000001.XSHE", "2024-03-01", "2024-03-11", fields=["close"], skip_suspended=True))

# 美股：代码自带市场
print(lf.get_price(["AAPL.US", "NVDA.US"], "2026-03-02", "2026-03-04", fields=["close", "volume"]))

# 行情覆盖到哪天：按证券类型与交易所给出
print(lf.get_price_coverage(market="cn")["stock"])

# 最近 5 个有行情的交易日：以覆盖上界为终点
end = lf.get_price_coverage(market="cn")["stock"]["XSHE"]["end"]
dates = lf.get_n_trading_dates_until(end, n=5, market="cn")
print(lf.get_price("000001.XSHE", dates[0], dates[-1], fields=["close"]))
