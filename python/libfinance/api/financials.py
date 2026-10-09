#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""财务数据：PIT 财报（financialstatement）与财务衍生指标（financialmetrics）。

``get_pit_financials_ex`` 按\ **季度**\ 取报表，带 ``as_of``\ ：财报会被追溯修订，\ ``as_of`` 决定用
"当时能看到的"还是"现在最新的"那一版。\ ``get_financial_metrics`` 按\ **交易日**\ 给指标：每天的值来自
那天收盘后能看到的最新报告，本身就是 point-in-time 的。
"""
from typing import List, Union

import pandas as pd

from libfinance.client import get_client
from libfinance.utils.decorators import export_as_api
from libfinance.utils.utils import to_date_str
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
) -> pd.DataFrame:
    r"""获取 point-in-time 财务数据。

    :param order_book_ids: 单个代码或代码列表
    :param fields: 需要的财务字段
    :param start_quarter: 起始季度，如 ``"2024q1"``
    :param end_quarter: 结束季度
    :param as_of: 以该时点\ **已知**\ 的版本为准；省略则取最新。回测里应当传入，否则会
                  用到当时还没发布的修订值。
    :param statements: ``"latest"``\ （每个季度取最新那一版）或 ``"all"``\ （返回全部修订版本）

    :returns: pandas.DataFrame，以 (order_book_id, quarter) 为索引，包含 info_date（披露时间，市场当地时间）、
              请求的财报字段（概念 id，如 ``total_operating_revenue``\ 、``net_income_parent``\ 、``assets``\ ）
              和 if_adjusted（1 表示取自后来报告的比较期）。
    """
    ids = ensure_list_of_string(order_book_ids, "order_book_ids")
    if not ids:
        raise ValueError("order_book_ids: at least one order book id expected")
    fields = ensure_list_of_string(fields, "fields")
    if not fields:
        raise ValueError("fields: at least one field expected")
    ensure_string_in(statements, STATEMENTS, "statements")
    frame = get_client().get_pit_financials_ex(
        order_book_ids=ids, fields=fields,
        start_quarter=_quarter(start_quarter, "start_quarter"),
        end_quarter=_quarter(end_quarter, "end_quarter"),
        as_of=as_of, statements=statements,
    )
    return _indexed(frame, "quarter")


@export_as_api
def get_financial_metrics(
    order_book_ids: Union[str, List[str]],
    fields: Union[str, List[str]],
    start_date=None,
    end_date=None,
) -> pd.DataFrame:
    r"""获取财务衍生指标，CN 与 US 同一套公式。

    每个交易日的值来自那一天收盘后能看到的最新报告：数值在公告日跳变、其间持平；最新报告算不出的为 NaN，
    不退回更早的报告。

    :param order_book_ids: 单个代码或代码列表
    :param fields: 指标名，如 ``roe_lf``\ 、``revenue_ttm``\ 、``net_profit_growth_lyr``\ 、``debt_to_assets_lf``
    :param start_date: 起始日期；与 end_date 都省略时取最近一个交易日
    :param end_date: 结束日期

    :returns: pandas.DataFrame，以 (order_book_id, date) 为索引，每个指标一列。
    """
    ids = ensure_list_of_string(order_book_ids, "order_book_ids")
    if not ids:
        raise ValueError("order_book_ids: at least one order book id expected")
    fields = ensure_list_of_string(fields, "fields")
    if not fields:
        raise ValueError("fields: at least one field expected")
    frame = get_client().get_financial_metrics(
        order_book_ids=ids, fields=fields,
        start_date=to_date_str(start_date) if start_date is not None else None,
        end_date=to_date_str(end_date) if end_date is not None else None,
    )
    return _indexed(frame, "date")


def _indexed(frame, second):
    """服务端的扁平表（order_book_id, <second>, ...）-> (order_book_id, <second>) 索引；已带索引的原样返回。"""
    if not isinstance(frame, pd.DataFrame) or not {"order_book_id", second} <= set(frame.columns):
        return frame
    frame = frame.copy()
    if second != "date":
        # (order_book_id, quarter, known_from) as the server ordered them; "all" repeats a key per report
        return frame.set_index(["order_book_id", second])
    frame["date"] = pd.to_datetime(frame["date"])
    return frame.set_index(["order_book_id", "date"]).sort_index()
