#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""证券目录：股票、指数、行业、主题在同一个目录里，先确定范围，再按代码查询。

all_instruments(type=None, market=None, source=None, as_of=None, cached=True) -> DataFrame
  type：stock / index / industry / theme，或它们的列表；省略为全部类型。
  market：cn / us；省略为全部市场。source：编号机构（交易所、指数发布机构、分类体系）。
  as_of：该日的历史视图；省略取各类型的当前状态。
instruments(order_book_ids, as_of=None, last_known=False) -> Instrument / list[Instrument]
  类型由代码本身决定；字符串返回单个对象，列表返回对象列表，代码可混合市场与类型。
"""
from libfinance import all_instruments, instruments

# [all_instruments]
# [all_instruments.1]
# 1. 目录里有什么？每行一只证券：order_book_id、permanent_id、type、market、name、exchange、source。
catalog = all_instruments()
print(catalog.head())
# [/all_instruments.1]

# [all_instruments.2]
# 2. 只看 A 股股票：改变 type 与 market，返回形状不变。
print(all_instruments(type="stock", market="cn").head())
# [/all_instruments.2]

# [all_instruments.3]
# 3. 中证指数公司发布的指数：source 是编号机构。
print(all_instruments(type="index", source="CSI").head())
# [/all_instruments.3]

# [all_instruments.4]
# 4. 历史时点的股票：as_of 决定身份快照，不表示当日一定有成交。
print(all_instruments(type="stock", market="cn", as_of="2025-09-18").head())
# [/all_instruments.4]

# [all_instruments.5]
# 5. 美股：exchange 是上市的交易所。
us_stocks = all_instruments(type="stock", market="us", as_of="2025-06-16")
print(us_stocks[us_stocks["exchange"] == "XNAS"].head())
# [/all_instruments.5]
# [/all_instruments]

# [instruments]
# [instruments.1]
# 1. 单个代码 -> Instrument；查询不到 -> None。
stock = instruments("000001.XSHE")
if stock is not None:
    print(stock.order_book_id, stock.name, stock.type, stock.permanent_id)
# [/instruments.1]

# [instruments.2]
# 2. 列表 -> Instrument 列表，股票与指数、中美市场可以混在一起；按输入顺序返回，跳过查不到的代码。
print(instruments(["AAPL.US", "000001.XSHE", "000300.XSHG"]))
# [/instruments.2]

# [instruments.3]
# 3. 同样的列表，增加 as_of，按当日有效的代码解析。
print(instruments(["000001.XSHE", "000300.XSHG"], as_of="2022-04-15"))
# [/instruments.3]

# [instruments.4]
# 4. 已退市的代码：last_known=True 按它最后一次的证券解析；Meta 在 2022-04-15 使用 FB.US。
print(instruments(["FB.US", "NVDA.US"], as_of="2022-04-15"))
print(instruments("FB.US", last_known=True))
# [/instruments.4]
# [/instruments]
