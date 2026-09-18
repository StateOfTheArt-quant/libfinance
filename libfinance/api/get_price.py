#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from typing import List, Union
import datetime

import pandas as pd
import json
import warnings
import pdb

from libfinance.client import get_client
from libfinance.utils.cache import versioned_cache, warn_if_clamped
from libfinance.utils.decorators import export_as_api, ttl_cache, compatible_with_parm
from libfinance.utils.datetime_func import convert_dateteime_to_timestamp
from libfinance.utils.utils import to_date_str

from libfinance.utils.validators import (
    ensure_string,
    ensure_list_of_string,
    check_items_in_container,
    ensure_instruments,
    ensure_date_range,
    is_panel_removed,
)

# 日频字段。股票这两组必须与上游 daybar 的权威列集逐字一致——
# pystockdaybarcn.dataset.VALUE_COLUMNS =
#     ("open", "high", "low", "close", "volume", "turnover", "limit_up", "limit_down")
# reader 对未知字段是 InvalidFieldError，不会静默忽略。此前这里写的是 rqdatac 口径的
# total_turnover 与 prev_close：前者在上游叫 turnover，后者上游根本没有，于是
# fields=None（默认）的每一次调用都会被 reader 拒掉。
#
# 其余几组（future / fund / spot / option / convertible / repo）上游**都还没有 artifact**，
# libfinanced 目前只出 CN 股票日频。留着它们只是为了 classify_order_book_ids 的分支不动；
# 真传了这些标的，服务端会明确报错而不是给出半份数据。
DAYBAR_FIELDS = {
    "future": ["settlement", "prev_settlement", "open_interest", "limit_up", "limit_down",
               "day_session_open"],
    "common": ["open", "close", "high", "low", "turnover", "volume"],
    "stock": ["limit_up", "limit_down"],
    "fund": ["limit_up", "limit_down", "num_trades", "iopv"],
    "spot": ["settlement", "prev_settlement", "open_interest", "limit_up", "limit_down"],
    "option": ["open_interest", "strike_price", "contract_multiplier", "prev_settlement", "settlement", "limit_up",
               "limit_down", "day_session_open"],
    "convertible": ["limit_up", "limit_down", "num_trades"],
    "index": [],
    "repo": ["num_trades"],
}

WEEKBAR_FIELDS = {
    "future": ["settlement", "prev_settlement", "open_interest", "day_session_open"],
    "common": ["open", "close", "high", "low", "total_turnover", "volume"],
    "stock": ["num_trades"],
    "fund": ["num_trades", "iopv"],
    "spot": ["settlement", "prev_settlement", "open_interest"],
    "option": ["open_interest", "strike_price", "contract_multiplier", "settlement", "day_session_open"],
    "convertible": ["num_trades"],
    "index": [],
    "repo": ["num_trades"],
}

MINBAR_FIELDS = {
    "future": ["trading_date", "open_interest"],
    "common": ["open", "close", "high", "low", "total_turnover", "volume"],
    "stock": ["num_trades"],
    "fund": ["num_trades", "iopv"],
    "spot": ["trading_date", "open_interest"],
    "option": ["trading_date", "open_interest"],
    "convertible": ["num_trades"],
    "index": [],
    "repo": [],
}

def classify_order_book_ids(order_book_ids, as_of=None):
    """按类型给标的分流。``as_of`` 决定用哪个时点的代码表 —— 见 ensure_instruments。"""
    ins_list = ensure_instruments(order_book_ids, as_of=as_of)
    _order_book_ids = []
    stocks = []
    funds = []
    indexes = []
    futures = []
    futures_888 = {}
    spots = []
    options = []
    convertibles = []
    repos = []
    for ins in ins_list:
        if ins.order_book_id not in _order_book_ids:
            _order_book_ids.append(ins.order_book_id)
            if ins.type == "CS":
                stocks.append(ins.order_book_id)
            elif ins.type == "INDX":
                indexes.append(ins.order_book_id)
            elif ins.type in {"ETF", "LOF", "SF", "FUND"}:
                funds.append(ins.order_book_id)
            elif ins.type == "Future":
                if ins.order_book_id.endswith(("88", "889")):
                    futures_888[ins.order_book_id] = ins.underlying_symbol
                futures.append(ins)
            elif ins.type == "Spot":
                spots.append(ins.order_book_id)
            elif ins.type == "Option":
                options.append(ins.order_book_id)
            elif ins.type == "Convertible":
                convertibles.append(ins.order_book_id)
            elif ins.type == "Repo":
                repos.append(ins.order_book_id)
    return _order_book_ids, stocks, funds, indexes, futures, futures_888, spots, options, convertibles, repos

