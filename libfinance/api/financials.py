#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""财务数据：PIT 财报与衍生因子。

两个接口都按**季度**取数，并且都带 ``as_of``：财报会被追溯修订，``as_of`` 决定用
"当时能看到的"还是"现在最新的"那一版。做回测时这个参数决定了有没有前视偏差。
"""
from typing import List, Optional, Union

import pandas as pd

from libfinance.client import get_client
from libfinance.utils.decorators import export_as_api
from libfinance.utils.validators import ensure_list_of_string, ensure_string, ensure_string_in

#: 服务端支持的报表口径。取值来自上游 financialmetrics/query.py:196 的白名单
#: （`statements must be 'latest' or 'all'`），不是猜的。
STATEMENTS = ("latest", "all")


def _quarter(value, name):
    """季度形如 ``2026q1``。这里只做形状检查，取值范围由服务端判定。"""
    text = ensure_string(value, name).lower().replace("-", "")
    if "q" not in text:
        raise ValueError("{}: expected a quarter like '2026q1', got {!r}".format(name, value))
    return text


@export_as_api
def get_pit_financials_ex(
    order_book_ids: Union[str, List[str]],
    fields: Union[str, List[str]],
    start_quarter: str,
    end_quarter: str,
    as_of=None,
    statements: str = "latest",
    market: Optional[str] = None,
) -> pd.DataFrame:
    """获取 point-in-time 财务数据。

    :param order_book_ids: 单个代码或代码列表
    :param fields: 需要的财务字段
    :param start_quarter: 起始季度，如 ``"2024q1"``
    :param end_quarter: 结束季度
    :param as_of: 以该时点**已知**的版本为准；省略则取最新。回测里应当传入，否则会
                  用到当时还没发布的修订值。
    :param statements: ``"latest"``（每个季度取最新那一版）或 ``"all"``（返回全部修订版本）
    :param market: 市场，省略则用服务端默认
    """
    ids = ensure_list_of_string(order_book_ids, "order_book_ids")
    if not ids:
        raise ValueError("order_book_ids: at least one order book id expected")
    fields = ensure_list_of_string(fields, "fields")
    if not fields:
        raise ValueError("fields: at least one field expected")
    ensure_string_in(statements, STATEMENTS, "statements")
    return get_client().get_pit_financials_ex(
        order_book_ids=ids, fields=fields,
        start_quarter=_quarter(start_quarter, "start_quarter"),
        end_quarter=_quarter(end_quarter, "end_quarter"),
        as_of=as_of, statements=statements, market=market,
    )


@export_as_api
def get_factor(
    order_book_ids: Union[str, List[str]],
    factors: Union[str, List[str]],
    start_quarter: str,
    end_quarter: str,
    as_of=None,
    market: Optional[str] = None,
) -> pd.DataFrame:
    """获取财务衍生因子。

    :param order_book_ids: 单个代码或代码列表
    :param factors: 因子名；可用因子见服务端的 ``financialmetrics.factor_catalog``
    :param start_quarter: 起始季度，如 ``"2024q1"``
    :param end_quarter: 结束季度
    :param as_of: 同 :func:`get_pit_financials_ex`
    :param market: 市场，省略则用服务端默认
    """
    ids = ensure_list_of_string(order_book_ids, "order_book_ids")
    if not ids:
        raise ValueError("order_book_ids: at least one order book id expected")
    factors = ensure_list_of_string(factors, "factors")
    if not factors:
        raise ValueError("factors: at least one factor expected")
    return get_client().get_factor(
        order_book_ids=ids, factors=factors,
        start_quarter=_quarter(start_quarter, "start_quarter"),
        end_quarter=_quarter(end_quarter, "end_quarter"),
        as_of=as_of, market=market,
    )
