#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""主题（概念）：证券属于哪些主题、主题包含哪些证券、成分各占多少。

主题以 order_book_id（300900.THS）命名，目录是 all_instruments(type="theme")；source 是主题定义方
（THS 为同花顺）；as_of 是那一天的事实。同花顺主题的数据从 2026-06-29 起，更早的 as_of 抛 CoverageError。
"""
from libfinance import all_instruments, get_instrument_themes, get_theme_constituents, get_theme_weights

# [get_instrument_themes]
# [get_instrument_themes.1]
# 证券在当日所属的主题；related_order_book_id 就是主题代码。
print(get_instrument_themes(["600000.XSHG", "000001.XSHE"], source="THS"))
# [/get_instrument_themes.1]
# [/get_instrument_themes]

# [get_theme_constituents]
# [get_theme_constituents.1]
# 主题代码来自目录，不硬编码可能已失效的编号。
themes = all_instruments(type="theme", source="THS")
print(themes.head())
theme = themes.iloc[0]["order_book_id"]
print(get_theme_constituents(theme))
print(get_theme_constituents(theme, as_of="2026-07-31"))  # 那一天还没有这个主题时为 None
# [/get_theme_constituents.1]
# [/get_theme_constituents]

# [get_theme_weights]
# [get_theme_weights.1]
# 同花顺主题的权重是由成分名单推出的等权（methodology=derived_equal_weight），不是供应商权重。
print(get_theme_weights(theme))
# [/get_theme_weights.1]
# [/get_theme_weights]