def _ensure_date(start_date, end_date, stocks, funds, indexes, futures, spots, options, convertibles, repos):
    default_start_date, default_end_date = ensure_date_range(start_date, end_date)

    start_date = to_date_str(start_date) if start_date else default_start_date
    end_date = to_date_str(end_date) if end_date else default_end_date
    if start_date < "2000-01-04":
        warnings.warn("start_date is earlier than 2000-01-04, adjusted to 2000-01-04")
        start_date = "2000-01-04"
    return start_date, end_date

def _ensure_fields(fields, fields_dict, stocks, funds, futures, futures888, spots, options, convertibles, indexes,
                   repos):
    has_dominant_id = False
    future_only = futures and not any([stocks, funds, spots, options, convertibles, indexes, repos])
    all_fields = set(fields_dict["common"])
    if futures:
        all_fields.update(fields_dict["future"])
    if stocks:
        all_fields.update(fields_dict["stock"])
    if funds:
        all_fields.update(fields_dict["fund"])
    if spots:
        all_fields.update(fields_dict["spot"])
    if options:
        all_fields.update(fields_dict["option"])
    if convertibles:
        all_fields.update(fields_dict["convertible"])
    if indexes:
        all_fields.update(fields_dict["index"])
    if repos:
        all_fields.update(fields_dict["repo"])
    if future_only and futures888 and len(futures) == len(futures888) and not fields:
        has_dominant_id = True

    if fields:
        fields = ensure_list_of_string(fields, "fields")
        fields_set = set(fields)
        if len(fields_set) < len(fields):
            warnings.warn("duplicated fields: %s" % [f for f in fields if fields.count(f) > 1])
            fields = list(fields_set)
        # 只有期货类型
        if 'dominant_id' in fields:
            fields.remove("dominant_id")
            if not fields:
                raise ValueError("can't get dominant_id separately, please use futures.get_dominant")
            if futures888:
                has_dominant_id = True
            else:
                warnings.warn(
                    "only if one of the order_book_id is future and contains 88/888/99/889 can the dominant_id be selected in fields")
        check_items_in_container(fields, all_fields, "fields")
        return fields, has_dominant_id
    else:
        return list(all_fields), has_dominant_id



@export_as_api
@versioned_cache
def get_price_coverage(market=None) -> dict:
    """日频行情各交易所的覆盖区间，形如 ``{"XSHG": {"start": ..., "end": ...}}``。

    **与交易日历的覆盖不是一回事**：日历是提前发布的（本机实测到 2026-12-31），
    而行情只到最后一个已收盘交易日（2026-09-15）。"查最近 10 天"之所以会失败，
    正是因为它把 end_date 取成了今天。

    ``end`` 是**复权价**能查到的最后一天（默认 adjust_type="pre" 要用 exfactor，而它的
    cutoff 通常比日频更早）；``raw_end`` 是未复权价能到哪天。

    用它先问一句，就不必靠试错：

        cov = get_price_coverage()["XSHG"]
        df = get_price(ids, start_date=..., end_date=cov["end"])
    """
    args = {} if market is None else {"market": market}
    info = get_client().call("daybar.dataset_info", args)
    out = {}
    for mic, item in (info or {}).items():
        if isinstance(item, dict) and item.get("coverage_end"):
            out[mic] = {"start": item.get("coverage_start"), "end": item["coverage_end"],
                        "raw_end": item["coverage_end"]}
    # 复权价还要 exfactor，而它的 cutoff 通常**更早**（实测 daybar 到 09-14、exfactor
    # 到 09-12）。默认 adjust_type="pre" 时真正的上界是两者的较小值，所以这里直接把
    # end 夹到它 —— 否则调用方按 end 去查会撞上
    # "2026-09-14 is past this release's cutoff 2026-09-12"。
    # raw_end 保留未复权价能到哪天。
    try:
        cutoff = (get_client().call("exfactor.dataset_info", args) or {}).get("cutoff")
    except Exception:
        cutoff = None
    if cutoff:
        for item in out.values():
            item["adjust_cutoff"] = cutoff
            if item["end"] > cutoff:
                item["end"] = cutoff
    return out


