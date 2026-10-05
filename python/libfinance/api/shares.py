#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""股本：统一字段，CN 与 US 同一套（后端 shares 数据族的 get_shares_panel）。"""
from typing import List, Optional, Union

import pandas as pd

from libfinance.client import get_client
from libfinance.utils.decorators import export_as_api
from libfinance.utils.utils import as_of_text, to_date_str
from libfinance.utils.validators import (
    check_items_in_container,
    ensure_list_of_string,
)


#: 后端的统一股本字段（pyshares field_codes），所有市场同一套，单位均为股。
SHARE_FIELDS = (
    "free_float_shares",
    "issued_shares",
    "preferred_shares",
    "restricted_shares",
    "shares_outstanding",
    "tradable_shares",
)


@export_as_api
def get_shares(
    order_book_ids: Union[str, List[str]],
    start_date=None,
    end_date=None,
    fields: Optional[Union[str, List[str]]] = None,
    as_of=None,
) -> pd.DataFrame:
    r"""获取证券逐交易日的股本（证券层级：股类值优先于公司层级）。

    :param order_book_ids: 单个代码或代码列表，可混合市场，如 ``"600000.XSHG"``\ 、\ ``"AAPL.US"``
    :param start_date: 开始日期；省略为 ``end_date`` 前 92 天
    :param end_date: 结束日期；省略为交易日历的最后一个交易日
    :param fields: 统一股本字段，省略为全部：``free_float_shares``\ 、\ ``issued_shares``\ 、
        ``preferred_shares``\ 、\ ``restricted_shares``\ 、\ ``shares_outstanding``\ 、\ ``tradable_shares``
    :param as_of: 知识截止时点（日期或 ISO 时间戳），只用当时已知的股本；省略取最新

    :returns: pandas.DataFrame，以 (order_book_id, date) 为索引、每个字段一列；某市场不发布的字段为 NaN。
    """
    order_book_ids = ensure_list_of_string(order_book_ids, "order_book_ids")
    if not order_book_ids:
        raise ValueError("order_book_ids: at least one order book id expected")

    if fields is not None:
        fields = ensure_list_of_string(fields, "fields")
        check_items_in_container(fields, SHARE_FIELDS, "fields")

    if start_date is not None:
        start_date = to_date_str(start_date)
    if end_date is not None:
        end_date = to_date_str(end_date)
    if start_date is not None and end_date is not None and start_date > end_date:
        raise ValueError(
            "invalid date range: [{!r}, {!r}]".format(start_date, end_date)
        )

    frame = get_client().get_shares(
        order_book_ids=order_book_ids,
        start_date=start_date,
        end_date=end_date,
        fields=fields,
        as_of=as_of_text(as_of),
    )
    return _indexed(frame)


def _indexed(frame):
    """服务端的扁平表（order_book_id, date, 字段...）-> (order_book_id, date) 索引；已带索引的原样返回。"""
    if not isinstance(frame, pd.DataFrame) or not {"order_book_id", "date"} <= set(frame.columns):
        return frame
    frame = frame.copy()
    frame["date"] = pd.to_datetime(frame["date"])
    return frame.set_index(["order_book_id", "date"]).sort_index()
