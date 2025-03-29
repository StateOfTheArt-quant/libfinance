# 数据接口：获取概念成分股、行情数据
from libfinance import get_concept_weights, get_price
import matplotlib.pyplot as plt

# 概念成分股
concept_weight = get_concept_weights(concept_ids=["886069"], source="THS") # 人形机器人
concept_instrument_ids = concept_weight.order_book_id.unique()

# 概念成分股日行情
concept_instrument_price = get_price(
    order_book_ids=concept_instrument_ids, start_date="2024-12-31", end_date="2025-03-21", frequency="1d", 
    fields=None, skip_suspended=True, include_now=True, adjust_type="none", adjust_orig=None)

# 计算个股收益率
concept_instrument_returns = concept_instrument_price.groupby("order_book_id")["close"].pct_change()
concept_instrument_returns.name = "returns"
concept_instrument_returns = concept_instrument_returns.reset_index()

# 整合个股权重
concept_instrument_returns = concept_instrument_returns.merge(concept_weight[["order_book_id", "weight"]], how="left", on="order_book_id")
concept_instrument_returns = concept_instrument_returns.set_index(["order_book_id", "datetime"]).dropna()

# 计算概念收益率
concept_returns = concept_instrument_returns["returns"] * concept_instrument_returns["weight"]
concept_returns = concept_returns.groupby("datetime").sum()

# 计算概念累计收益率
concept_net_value = (concept_returns + 1).cumprod()
concept_cumulative_returns = concept_net_value.iloc[-1] - 1

# 计算概念收益率的夏普比率
concept_returns_sharpe = concept_returns.mean() / concept_returns.std()

# 打印概念信息
print(f"概念名：{concept_weight.index_name.iloc[0]}")
print(f"概念成分股数量：{len(concept_weight)}")
print(f"概念成分股预览：\n{concept_weight.head(3)}\n")
print(f"概念累计收益率：{concept_cumulative_returns.round(2)}")
print(f"概念夏普比率：{concept_returns_sharpe.round(2)}")

# 概念净值走势
concept_net_value.plot(title="concept_net_value")
plt.savefig("concept_net_value.jpg")
