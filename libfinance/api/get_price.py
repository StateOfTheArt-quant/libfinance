#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from typing import List, Union
import datetime

import pandas as pd
import json
import warnings
import pdb

from libfinance.client import get_client
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

DAYBAR_FIELDS = {
    "future": ["settlement", "prev_settlement", "open_interest", "limit_up", "limit_down",
               "day_session_open"],
    "common": ["open", "close", "high", "low", "total_turnover", "volume", "prev_close"],
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

def classify_order_book_ids(order_book_ids):
    ins_list = ensure_instruments(order_book_ids)
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
def get_price(
    order_book_ids: list,
    start_date: str,
    end_date: str,
    frequency: str="1d",
    fields: List[str]=None,
    skip_suspended: bool=True,
    include_now: bool=True,
    adjust_type: str="none",
    adjust_orig:datetime.datetime = None) -> pd.DataFrame:
    """获取指定合约的历史 k 线行情，支持任意日频率xd(1d,5d)和任意分钟频率xm(1m,3m,5m,15m)的历史数据。
    
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
    
    
    order_book_ids, stocks, funds, indexes, futures, futures888, spots, options, convertibles, repos = classify_order_book_ids(order_book_ids)
    if not order_book_ids:
        warnings.warn("no valid instrument")
        return
    
    start_date, end_date = _ensure_date(
        start_date, end_date, stocks, funds, indexes, futures, spots, options, convertibles, repos
    )
    
    fields, has_dominant_id = _ensure_fields(fields, DAYBAR_FIELDS, stocks, funds, futures, futures888, spots, options, convertibles, indexes, repos)
    #start_date = convert_dateteime_to_timestamp(start_date)
    #end_date = convert_dateteime_to_timestamp(end_date)
    #pdb.set_trace()
    return get_client().get_price(order_book_ids=order_book_ids,
                                           start_date=start_date,
                                           end_date=end_date,
                                           frequency=frequency, 
                                           fields=fields, 
                                           skip_suspended=skip_suspended, 
                                           include_now=include_now,
                                           adjust_type=adjust_type, 
                                           adjust_orig=adjust_orig)