#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""行业的成员与权重。

行业以 ``order_book_id``\ （``<分类代码>.<分类体系>``，如 ``801780.SW``、``10.GICS``\ ）命名，
规则与证券相同；行业目录是 ``all_instruments(type="industry")``\ 。按行业查成分与权重，
按证券查所属行业。
"""
from typing import List, Optional

import pandas as pd

from libfinance.client import get_client
from libfinance.utils.decorators import export_as_api
from libfinance.utils.utils import to_date_str
from libfinance.utils.validators import ensure_string


@export_as_api
def get_industry_constituents(order_book_id: str, as_of=None) -> Optional[List[str]]:
    r"""获取某个行业在指定日期的成分证券。

    :param order_book_id: 行业代码，``<分类代码>.<分类体系>``\ ，如 ``"801780.SW"``\ （申万银行）、``"10.GICS"``
    :param as_of: 那一天的事实；省略则取数据已确认的最新日期
    :returns: list[str]，成分证券的 ``order_book_id``\ ；该日没有这个行业时为 ``None``\ 。
    """
    order_book_id = ensure_string(order_book_id, "order_book_id")
    return get_client().get_industry_constituents(
        order_book_id=order_book_id, as_of=to_date_str(as_of) if as_of is not None else None)


@export_as_api
def get_instrument_industry(order_book_ids, source: Optional[str] = None, level: Optional[int] = None,
                            as_of=None) -> pd.DataFrame:
    r"""查询证券在指定日期所属的行业。

    :param order_book_ids: 证券代码列表（单个代码也可以），代码自己确定市场
    :param source: 分类体系，如 ``"SW"``\ （申万）、``"GICS"``\ ；省略则返回全部分类体系
    :param level: 分类层级（申万 1、2、3）；省略则返回全部层级
    :param as_of: 那一天的事实；省略则取数据已确认的最新日期
    :returns: pandas.DataFrame，包含 order_book_id、related_order_book_id（行业代码，如 ``801780.SW``\ ）、
              source、market 和 level。
    """
    return get_client().get_instrument_industry(
        order_book_ids=order_book_ids, source=source, level=level,
        as_of=to_date_str(as_of) if as_of is not None else None)


@export_as_api
def get_industry_weights(order_book_id: str, as_of=None) -> pd.DataFrame:
    r"""获取某个行业在指定日期的成分权重。

    每一行都带 ``methodology``\ ：没有供应商权重和明确方法时不生成权重。

    :param order_book_id: 行业代码，如 ``"801780.SW"``
    :param as_of: 那一天的事实；省略则取数据已确认的最新日期
    :returns: pandas.DataFrame，包含 order_book_id（成分证券）、weight、methodology、source、effective_from、effective_to。
    """
    order_book_id = ensure_string(order_book_id, "order_book_id")
    return get_client().get_industry_weights(
        order_book_id=order_book_id, as_of=to_date_str(as_of) if as_of is not None else None)
