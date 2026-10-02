#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""证券目录：股票、指数、行业、主题在同一个目录里，先确定范围，再按代码查询。

all_instruments(type=None, market=None, source=None, as_of=None, cached=True) -> DataFrame
  type：stock / index / industry / theme，或它们的列表；省略为全部类型。
  market：cn / us；省略为全部市场。source：编号机构——股票是交易所，指数是发布机构，
  行业是分类体系，主题是主题目录。
  as_of：该日的历史视图；省略取各类型、各来源的当前状态。
instruments(order_book_ids, as_of=None, last_known=False) -> Instrument / list[Instrument]
  类型由代码本身决定；字符串返回单个对象，列表返回对象列表，代码可混合市场与类型。

四种类型的代码与编号机构：

  类型      代码示例                     source
  stock     000001.XSHE  AAPL.US         XSHG / XSHE / XBSE、XNAS / XNYS（交易所）
  index     000300.XSHG  SPX.US          CSI / CNI、SPDJI / NASDAQ / FTSE_RUSSELL（发布机构）
  industry  480000.SW    45.GICS         SW、GICS / ICB / NAICS / SIC（分类体系）
  theme     300008.THS                   THS（主题目录，仅 A 股）

股票、指数与申万行业有历史；美国行业分类与主题目前只有当前快照，给它们早于发布的 as_of 会报 CoverageError。
"""
from libfinance import all_instruments, instruments

# [all_instruments]
# [all_instruments.1]
# 1. 目录里有什么？每行一只证券：order_book_id、permanent_id、type、market、name、exchange、source。
#    四种类型在同一张表里，按 type 与 market 计数看全貌。
catalog = all_instruments()
print(catalog.groupby(["type", "market"]).size())
# [/all_instruments.1]

# [all_instruments.2]
# 2. 股票：source 与 exchange 是上市的交易所。
print(all_instruments(type="stock", market="cn").head())
# [/all_instruments.2]

# [all_instruments.3]
# 3. 指数：source 是指数发布机构，如中证指数公司（CSI）、标普道琼斯（SPDJI）。
print(all_instruments(type="index", source="CSI").head())
print(all_instruments(type="index", market="us"))
# [/all_instruments.3]

# [all_instruments.4]
# 4. 行业：source 是分类体系。A 股用申万（SW），美股有 GICS、ICB、NAICS、SIC 四套。
print(all_instruments(type="industry", source="SW").head())
print(all_instruments(type="industry", source="GICS").head())
# [/all_instruments.4]

# [all_instruments.5]
# 5. 主题：同花顺概念（THS），仅 A 股。
print(all_instruments(type="theme").head())
# [/all_instruments.5]

# [all_instruments.6]
# 6. 几种类型一起：type 给列表。
print(all_instruments(type=["index", "industry"], market="cn").groupby(["type", "source"]).size())
# [/all_instruments.6]

# [all_instruments.7]
# 7. 历史时点：as_of 决定身份快照，不表示当日一定有成交。
#    申万 2021 年改版前后行业数不同；股票的 source 就是交易所，可以只看纳斯达克。
print(len(all_instruments(type="industry", source="SW", as_of="2020-01-02")),
      len(all_instruments(type="industry", source="SW", as_of="2022-04-15")))
print(all_instruments(type="stock", market="us", source="XNAS", as_of="2025-06-16").head())
# [/all_instruments.7]
# [/all_instruments]

# [instruments]
# [instruments.1]
# 1. 单个代码 -> Instrument；查询不到 -> None。
stock = instruments("000001.XSHE")
if stock is not None:
    print(stock.order_book_id, stock.name, stock.type, stock.permanent_id)
# [/instruments.1]

# [instruments.2]
# 2. 一个列表里四种类型、两个市场都可以：类型由代码决定，按输入顺序返回，跳过查不到的代码。
for item in instruments(["000001.XSHE", "000300.XSHG", "480000.SW", "300008.THS",
                         "AAPL.US", "SPX.US", "45.GICS"]):
    print(item.order_book_id, item.type, item.market, item.source, item.name)
# [/instruments.2]

# [instruments.3]
# 3. 增加 as_of，按当日有效的代码解析；股票、指数与申万行业都有历史。
for item in instruments(["000001.XSHE", "000300.XSHG", "480000.SW", "SPX.US"], as_of="2022-04-15"):
    print(item.order_book_id, item.type, item.name)
# [/instruments.3]

# [instruments.4]
# 4. 代码随时间变化：Meta 在 2022-04-15 使用 FB.US。已退市的代码当前查不到，last_known=True 按它
#    最后一次的证券解析：ATVI.US 在 2023-10 被微软收购后退市。
print([item.name for item in instruments(["FB.US", "NVDA.US"], as_of="2022-04-15")])
print(instruments("ATVI.US"), instruments("ATVI.US", last_known=True).name)
# [/instruments.4]
# [/instruments]