def _warn_beyond_coverage(end_date):
    """end_date 超出行情覆盖时先说清楚，而不是让调用方拿到一句 RPC 报错。

    服务端的拒绝本身是对的 ——"a date this release does not reach is not a date with
    no trading" —— 它拒绝把"数据还没到"伪装成"那天没交易"。这里不改写调用方的请求，
    只是提前把原因和可用的上界说出来。
    """
    if not end_date:
        return
    try:
        cov = get_price_coverage()
    except Exception:
        return
    ends = [v["end"] for v in cov.values() if v.get("end")]
    if not ends:
        return
    latest = max(ends)
    if str(end_date) > latest:
        warnings.warn(
            "get_price: end_date={} 超出行情覆盖（最新已收盘交易日 {}）。服务端会拒绝"
            "这个区间——数据还没到不等于那天没交易。用 get_price_coverage() 查上界。"
            .format(end_date, latest),
            stacklevel=3,
        )


@export_as_api
def get_price(
    order_book_ids: list,
    start_date: str,
    end_date: str,
    frequency: str="1d",
    fields: List[str]=None,
    skip_suspended: bool=False,
    include_now: bool=True,
    adjust_type: str="pre",
    adjust_orig:datetime.datetime = None) -> pd.DataFrame:
    """获取指定合约的历史 k 线行情，支持任意日频率xd(1d,5d)和任意分钟频率xm(1m,3m,5m,15m)的历史数据。

    .. warning::

       **0.0.2 起 ``adjust_type`` 的默认值从 ``"none"`` 改为 ``"pre"``**（同时
       ``skip_suspended`` 从 ``True`` 改为 ``False``），与服务端的默认值一致。

       这是一个**静默的数值变化**：不会报错，但不传 ``adjust_type`` 时拿到的价格
       从不复权变成了前复权。依赖旧行为的代码请显式写 ``adjust_type="none"``。

       改的理由是此前两边默认值相反 —— 同一个语义调用，走客户端和走服务端内部会得到
       不同的数字，而这种不一致没有任何人能从文档上看出来。
    
    :param order_book_ids: 多个标的合约代码, 必填项
    :param start_date: 开始日期，必填项
    :param end_date: 结束日期，必填项
    :param frequency: 获取数据什么样的频率进行。'1d'或'1m'分别表示每日和每分钟
    :param fields: 返回数据字段
    :param skip_suspended: 是否跳过停牌数据
    :param include_now: 是否包含当前数据
    :param adjust_type: 复权类型，默认为前复权 pre；可选 pre, none, post
    
    =========================   ===================================================
    fields                      字段名
    =========================   ===================================================
    datetime                    时间戳
    open                        开盘价
    high                        最高价
    low                         最低价
    close                       收盘价
    volume                      成交量
    total_turnover              成交额
    open_interest               持仓量（期货专用）
    basis_spread                期现差（股指期货专用）
    settlement                  结算价（期货日线专用）
    prev_settlement             结算价（期货日线专用）
    =========================   ===================================================
    
    Example1::
    
        获取中国平安和浦发银行 2024-03-01至2024-03-11之间的交易数据
    
    ..  code-block:: python3
        
        import pandas as pd
        from libfinance import get_price
    
        >>> data = get_price(order_book_ids=["000001.XSHE","600000.XSHG"], start_date="2024-03-01", end_date="2024-03-11")
        >>> print(data)
        
                                   open   high    low  close       volume
        order_book_id datetime                                           
        000001.XSHE   2024-03-01  10.59  10.60  10.43  10.49  182810290.0
                      2024-03-04  10.45  10.50  10.32  10.33  165592954.0
                      2024-03-05  10.30  10.47  10.26  10.43  181731907.0
                      2024-03-06  10.40  10.45  10.33  10.33  134564016.0
                      2024-03-07  10.33  10.64  10.33  10.38  201616589.0
                      2024-03-08  10.35  10.44  10.30  10.38  111397428.0
                      2024-03-11  10.38  10.47  10.34  10.47  121067298.0
        600000.XSHG   2024-03-01   7.13   7.16   7.10   7.11   29431801.0
                      2024-03-04   7.12   7.12   7.05   7.07   27855963.0
                      2024-03-05   7.05   7.18   7.04   7.16   41756232.0
                      2024-03-06   7.17   7.22   7.12   7.12   25918749.0
                      2024-03-07   7.12   7.20   7.11   7.14   24690348.0
                      2024-03-08   7.12   7.17   7.11   7.12   19861794.0
                      2024-03-11   7.13   7.17   7.06   7.11   26195498.0
    
    """
    if not frequency.endswith(("d", "w")):
        return ValueError("current, only suport xd and xw frequency data")
    
    # tick数据
    if frequency == "tick":
        return ValueError("current, only suport xd and xw data")
    elif frequency.endswith(("d", "m", "w")):
        duration = int(frequency[:-1])
        _frequency = frequency[-1]
        assert 1 <= duration <= 240, "frequency should in range [1, 240]"
        if _frequency == "m" and duration not in (1, 5, 15, 30, 60):
            raise ValueError("frequency should be str like 1m, 5m, 15m 30m,or 60m")
        elif _frequency == 'w' and duration not in (1,):
            raise ValueError("Weekly frequency should be str '1w'")
    else:
       raise ValueError("frequency should be str like 1d, 1m, 5m or tick")
    
    valid_adjust = ["pre", "post", "none"]
    ensure_string(adjust_type, "adjust_type")
    check_items_in_container(adjust_type, valid_adjust, "adjust_type")
    order_book_ids = ensure_list_of_string(order_book_ids, "order_book_ids")
    
    assert isinstance(skip_suspended, bool), "'skip_suspended' should be a bool"
    
    
    # 按**查询窗口末端**解析代码，不是按今天 —— 与服务端 compose/price.py 同口径。
    # 否则已退市的证券在这里就被当成无效代码丢掉，服务端根本没机会回答。
    order_book_ids, stocks, funds, indexes, futures, futures888, spots, options, convertibles, repos = classify_order_book_ids(
        order_book_ids, as_of=end_date)
    if not order_book_ids:
        warnings.warn("no valid instrument")
        return
    
    start_date, end_date = _ensure_date(
        start_date, end_date, stocks, funds, indexes, futures, spots, options, convertibles, repos
    )
    # 分档限制会把 start_date 夹到边界，end_date 早于边界时也一起上拉 —— 结果是一张
    # 空表，而调用方无从知道是档位问题还是真的没数据。先说出来。
    warn_if_clamped("get_price", start_date)
    _warn_beyond_coverage(end_date)
    
    fields, has_dominant_id = _ensure_fields(fields, DAYBAR_FIELDS, stocks, funds, futures, futures888, spots, options, convertibles, indexes, repos)
    #start_date = convert_dateteime_to_timestamp(start_date)
    #end_date = convert_dateteime_to_timestamp(end_date)
    #pdb.set_trace()
    frame = get_client().get_price(order_book_ids=order_book_ids,
                                           start_date=start_date,
                                           end_date=end_date,
                                           frequency=frequency, 
                                           fields=fields, 
                                           skip_suspended=skip_suspended, 
                                           include_now=include_now,
                                           adjust_type=adjust_type, 
                                           adjust_orig=adjust_orig)
    return _to_panel(frame)


