#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""日频因子：qlib、alpha158、Barra CNE5 风格 / 行业因子与描述符（factors-daybar）。

因子名写全名：库 ``owner/library[@rev]``\ （展开为它的全部因子）或因子 ``owner/library/factor[@rev]``\ ，
可以混在一次请求里；\ ``list_factor_libraries``\ 、\ ``list_factors`` 列出可用的名字。值为 float32，NaN 表示
在 universe 中但无法计算。

截面因子（如 ``system/barra-cne5`` 的风格因子）的值取决于截面里有哪些股票，由服务端在读取时计算：默认是
当天全部 A 股，传 ``universe`` 时在这批代码上重算。时序因子（qlib、alpha158、Barra 描述符、行业哑变量）
不受 ``universe`` 影响。
"""
from typing import List, Optional, Union

import pandas as pd

from libfinance.client import get_client
from libfinance.utils.cache import warn_if_clamped, warn_if_truncated
from libfinance.utils.decorators import export_as_api
from libfinance.utils.utils import to_date_str
from libfinance.utils.validators import ensure_list_of_string, ensure_string


@export_as_api
def get_factor_exposure(
    order_book_ids: Union[str, List[str]],
    factor_names: Union[str, List[str]],
    start_date,
    end_date,
    universe: Optional[Union[str, List[str]]] = None,
) -> pd.DataFrame:
    r"""获取因子暴露。

    :param order_book_ids: 单个代码或代码列表
    :param factor_names: 库名（如 ``"system/barra-cne5"``\ ）或因子全名（如 ``"system/qlib/MA5"``\ ），
                         一个或一组，可以混合
    :param start_date: 起始日期；与 ``end_date`` 相同时是当天的截面
    :param end_date: 结束日期
    :param universe: 截面因子的计算范围（代码列表）；省略为当天全部 A 股。只影响截面因子

    :returns: pandas.DataFrame，以 (order_book_id, date) 为索引，每个因子一列，列名为因子全名
              （库展开为 ``owner/library/factor``\ ）。
    """
    ids = ensure_list_of_string(order_book_ids, "order_book_ids")
    if not ids:
        raise ValueError("order_book_ids: at least one order book id expected")
    names = ensure_list_of_string(factor_names, "factor_names")
    if not names:
        raise ValueError("factor_names: at least one factor name expected")
    start, end = to_date_str(start_date), to_date_str(end_date)
    if start > end:
        raise ValueError("start_date {} is after end_date {}".format(start, end))
    members = None if universe is None else ensure_list_of_string(universe, "universe")
    warn_if_clamped("get_factor_exposure", start)
    warn_if_truncated("get_factor_exposure", len(ids))
    frame = get_client().get_factor_exposure(order_book_ids=ids, factor_names=names, start_date=start,
                                             end_date=end, universe=members)
    if not isinstance(frame, pd.DataFrame) or not {"order_book_id", "date"} <= set(frame.columns):
        return frame
    frame = frame.copy()
    frame["date"] = pd.to_datetime(frame["date"])
    return frame.set_index(["order_book_id", "date"])


@export_as_api
def list_factor_libraries() -> pd.DataFrame:
    r"""列出因子库。

    :returns: pandas.DataFrame，列为 name（库名）、version（当前版本）、factors（因子数）、description。
    """
    rows = get_client().list_factor_libraries()
    return pd.DataFrame(list(rows or []), columns=["name", "version", "factors", "description"])


@export_as_api
def list_factors(library: Optional[str] = None) -> List[str]:
    r"""列出因子全名。

    :param library: 库名，如 ``"system/barra-cne5"``\ ；省略为全部库

    :returns: 带版本的因子全名列表，如 ``["system/barra-cne5/SIZE@v2.0.0", ...]``\ ；去掉 ``@版本`` 即读取当前版本
    """
    if library is not None:
        library = ensure_string(library, "library")
    return list(get_client().list_factors(library=library) or [])
