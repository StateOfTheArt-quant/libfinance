#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import bisect
import datetime
import pandas as pd

from libfinance.client import get_client
from libfinance.utils.decorators import export_as_api, ttl_cache, compatible_with_parm

def _to_timestamp(d):
    return pd.Timestamp(d).replace(hour=0, minute=0, second=0, microsecond=0)

@ttl_cache(24 * 3600)
def _get_all_trading_dates():
    return get_client().get_trading_calendar()

@export_as_api
def get_trading_dates(start_date, end_date):
    r"""get the trading datata
    
    获取A股某个区间的交易日期
    
    :param start_date: 开始日期
    :param end_date: 结束如期
    
    Example::

        获取2020-05-10至2020-05-20之间的交易日期

    ..  code-block:: python3
    
        from libfinance import get_trading_dates

     
        >>> trading_dates = get_trading_dates(start_date = "2020-05-11", end_date="2020-05-20")
        >>> print(trading_dates)
        DatetimeIndex(['2020-05-11', '2020-05-12', '2020-05-13', '2020-05-14',
           '2020-05-15', '2020-05-18', '2020-05-19', '2020-05-20'],
          dtype='datetime64[ns]', freq=None)
    """
    trading_dates = _get_all_trading_dates()
    
    start_date = _to_timestamp(start_date)
    end_date = _to_timestamp(end_date)
    left = trading_dates.searchsorted(start_date)
    right = trading_dates.searchsorted(end_date, side='right')
    return trading_dates[left:right]

@export_as_api
def get_previous_trading_date(date, n=1):
    """获取指定日期的之前的第 n 个交易日
    
    :param date: 指定日期
    :param n: 第 n 个交易日
    
    Example::
       
        2020-05-18之前3天的交易日
    
    ..  code-block:: python3
    
        from libfinance import get_previous_trading_date
        
        >>> get_previous_trading_date(date='2020-05-18', n=3)
        Timestamp('2020-05-13 00:00:00')
    """    
    trading_dates = _get_all_trading_dates()
    pos = trading_dates.searchsorted(_to_timestamp(date))
    if pos >= n:
        return trading_dates[pos - n]
    else:
        return trading_dates[0]

@export_as_api
def get_next_trading_date(date, n=1):
    """
    获取指定日期之后的第 n 个交易日
    
    :param date: 指定日期
    :param n: 第 n 个交易日
        
    :example:
    
    ..  code-block:: python3
    
        from libfinance import get_next_trading_date
    
        >>> get_next_trading_date(date='2020-05-13', n=3)
        Timestamp('2020-05-18 00:00:00')
    """    
    trading_dates = _get_all_trading_dates()
    pos = trading_dates.searchsorted(_to_timestamp(date), side='right')
    if pos + n > len(trading_dates):
        return trading_dates[-1]
    else:
        return trading_dates[pos + n - 1]

@export_as_api
def is_trading_date(date):
    date = _to_timestamp(date)
    trading_dates = _get_all_trading_dates()
    pos = trading_dates.searchsorted(date)
    return pos < len(trading_dates) and trading_dates[pos] == date

@export_as_api
def get_n_trading_dates_until(date, n):
    trading_dates = _get_all_trading_dates()
    pos = trading_dates.searchsorted(_to_timestamp(date), side='right')
    if pos >= n:
        return trading_dates[pos - n:pos]
    return trading_dates[:pos]

@export_as_api
def count_trading_dates(start_date, end_date):
    start_date = _to_timestamp(start_date)
    end_date = _to_timestamp(end_date)
    trading_dates = _get_all_trading_dates()
    return trading_dates.searchsorted(end_date, side='right') - trading_dates.searchsorted(start_date)


if __name__ == "__main__":
    start_date = "2024-01-01"
    end_date = "2024-02-27"
    
    trading_dates = get_trading_dates(start_date, end_date)
    
    


