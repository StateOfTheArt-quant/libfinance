#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import List, Union
import datetime

import pandas as pd
from libfinance.client import get_client
from libfinance.utils.decorators import export_as_api, ttl_cache, compatible_with_parm
from libfinance.utils.datetime_func import convert_dateteime_to_timestamp

@export_as_api
def history_bars(
    order_book_ids: list,
    bar_count: int,
    frequency: str,
    datetime: str,
    fields: List[str]=None,
    skip_suspended: bool=True,
    include_now: bool=True,
    adjust_type: str="none",
    adjust_orig:datetime.datetime = None) -> pd.DataFrame:
    """获取指定合约的历史 k 线行情，支持任意日频率xd(1d,5d)和任意分钟频率xm(1m,3m,5m,15m)的历史数据。
    
    :param order_book_ids: 多个标的合约代码
    :param bar_count: 获取的历史数据数量，必填项
    :param frequency: 获取数据什么样的频率进行。'1d'或'1m'分别表示每日和每分钟，必填项
    :param fields: 返回数据字段。必填项。见下方列表。
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
    
        获取中国平安和万科 2020-04-20之前10天的交易数据
    
    ..  code-block:: python3
        
        import pandas as pd
        from simons.api import history_bars
    
        # 
        >>> dt = pd.Timestamp("2020-04-20")
        >>> fields=["datetime","open","high","low","close","volume"]
        >>> data = history_bars(order_book_ids=["000001.XSHE", "000002.XSHE"], datatime=dt, bar_count=10, frequency="1d", fields=fields)
        >>> print(data)
        
                                       open   high    low  close     volume
        order_book_id datetime                                  
        000001.XSHE   2020-04-07      12.89  12.94  12.81  12.88    87031371.0
                      2020-04-08      12.88  12.92  12.72  12.78    52871614.0
                      2020-04-09      12.88  12.89  12.72  12.74    40855377.0
                      2020-04-10      12.76  12.98  12.65  12.79    66667495.0
                      2020-04-13      12.67  12.71  12.47  12.59    44621440.0
                      2020-04-14      12.65  12.86  12.57  12.86    68608687.0
                      2020-04-15      12.86  12.93  12.78  12.87    65639640.0
                      2020-04-16      12.79  12.79  12.54  12.68    78915498.0
                      2020-04-17      12.77  13.04  12.65  12.89   133116477.0
                      2020-04-20      12.86  13.05  12.77  12.99    81845583.0
        000002.XSHE   2020-04-07      27.34  27.42  26.80  27.07    67154006.0
                      2020-04-08      26.90  27.25  26.75  26.96    41251395.0
                      2020-04-09      27.10  27.16  26.60  26.69    38726254.0
                      2020-04-10      26.84  27.34  26.59  26.88    62460322.0
                      2020-04-13      26.74  27.13  26.61  27.04    43264902.0
                      2020-04-14      27.10  27.75  27.02  27.35    64241868.0
                      2020-04-15      27.20  27.23  26.55  26.70    70359257.0
                      2020-04-16      26.52  26.76  26.40  26.58    50238931.0
                      2020-04-17      26.78  27.03  26.55  26.72    83813322.0
                      2020-04-20      26.78  26.81  26.05  26.58    85012343.0
    
    """
    dt = convert_dateteime_to_timestamp(datetime)
    return get_client().multi_history_bars(order_book_ids=order_book_ids,
                                           bar_count=bar_count, 
                                           frequency=frequency, 
                                           fields=fields, 
                                           dt=dt,
                                           skip_suspended=skip_suspended, 
                                           include_now=include_now,
                                           adjust_type=adjust_type, 
                                           adjust_orig=adjust_orig)