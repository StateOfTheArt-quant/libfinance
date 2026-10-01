#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""日线行情：股票与指数在同一个 daybar 聚合包后面。

签名取自后端 daybar 数据族（\ ``daybar.get_price``\ ）：代码写成 ``order_book_id``\ ，股票与指数
可以混在一批里，由服务端按 instrument 给出的类型路由——股票按 ``adjust_type`` 复权，指数原样
返回。本模块只做参数检查、越界提示与结果的形状。
"""
import datetime
import warnings
from typing import List, Optional, Union

import pandas as pd

from libfinance.client import get_client
from libfinance.utils.cache import versioned_cache, warn_if_clamped
from libfinance.utils.decorators import export_as_api
from libfinance.utils.utils import to_date_str
from libfinance.utils.validators import check_items_in_container, ensure_list_of_string, ensure_string

#: 后端发布的频率与复权方式。
FREQUENCIES = ("1d",)
ADJUST_TYPES = ("pre", "post", "none")
#: 有日线的证券类型。
TYPES = ("stock", "index")


@export_as_api
@versioned_cache
def get_price_coverage(market: str = "cn") -> dict:
    r"""日线行情的覆盖区间，按证券类型与场所给出：\ ``{"stock": {"XSHG": {...}}, "index": {...}}``\ 。

    :param market: 市场，\ ``"cn"``\ （默认）或 ``"us"``

    **与交易日历的覆盖不是一回事**\ ：日历是提前发布的，而行情只到最后一个已收盘交易日。

    每个场所给出：

    ==============  ==========================================================
    键              含义
    ==============  ==========================================================
    start           最早有行情的日期
    end             能查到的最后一天。股票取复权价的上界：默认 ``adjust_type="pre"``
                    要用除权因子，它的 cutoff 早于行情时取两者的较小值；指数不复权，
                    即 ``raw_end``
    raw_end         未复权价能查到的最后一天
    adjust_cutoff   除权因子的 cutoff（只有股票有）
    ==============  ==========================================================

    :raises RuntimeError: 服务端没有给出该市场的任何覆盖信息时抛出。\ **不返回空字典**
        —— 否则"查不到覆盖信息"和"这个市场没有行情"在调用方看来一模一样。
    :returns: dict，``{类型: {场所: {start, end, raw_end[, adjust_cutoff]}}}``\ 。
    """
    wanted = ensure_string(market, "market").upper()
    coverage = get_client().call("daybar.coverage", {"type": None}) or {}
    try:
        cutoff = (get_client().call("exfactor.coverage", {"market": wanted}) or {}).get("cutoff")
    except Exception:
        cutoff = None

    out = {}
    for code_type in TYPES:
        venues = ((coverage.get(code_type) or {}).get(wanted)) or {}
        for venue, item in sorted(venues.items()):
            if not isinstance(item, dict) or not item.get("coverage_end"):
                continue
            raw_end = item["coverage_end"]
            entry = {"start": item.get("coverage_start"), "end": raw_end, "raw_end": raw_end}
            if code_type == "stock" and cutoff:
                entry["end"] = min(raw_end, cutoff)
                entry["adjust_cutoff"] = cutoff
            out.setdefault(code_type, {})[venue] = entry
    if not out:
        raise RuntimeError(
            "get_price_coverage: 服务端没有给出 market={!r} 的覆盖信息。"
            "这不表示该市场没有行情，而是拿不到区间——请检查 market 取值。".format(market)
        )
    return out


def _warn_beyond_coverage(end_date):
    """end_date 超出行情覆盖时先说清楚，而不是让调用方拿到一句 RPC 报错。

    服务端拒绝把"数据还没到"伪装成"那天没交易"；这里不改写请求，只提前说出原因与上界。
    """
    latest = None
    try:
        for market in ("cn", "us"):
            for venues in get_price_coverage(market).values():
                for item in venues.values():
                    if item.get("end") and (latest is None or item["end"] > latest):
                        latest = item["end"]
    except Exception:
        return
    if latest and str(end_date) > latest:
        warnings.warn(
            "get_price: end_date={} 超出行情覆盖（最新已收盘交易日 {}）。服务端会拒绝"
            "这个区间——数据还没到不等于那天没交易。用 get_price_coverage() 查上界。"
            .format(end_date, latest),
            stacklevel=3,
        )


@export_as_api
def get_price(
    order_book_ids: Union[str, List[str]],
    start_date,
    end_date,
    frequency: str = "1d",
    fields: Optional[Union[str, List[str]]] = None,
    skip_suspended: bool = False,
    include_now: bool = True,
    adjust_type: str = "pre",
    adjust_orig: Optional[datetime.date] = None,
) -> pd.DataFrame:
    r"""获取股票与指数的日线。

    :param order_book_ids: 单个代码或代码列表，股票与指数可以混在一批里，如
        ``["600000.XSHG", "000300.XSHG", "AAPL.US"]``\ 。代码按 ``end_date`` 当日解析。
    :param start_date: 开始日期，必填
    :param end_date: 结束日期，必填；应落在行情覆盖范围内（\ :func:`get_price_coverage`\ ）
    :param frequency: 只发布日频 ``"1d"``
    :param fields: 返回字段，省略取全部：\ ``open, high, low, close, volume, turnover, limit_up, limit_down``\ 。
        字段由服务端核对。
    :param skip_suspended: 是否去掉无成交的日子（成交量为 0），默认 False。只发布收盘点位、没有成交量
        的指数日不算停牌。
    :param include_now: 对日线没有影响，保留与 rqdata 的 ``get_price`` 对齐
    :param adjust_type: 股票的复权方式：\ ``"pre"`` 前复权（默认）、\ ``"post"`` 后复权或 ``"none"`` 原始价；
        指数原样返回
    :param adjust_orig: 复权基准日；省略使用除权因子的 cutoff
    :returns: 以 ``(order_book_id, datetime)`` 为索引的 DataFrame，列为 ``permanent_id`` 与所选字段。

    规则同 rqalpha：成交量随复权反向缩放，成交额 ``turnover`` 不受复权影响。
    """
    ids = ensure_list_of_string(order_book_ids, "order_book_ids")
    if not ids:
        raise ValueError("order_book_ids: at least one order book id expected")
    ensure_string(frequency, "frequency")
    check_items_in_container(frequency, list(FREQUENCIES), "frequency")
    ensure_string(adjust_type, "adjust_type")
    check_items_in_container(adjust_type, list(ADJUST_TYPES), "adjust_type")
    if not isinstance(skip_suspended, bool):
        raise ValueError("skip_suspended: a bool expected, got {!r}".format(skip_suspended))
    if fields is not None:
        fields = ensure_list_of_string(fields, "fields")
        if len(set(fields)) < len(fields):
            warnings.warn("duplicated fields: %s" % [f for f in fields if fields.count(f) > 1])
            fields = list(dict.fromkeys(fields))
    start_date, end_date = to_date_str(start_date), to_date_str(end_date)
    if start_date > end_date:
        raise ValueError("start_date must not be after end_date")
    # 分档限制会把 start_date 夹到边界——结果可能是一张空表，先说出来。
    warn_if_clamped("get_price", start_date)
    _warn_beyond_coverage(end_date)

    frame = get_client().get_price(order_book_ids=list(dict.fromkeys(ids)),
                                   start_date=start_date,
                                   end_date=end_date,
                                   frequency=frequency,
                                   fields=fields,
                                   skip_suspended=skip_suspended,
                                   include_now=include_now,
                                   adjust_type=adjust_type,
                                   adjust_orig=to_date_str(adjust_orig) if adjust_orig is not None else None)
    return _to_panel(frame)


def _to_panel(frame):
    r"""daybar 的扁平表（\ ``order_book_id, permanent_id, session_date, 字段...``\ ）还原成
    ``(order_book_id, datetime)`` 索引。不认识的形状原样返回，让调用方看见真实的列。"""
    if not isinstance(frame, pd.DataFrame) or not {"order_book_id", "session_date"} <= set(frame.columns):
        return frame
    frame = frame.copy()
    frame["datetime"] = pd.to_datetime(frame["session_date"])
    frame = frame.drop(columns=["session_date"])
    return frame.set_index(["order_book_id", "datetime"]).sort_index()
