#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""合约信息：先确定证券范围，再按代码查询详细信息。

all_instruments(type=None, date=None, market=None, cached=True) -> DataFrame
  type：CS 股票、INDX 指数；省略则保留全部类型。
  date：身份快照日期；省略取最新。market：省略合并已绑定市场。
instruments(order_book_ids, date=None) -> Instrument / list[Instrument]
  字符串返回单个对象，列表返回对象列表；代码可混合市场。
"""
from libfinance import all_instruments, instruments

# [all_instruments]
# [all_instruments.1]
# 1. 有哪些合约？省略 market 合并服务端已绑定市场，结果中的 market 标明所属市场。
all_contracts = all_instruments()
print(all_contracts.head())
# [/all_instruments.1]

# [all_instruments.2]
# 2. 只看 A 股股票，或只看指数：改变 type，返回形状仍是 DataFrame。
print(all_instruments(type="CS", market="cn").head())
# [/all_instruments.2]

# [all_instruments.3]
print(all_instruments(type="INDX", market="cn").head())
# [/all_instruments.3]

# [all_instruments.4]
# 3. 历史时点有哪些合约？date 决定身份快照，不表示当日一定有成交。
print(all_instruments(type="CS", date="2025-09-18", market="cn").head())
# [/all_instruments.4]

# [all_instruments.5]
# 4. 查询美股历史身份。美股类型使用 EQTY/FUND/DERV，不能用 CS 筛选。
# 当前客户端 type 参数只接受 CS/INDX，故先省略 type，再筛选返回表。
us_contracts = all_instruments(date="2025-06-16", market="us")
print(us_contracts[us_contracts["type"] == "EQTY"].head())
# [/all_instruments.5]
# [/all_instruments]

# [instruments]
# [instruments.1]
# 1. 单个代码 -> Instrument；查询不到 -> None。
stock = instruments("000001.XSHE")
if stock is not None:
    print(stock.order_book_id, stock.symbol, stock.type)
# [/instruments.1]

# [instruments.2]
# 2. 列表 -> Instrument 列表，可混合中美市场；按输入顺序返回，跳过查不到的代码。
print(instruments(["AAPL.US", "000001.XSHE", "000300.XSHG"]))
# [/instruments.2]

# [instruments.3]
# 3. 同样的列表，增加 date，查询历史身份。
print(instruments(["000001.XSHE", "000300.XSHG"], date="2022-04-15"))
# [/instruments.3]

# [instruments.4]
# 4. 历史代码按当时名称查询；Meta 在 2022-04-15 使用 FB.US。
print(instruments(["FB.US", "NVDA.US"], date="2022-04-15"))
# [/instruments.4]
# [/instruments]