def _to_panel(frame):
    """把 daybar 的扁平列还原成本函数文档里承诺的形状。

    本接口对外一直是 ``(order_book_id, datetime)`` 的 MultiIndex，而上游给身份的方式
    **两个市场不一样**：

    * CN 按 ``exchange_id`` + ``trading_code`` 两列组织（daybar artifact 的
      KEY_COLUMNS），``600000`` + ``XSHG`` 在这里拼成 ``600000.XSHG``；
    * US 不带这两列 —— ticker 全国唯一、转板不改身份，所以那边直接给整的
      ``order_book_id``（服务端把 artifact 的 ``symbol`` 改名而来），已经是 ``AAPL.US``。

    只认 CN 那一套的后果不是报错，是 ``market="us"`` 悄悄走进下面的降级分支，于是
    同一个函数对 CN 返回 MultiIndex、对 US 返回扁平表。调用方拿到的形状取决于查的是
    哪个市场，而文档只承诺了一种。
    """
    if frame is None or not isinstance(frame, pd.DataFrame) or frame.empty:
        return frame
    if "session_date" not in frame.columns:
        # 服务端换了形状——原样返回，让调用方看见真实的列，而不是在这里猜。
        return frame
    parts = {"exchange_id", "trading_code"}
    if parts.issubset(frame.columns):
        frame = frame.copy()
        frame["order_book_id"] = (
            frame["trading_code"].astype(str) + "." + frame["exchange_id"].astype(str)
        )
        frame = frame.drop(columns=["exchange_id", "trading_code"])
    elif "order_book_id" in frame.columns:
        frame = frame.copy()
    else:
        return frame
    frame["datetime"] = pd.to_datetime(frame["session_date"])
    frame = frame.drop(columns=["session_date"])
    return frame.set_index(["order_book_id", "datetime"]).sort_index()