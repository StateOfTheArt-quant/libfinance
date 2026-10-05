#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""主题（概念）的成分与权重。

主题以 ``order_book_id``\ （``<主题编号>.<定义方>``，如 ``885311.THS``\ ）命名，规则与证券相同；
主题目录是 ``all_instruments(type="theme")``\ 。按主题查成分与权重，按证券查所属主题。
"""
from typing import List, Optional

import pandas as pd

from libfinance.client import get_client
from libfinance.utils.decorators import export_as_api
from libfinance.utils.utils import to_date_str
from libfinance.utils.validators import ensure_string


def _as_of(as_of):
    return to_date_str(as_of) if as_of is not None else None


@export_as_api
def get_theme_constituents(order_book_id: str, as_of=None) -> Optional[List[str]]:
    r"""获取主题在指定日期的成分证券。

    :param order_book_id: 主题代码，如 ``"885311.THS"``
    :param as_of: 那一天的事实；省略则取数据已确认的最新日期
    :returns: list[str]，成分证券的 ``order_book_id``\ ；该日没有这个主题时为 ``None``\ 。
    """
    order_book_id = ensure_string(order_book_id, "order_book_id")
    return get_client().get_theme_constituents(order_book_id=order_book_id, as_of=_as_of(as_of))


@export_as_api
def get_instrument_themes(order_book_ids, source: Optional[str] = None, as_of=None) -> pd.DataFrame:
    r"""查询证券在指定日期所属的主题。

    :param order_book_ids: 证券代码列表（单个代码也可以），代码自己确定市场
    :param source: 主题定义方，如 ``"THS"``\ ；省略则返回全部定义方
    :param as_of: 那一天的事实；省略则取数据已确认的最新日期
    :returns: pandas.DataFrame，包含 order_book_id、related_order_book_id（主题代码）、source、market 和 level。
    """
    return get_client().get_instrument_themes(
        order_book_ids=order_book_ids, source=source, as_of=_as_of(as_of))


@export_as_api
def get_theme_weights(order_book_id: str, as_of=None) -> pd.DataFrame:
    r"""获取主题在指定日期的成分权重。

    每一行都带 ``methodology``\ ：同花顺主题的 ``derived_equal_weight`` 是由成分名单推出的等权，
    不是供应商权重。

    :param order_book_id: 主题代码，如 ``"885311.THS"``
    :param as_of: 那一天的事实；省略则取数据已确认的最新日期
    :returns: pandas.DataFrame，包含 order_book_id（成分证券）、weight、methodology、source、effective_from、effective_to。
    """
    order_book_id = ensure_string(order_book_id, "order_book_id")
    return get_client().get_theme_weights(order_book_id=order_book_id, as_of=_as_of(as_of))
