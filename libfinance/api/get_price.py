#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from typing import List, Union
import datetime

import pandas as pd
import json
from libfinance.client import get_client
from libfinance.utils.decorators import export_as_api, ttl_cache, compatible_with_parm
from libfinance.utils.datetime_func import convert_dateteime_to_timestamp

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
    #start_date = convert_dateteime_to_timestamp(start_date)
    #end_date = convert_dateteime_to_timestamp(end_date)
    return get_client().get_price(order_book_ids=order_book_ids,
                                           start_date=start_date,
                                           end_date=end_date,
                                           frequency=frequency, 
                                           fields=fields, 
                                           skip_suspended=skip_suspended, 
                                           include_now=include_now,
                                           adjust_type=adjust_type, 
                                           adjust_orig=adjust_orig)