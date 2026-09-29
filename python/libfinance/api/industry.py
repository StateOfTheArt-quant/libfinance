#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""行业的成员与权重。

行业以 ``order_book_id``\ （``<分类代码>.<分类体系>``，如 ``801780.SW``、``10.GICS``\ ）命名，
规则与证券相同。按证券查所属行业的 ``get_instrument_industry`` 在 index_components 里；
这里是按行业查的两个：成分证券与权重。
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
