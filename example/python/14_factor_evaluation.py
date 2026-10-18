"""Turn20：批量取数，逐日评价 1、3、5、10、20 日未来收益。"""
import pandas as pd
import libfinance as lf


# 1. 研究日期与每日股票池
horizons = [1, 3, 5, 10, 20]
dates = lf.get_trading_dates("2024-01-01", "2024-12-31")
members = {
    day: lf.get_index_constituents("000300.XSHG", as_of=day)
    for day in dates
}
stocks = sorted({stock for ids in members.values() for stock in ids})
start = lf.get_n_trading_dates_until(dates[0], n=20)[0]
end = lf.get_next_trading_date(dates[-1], n=max(horizons))
calendar = lf.get_trading_dates(start, end)

in_pool = pd.DataFrame(False, index=dates, columns=stocks)
for day, ids in members.items():
    in_pool.loc[day, ids] = True

# 2. 换手率与行情分别只查询一次
rates = lf.get_turnover_rate(stocks, start, dates[-1])
rates = rates["turnover_rate"].unstack("order_book_id")
rates = rates.reindex(index=calendar, columns=stocks)

bars = lf.get_price(
    stocks, start, end, fields=["close", "volume"], adjust_type="pre",
)
close = bars["close"].unstack("order_book_id").reindex(index=calendar, columns=stocks)
volume = bars["volume"].unstack("order_book_id").reindex(index=calendar, columns=stocks)

# 3. 每列是一只股票，沿交易日计算 rolling 和 shift
factor = rates.rolling(20, min_periods=20).mean().loc[dates].where(in_pool)
future_returns = {}
for n in horizons:
    returns = close.shift(-n) / close - 1
    active = (volume > 0) & (volume.shift(-n) > 0)
    future_returns[n] = returns.where(active).loc[dates].where(in_pool)

coverage = pd.DataFrame({"pool": in_pool.sum(axis=1), "factor": factor.count(axis=1)})
for n in horizons:
    coverage[f"valid_{n}d"] = (factor.notna() & future_returns[n].notna()).sum(axis=1)
print(coverage.agg(["min", "max"]))

# 4. 每日截面 IC 与 Rank IC，再沿时间汇总
ic = pd.DataFrame({
    n: factor.corrwith(future_returns[n], axis=1) for n in horizons
})
rank_ic = pd.DataFrame({
    n: factor.corrwith(future_returns[n], axis=1, method="spearman") for n in horizons
})
summary = pd.DataFrame({
    "days": ic.count(),
    "IC_mean": ic.mean(),
    "IC_std": ic.std(),
    "ICIR": ic.mean() / ic.std().replace(0, float("nan")),
    "RankIC_mean": rank_ic.mean(),
    "RankIC_std": rank_ic.std(),
    "RankICIR": rank_ic.mean() / rank_ic.std().replace(0, float("nan")),
})
summary.index.name = "horizon"
print(summary.round(4).to_string())

# 5. 以 20 日收益检查分组关系

groups = factor.apply(
    lambda row: pd.qcut(row, q=5, labels=False, duplicates="drop") + 1, axis=1,
)
if not groups.nunique(axis=1).eq(5).all():
    raise ValueError("部分日期无法形成五组，请检查样本量和因子取值")
group_returns = pd.DataFrame({
    g: future_returns[20].where(groups == g).mean(axis=1) for g in range(1, 6)
})
print(group_returns.mean().rename("各组平均20日收益").round(4))
print("低组减高组：", round((group_returns[1] - group_returns[5]).mean(), 4))
