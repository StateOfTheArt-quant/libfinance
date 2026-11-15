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

from libfinance.client import RpcError, get_client
from libfinance.utils.cache import versioned_cache, warn_if_clamped
from libfinance.utils.decorators import export_as_api
from libfinance.utils.utils import to_date_str
from libfinance.utils.validators import check_items_in_container, ensure_list_of_string, ensure_string

#: 后端发布的频率与复权方式。
FREQUENCIES = ("1d",)
ADJUST_TYPES = ("pre", "post", "none")
#: 有日线的证券类型。
TYPES = ("stock", "index")
#: 交易所后缀 -> 市场；不认识的后缀两个市场都核对。
_CN_VENUES = ("XSHG", "XSHE", "XBSE")
#: end_date 早于"今天 − 这么多天"时不核对覆盖：最新已收盘交易日不会比它更早，除非数据断更
#: 十天以上——那时服务端照样拒绝并给出原因。核对要 2–3 个往返（每个约 185 ms，2026-11-11 实测），
#: 不该让查历史区间的每次 get_price 都付。
_COVERAGE_CHECK_DAYS = 10


@versioned_cache
def _daybar_coverage():
    """daybar 全部类型与市场的覆盖；与市场无关，所以 cn、us 共用这一次。"""
    return get_client().call("daybar.coverage", {"type": None}) or {}


@versioned_cache
def _adjust_cutoff(market):
    try:
        return (get_client().call("exfactor.coverage", {"market": market}) or {}).get("cutoff")
    except Exception:
        return None


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
    coverage = _daybar_coverage()
    cutoff = _adjust_cutoff(wanted)

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


def _markets_of(ids):
    suffixes = {code.rpartition(".")[2].upper() for code in ids}
    if suffixes <= set(_CN_VENUES):
        return ("cn",)
    if not suffixes & set(_CN_VENUES):
        return ("us",)
    return ("cn", "us")


def _warn_beyond_coverage(end_date, ids=()):
    """end_date 超出行情覆盖时先说清楚，而不是让调用方拿到一句 RPC 报错。

    服务端拒绝把"数据还没到"伪装成"那天没交易"；这里不改写请求，只提前说出原因与上界。
    只在 end_date 接近今天时核对，且只核对所查代码所在的市场。
    """
    recent = (datetime.date.today() - datetime.timedelta(days=_COVERAGE_CHECK_DAYS)).isoformat()
    if str(end_date) < recent:
        return
    latest = None
    try:
        for market in _markets_of(ids) if ids else ("cn", "us"):
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
    :param include_now: 对日线没有影响，保留以兼容常见的 ``get_price`` 签名
    :param adjust_type: 股票的复权方式：\ ``"pre"`` 前复权（默认）、\ ``"post"`` 后复权或 ``"none"`` 原始价；
        指数原样返回
    :param adjust_orig: 前复权的基准日；省略时为 ``end_date``\ ：价格换算到查询区间最后一天的口径，
        区间之后的除权不影响结果（point-in-time）
    :returns: 以 ``(order_book_id, datetime)`` 为索引的 DataFrame，列为所选字段。

    复权规则：成交量随复权反向缩放，成交额 ``turnover`` 不受复权影响。
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
        if not fields:
            # 空列表不是"全部字段"（那是 None），而是一张没有列的表——几乎一定是调用方的错
            raise ValueError("fields: at least one field expected (None means all fields)")
        if len(set(fields)) < len(fields):
            warnings.warn("duplicated fields: %s" % [f for f in fields if fields.count(f) > 1])
            fields = list(dict.fromkeys(fields))
    start_date, end_date = to_date_str(start_date), to_date_str(end_date)
    if start_date > end_date:
        raise ValueError("start_date must not be after end_date")
    # 两项提示（分档夹紧、超出覆盖）都要先取元数据（describe_capabilities、daybar.coverage、
    # exfactor.coverage、ping），冷启动时是 4 个串行往返（跨公网约 0.8 s）。它们只在"结果不完整"时
    # 才有意义，所以放到查询之后、只在需要时做：成功且从 start_date 起就有数据的调用只付 1 个往返。
    try:
        frame = get_client().get_price(order_book_ids=list(dict.fromkeys(ids)),
                                       start_date=start_date,
                                       end_date=end_date,
                                       frequency=frequency,
                                       fields=fields,
                                       skip_suspended=skip_suspended,
                                       include_now=include_now,
                                       adjust_type=adjust_type,
                                       adjust_orig=to_date_str(adjust_orig) if adjust_orig is not None else None)
    except RpcError as error:
        if _is_coverage_refusal(error):
            _warn_beyond_coverage(end_date, ids)   # 说出覆盖上界，再把服务端的拒绝原样抛出
        raise
    panel = _to_panel(frame)
    if _starts_after(panel, start_date):
        # 分档限制会把 start_date 夹到边界——结果可能是空表或缺了开头，说出来
        warn_if_clamped("get_price", start_date)
    _warn_unknown_codes(panel, ids, end_date)
    return panel


def _warn_unknown_codes(panel, ids, end_date):
    """某个代码一行都没有时，分清"写错了/当日不存在"与"这段时间没有行情"。

    只在出现无行代码时才多问一次 instruments（正常调用不付这个往返）；问不到就不说话。
    """
    if not isinstance(panel, pd.DataFrame) or "order_book_id" not in (panel.index.names or ()):
        return
    present = set(panel.index.get_level_values("order_book_id").unique())
    missing = [code for code in dict.fromkeys(ids) if code not in present]
    if not missing:
        return
    try:
        found = get_client().instruments(order_book_ids=missing, as_of=end_date, last_known=True) or []
        known = {item.get("order_book_id") for item in found}
    except Exception:
        return
    unknown = [code for code in missing if code not in known]
    if unknown:
        warnings.warn(
            "get_price: {} 在 {} 不是已知的证券代码，结果中没有它们的行（不是停牌或缺数据）。"
            "用 instruments() 核对代码。".format(unknown, end_date),
            stacklevel=3,
        )


def _is_coverage_refusal(error):
    return error.kind == "CoverageError" or "outside coverage" in str(error.message)


def _starts_after(panel, start_date):
    """结果为空，或第一行晚于 start_date（可能被分档限制夹紧）。"""
    if not isinstance(panel, pd.DataFrame):
        return False
    if panel.empty:
        return True
    if "datetime" not in (panel.index.names or ()):
        return False
    return panel.index.get_level_values("datetime").min() > pd.Timestamp(start_date)


def _to_panel(frame):
    r"""daybar 的扁平表（\ ``order_book_id, session_date, 字段...``\ ）还原成
    ``(order_book_id, datetime)`` 索引。不认识的形状原样返回，让调用方看见真实的列。"""
    if not isinstance(frame, pd.DataFrame) or not {"order_book_id", "session_date"} <= set(frame.columns):
        return frame
    frame = frame.copy()
    frame["datetime"] = pd.to_datetime(frame["session_date"])
    frame = frame.drop(columns=["session_date"])
    return frame.set_index(["order_book_id", "datetime"]).sort_index()
