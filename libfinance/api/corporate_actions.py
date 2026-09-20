#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""公司行动：分红、拆股、配股、分拆。

这四者是除权因子的\ **成因** —— 价格出现跳空时，答案在这里。四个接口的参数与返回
形状完全一致，所以共用同一套参数处理。

``get_spinoffs`` 只有美股有：A 股的分拆上市走另一套流程，不产生这种除权事件，
所以它不带 ``market`` 默认值之外的特殊处理 —— 传 ``market="cn"`` 会从服务端得到
"未绑定"，那不是"这段时间没有分拆"。
"""
from typing import List, Optional, Union

import pandas as pd

from libfinance.client import get_client
from libfinance.utils.decorators import export_as_api
from libfinance.utils.utils import to_date_str
from libfinance.utils.validators import ensure_list_of_string


def _args(order_book_ids, start_date, end_date, fields, as_of, market):
    r"""三个接口的参数处理完全一样，只有 RPC 名不同。

    **调用点不做动态派发**\ （不写 getattr(client, rpc)）：test/test_rpc_contract.py 靠
    静态扫描源码里的 client.<name>( 来核对"客户端调的 RPC 服务端有没有"，动态派发会让
    这三个接口在那条闸门下隐形 —— 而它们恰恰是新接的、最可能写错名字的。
    """
    ids = ensure_list_of_string(order_book_ids, "order_book_ids")
    if not ids:
        raise ValueError("order_book_ids: at least one order book id expected")
    if fields is not None:
        fields = ensure_list_of_string(fields, "fields")
    start_date = to_date_str(start_date) if start_date is not None else None
    end_date = to_date_str(end_date) if end_date is not None else None
    if start_date is not None and end_date is not None and start_date > end_date:
        raise ValueError("invalid date range: [{!r}, {!r}]".format(start_date, end_date))
    return dict(
        order_book_ids=ids, start_date=start_date, end_date=end_date,
        fields=fields, as_of=as_of, market=market,
    )


@export_as_api
def get_dividends(
    order_book_ids: Union[str, List[str]],
    start_date=None, end_date=None,
    fields: Optional[Union[str, List[str]]] = None,
    as_of=None, market: Optional[str] = None,
) -> pd.DataFrame:
    r"""获取分红事件。

    :param order_book_ids: 单个代码或代码列表
    :param start_date: 起始日期，省略则从首个事件开始
    :param end_date: 结束日期，省略则截至最后一个事件
    :param fields: 需要的字段，省略则全部
    :param as_of: 以该时点\ **已知**\ 的信息为准（可见性口径），省略则取最新
    :param market: 市场，省略则用服务端默认
    """
    return get_client().get_dividends(**_args(order_book_ids, start_date, end_date, fields, as_of, market))


@export_as_api
def get_splits(
    order_book_ids: Union[str, List[str]],
    start_date=None, end_date=None,
    fields: Optional[Union[str, List[str]]] = None,
    as_of=None, market: Optional[str] = None,
) -> pd.DataFrame:
    """获取拆股（送转）事件。参数含义同 :func:`get_dividends`。"""
    return get_client().get_splits(**_args(order_book_ids, start_date, end_date, fields, as_of, market))


@export_as_api
def get_allotments(
    order_book_ids: Union[str, List[str]],
    start_date=None, end_date=None,
    fields: Optional[Union[str, List[str]]] = None,
    as_of=None, market: Optional[str] = None,
) -> pd.DataFrame:
    """获取配股事件。参数含义同 :func:`get_dividends`。"""
    return get_client().get_allotments(**_args(order_book_ids, start_date, end_date, fields, as_of, market))


@export_as_api
def get_spinoffs(
    order_book_ids: Union[str, List[str]],
    start_date=None, end_date=None,
    fields: Optional[Union[str, List[str]]] = None,
    as_of=None, market: Optional[str] = None,
) -> pd.DataFrame:
    r"""获取分拆事件（**仅美股**）。参数含义同 :func:`get_dividends`。

    母公司股东按比例获得子公司股份。除权要的是钱，而子公司在除权当日往往还没有独立
    市价，所以 ``valuation_price`` 是估出来的 —— ``valuation_basis`` 与
    ``valuation_source`` 说的就是按哪种口径估的。这三列要一起看：只取价格不看口径，
    等于替数据假定了一个它没说的东西。\ ``d_spin_per_share`` 是折算到每股的分拆价值。

    A 股不产生这种事件，\ ``market="cn"`` 会得到"未绑定"而不是空表。
    """
    return get_client().get_spinoffs(**_args(order_book_ids, start_date, end_date, fields, as_of, market))
