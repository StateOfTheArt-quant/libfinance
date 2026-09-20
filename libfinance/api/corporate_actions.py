#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""公司行动：分红、拆股、配股、分拆。

这四者是除权因子的\ **成因** —— 价格出现跳空时，答案在这里。四个接口的参数与返回
形状完全一致，所以共用同一套参数处理。

``get_spinoffs`` 只有美股有：A 股的分拆上市走另一套流程，不产生这种除权事件，
服务端从代码确定市场；传入 A 股代码会得到不支持该市场的错误。
"""
from typing import List, Optional, Union

import pandas as pd

from libfinance.client import get_client
from libfinance.utils.decorators import export_as_api
from libfinance.utils.utils import to_date_str
from libfinance.utils.validators import ensure_list_of_string


def _args(order_book_ids, start_date, end_date, fields, as_of):
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
        fields=fields, as_of=as_of,
    )


@export_as_api
def get_dividends(
    order_book_ids: Union[str, List[str]],
    start_date=None, end_date=None,
    fields: Optional[Union[str, List[str]]] = None,
    as_of=None,
) -> pd.DataFrame:
    r"""获取分红事件。

    :param order_book_ids: 单个代码或代码列表
    :param start_date: 起始日期，省略则从首个事件开始
    :param end_date: 结束日期，省略则截至最后一个事件
    :param fields: 需要的字段，省略则全部
    :param as_of: 以该时点\ **已知**\ 的信息为准（可见性口径），省略则取最新

    :returns: pandas.DataFrame，分红事件及除息日、每股现金分红等字段；无匹配事件时为空表。
    """
    return get_client().get_dividends(**_args(order_book_ids, start_date, end_date, fields, as_of))


@export_as_api
def get_splits(
    order_book_ids: Union[str, List[str]],
    start_date=None, end_date=None,
    fields: Optional[Union[str, List[str]]] = None,
    as_of=None,
) -> pd.DataFrame:
    r"""获取拆股（送转）事件。

    :param order_book_ids: 单个代码或代码列表
    :param start_date: 起始日期，省略则从首个事件开始
    :param end_date: 结束日期，省略则截至最后一个事件
    :param fields: 返回字段列表，省略则全部
    :param as_of: 只使用截至该时点已知的信息，省略取最新

    :returns: pandas.DataFrame，拆股事件；ratio_from 股变为 ratio_to 股，无匹配事件时为空表。
    """
    return get_client().get_splits(**_args(order_book_ids, start_date, end_date, fields, as_of))


@export_as_api
def get_allotments(
    order_book_ids: Union[str, List[str]],
    start_date=None, end_date=None,
    fields: Optional[Union[str, List[str]]] = None,
    as_of=None,
) -> pd.DataFrame:
    r"""获取配股事件。

    :param order_book_ids: 单个代码或代码列表
    :param start_date: 起始日期，省略则从首个事件开始
    :param end_date: 结束日期，省略则截至最后一个事件
    :param fields: 返回字段列表，省略则全部
    :param as_of: 只使用截至该时点已知的信息，省略取最新

    :returns: pandas.DataFrame，配股事件及相关比例、价格；无匹配事件时为空表。
    """
    return get_client().get_allotments(**_args(order_book_ids, start_date, end_date, fields, as_of))


@export_as_api
def get_spinoffs(
    order_book_ids: Union[str, List[str]],
    start_date=None, end_date=None,
    fields: Optional[Union[str, List[str]]] = None,
    as_of=None,
) -> pd.DataFrame:
    r"""获取美股分拆事件。估值价格需连同估值依据和来源一起阅读。

    :param order_book_ids: 单个代码或代码列表
    :param start_date: 起始日期，省略则从首个事件开始
    :param end_date: 结束日期，省略则截至最后一个事件
    :param fields: 返回字段列表，省略则全部
    :param as_of: 只使用截至该时点已知的信息，省略取最新

    :returns: pandas.DataFrame，美股分拆事件，含 valuation_price、valuation_basis 和 valuation_source 等估值字段。
    """
    return get_client().get_spinoffs(**_args(order_book_ids, start_date, end_date, fields, as_of))
