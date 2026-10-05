"""指数：证券所属指数、指数成分与指数权重。"""
import libfinance as lf

# 一只 A 股、一只美股所属的指数
print(lf.get_instrument_indices(["600000.XSHG", "AAPL.US"], as_of="2024-06-28").head(10))

# 只看中证指数公司（CSI）发布的指数
print(lf.get_instrument_indices("600000.XSHG", source="CSI", as_of="2024-06-28"))

# 沪深 300 在 2024-06-28 的成分
members = lf.get_index_constituents("000300.XSHG", as_of="2024-06-28")
print(len(members), members[:5])

# 省略 as_of：已确认的最新成分
members = lf.get_index_constituents("SPX.US")
print(len(members), members[:5])

# 成分权重与 methodology；非月末日按复权收益率漂移
weights = lf.get_index_weights("000300.XSHG", as_of="2024-06-28")
print(weights.head())
print(weights["weight"].sum())
