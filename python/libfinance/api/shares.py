#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""股本结构查询接口。"""
from typing import List, Optional, Union

import pandas as pd

from libfinance.client import get_client
from libfinance.utils.decorators import export_as_api
from libfinance.utils.utils import to_date_str
from libfinance.utils.validators import (
    check_items_in_container,
    ensure_list_of_string,
)


SHARE_FIELDS = (
    "total",
    "total_a",
    "circulation_a",
    "non_circulation_a",
    "free_circulation",
    "preferred_shares",
)


@export_as_api
def get_shares(
    order_book_ids: Union[str, List[str]],
    start_date=None,
    end_date=None,
    fields: Optional[Union[str, List[str]]] = None,
) -> pd.DataFrame:
    r"""获取股票在指定日期范围内的股本结构。

    :param order_book_ids: 单个股票代码或股票代码列表
    :param start_date: 开始日期；省略时从首个股本事件开始
    :param end_date: 结束日期；省略时截至最后一个股本事件
    :param fields: 需要返回的股本字段；省略时返回全部字段

    :returns: pandas.DataFrame，以 (order_book_id, date) 为索引；所有股本字段单位均为股。
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

    return get_client().get_shares(
        order_book_ids=order_book_ids,
        start_date=start_date,
        end_date=end_date,
        fields=fields,
    )
