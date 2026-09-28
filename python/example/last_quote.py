#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""实时快照：一次调用取当前最新报价；持续推送见 subscription/python/。

get_last_quotes(order_book_ids)：代码列表，可传一只或多只。
返回 dict[代码, Quote 或 None]，快照不是历史分钟线。
"""
from libfinance import get_last_quotes

# [get_last_quotes]
# [get_last_quotes.1]
# 1. 单只证券也使用列表。
print(get_last_quotes(["600000.XSHG"]))
# [/get_last_quotes.1]

# [get_last_quotes.2]
# 2. 一次查询多只证券，减少逐只请求。
quotes = get_last_quotes(["600000.XSHG", "000001.XSHE"])
for code, quote in quotes.items():
    if quote is not None:
        print(code, quote.last_price, quote.volume)
    else:
        print(code, "暂无快照")
# [/get_last_quotes.2]
# [/get_last_quotes]
