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
concept_instrument_returns = concept_instrument_returns.to_frame("returns")

# top5龙头股涨幅
concept_instrument_net_value = concept_instrument_returns.groupby("order_book_id", group_keys=False)["returns"].apply(lambda x: (x+1).cumprod())
concept_instrument_cumulative_returns = concept_instrument_net_value.groupby("order_book_id").last() - 1
top5_instrument_cumulative_returns = concept_instrument_cumulative_returns.sort_values(ascending=False).head(5)

# top5龙头股名称
top_instrument_name = concept_weight.set_index('order_book_id').loc[top5_instrument_cumulative_returns.index]['symbol']

# top5龙头股净值走势
top_instrument_net_value = concept_instrument_net_value.loc[top5_instrument_cumulative_returns.index]
top_instrument_net_value = top_instrument_net_value.unstack().T

# 打印龙头股信息
print(f"概念名：{concept_weight.index_name.iloc[0]}")
print(f"概念成分股数量：{len(concept_weight)}")
print(f"涨幅Top5的个股：\n{top5_instrument_cumulative_returns}\n")
print(f"涨幅Top5的个股名称：\n{top_instrument_name}\n")

# Top5龙头股净值走势
top_instrument_net_value.plot(title="Top5_leading_stock_net_value")
plt.savefig("Top5_leading_stock_net_value.jpg")