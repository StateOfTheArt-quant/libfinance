#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""交易日历。

服务端只出\ **两条原语\ **——会话集合（\ ``get_trading_calendar``）与这份集合的\ **\ 权威区间**
（\ ``get_calendar_coverage``\ ）。区间切片、前后推 n 个交易日、是否交易日、区间计数，全是
在一个有序数组上做 bisect，在这里本地算：一个场所几千个日期、几十 KB、更新极慢，拉一次
缓存一天，比每问一个日期就走一次 RPC 划算得多。

**为什么必须一起取区间。** release 有一个 ``confirmed_through``——没人发布过的日子，
任何据此推出的答案都是猜的。只拿会话集合而不校验区间，本地 bisect 会把"查询超出确认
范围"悄悄变成"那几天没有交易"，回测不会察觉自己少了几天。区间也不能用
``sessions[0]`` / ``sessions[-1]`` 顶替：端点是自然日，而最后一个会话是它之前的最后一个
**交易日**\ ，中间隔着周末与假期。

两者在 ``_calendar()`` 里\ **一次取回并一起缓存**\ ：分两次取、各自缓存，中间服务端切了一版
就会拿到一对来自不同 release 的数据——用旧区间去校验新会话，而且没有任何迹象。

``market`` 默认 ``"cn"``\ 。服务端的 calendar 命名空间同时绑了 CN 与 US，不传 market 时
它无从选路会直接报错；给个默认值让既有调用继续工作，要美股传 ``market="us"``\ 。
"""
import json

import pandas as pd

from libfinance.client import get_client
from libfinance.utils.decorators import export_as_api, ttl_cache

DEFAULT_MARKET = "cn"


class CalendarCoverageError(ValueError):
    """查询落在 release 确认过的区间之外。

    这不是"那天没有交易"——是没人发布过那一天，所以任何答案都是猜的。宁可报错，
    也不要让调用方拿到一个悄悄变短的结果。
    """


def _to_timestamp(d):
    return pd.Timestamp(d).replace(hour=0, minute=0, second=0, microsecond=0)


@ttl_cache(24 * 3600)
def _calendar(market=DEFAULT_MARKET):
    """(会话集合, 区间下界, 区间上界)。两条 RPC 一次取回，绑在同一个缓存条目上。"""
    client = get_client()
    sessions = pd.to_datetime(json.loads(client.get_trading_calendar(market=market)))
    window = client.get_calendar_coverage(market=market)
    return (
        sessions,
        _to_timestamp(window["history_start"]),
        _to_timestamp(window["confirmed_through"]),
    )


def _sessions(market, *dates):
    """取会话集合，并确认每个被问到的日期都落在 release 确认过的区间内。"""
    sessions, lower, upper = _calendar(market)
    for value in dates:
        if value < lower or value > upper:
            raise CalendarCoverageError(
                "{} 的查询 {} 超出 release 确认范围 {}..{}".format(
                    market, value.date(), lower.date(), upper.date()
                )
            )
    return sessions


@export_as_api
@ttl_cache(24 * 3600)
def get_all_trading_dates(market=DEFAULT_MARKET):
    """获取全部交易日。

    :param market: 市场，cn（默认）或 us
    """
    return _calendar(market)[0]


@export_as_api
def get_calendar_coverage(market=DEFAULT_MARKET):
    """获取日历的权威区间——本 release 确认到哪一天。

    :param market: 市场，cn（默认）或 us
    :returns: ``{"history_start": ..., "confirmed_through": ...}``

    ..  code-block:: python3

        from libfinance import get_calendar_coverage

        >>> get_calendar_coverage()
        {'history_start': Timestamp('1991-07-03 00:00:00'),
         'confirmed_through': Timestamp('2026-09-10 00:00:00')}
    """
    _, lower, upper = _calendar(market)
    return {"history_start": lower, "confirmed_through": upper}


@export_as_api
def get_trading_dates(start_date, end_date, market=DEFAULT_MARKET):
    r"""获取某个区间的交易日期

    :param start_date: 开始日期
    :param end_date: 结束日期
    :param market: 市场，cn（默认）或 us

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
    start_date, end_date = _to_timestamp(start_date), _to_timestamp(end_date)
    sessions = _sessions(market, start_date, end_date)
    left = sessions.searchsorted(start_date)
    right = sessions.searchsorted(end_date, side="right")
    return sessions[left:right]


@export_as_api
def get_previous_trading_date(date, n=1, market=DEFAULT_MARKET):
    """获取指定日期之前的第 n 个交易日

    :param date: 指定日期
    :param n: 第 n 个交易日
    :param market: 市场，cn（默认）或 us

    Example::

        2020-05-18之前3天的交易日

    ..  code-block:: python3

        from libfinance import get_previous_trading_date

        >>> get_previous_trading_date(date='2020-05-18', n=3)
        Timestamp('2020-05-13 00:00:00')
    """
    date = _to_timestamp(date)
    sessions = _sessions(market, date)
    pos = sessions.searchsorted(date)
    if pos < n:
        # 旧实现在这里返回 sessions[0]。那是个**错误答案**：调用方要的是"往前第 n 个"，
        # 拿到的却是"最早的那个"，且无从分辨。宁可报错。
        raise CalendarCoverageError(
            "{} 之前没有第 {} 个交易日；release 的第一个交易日是 {}".format(
                date.date(), n, sessions[0].date()
            )
        )
    return sessions[pos - n]


@export_as_api
def get_next_trading_date(date, n=1, market=DEFAULT_MARKET):
    """获取指定日期之后的第 n 个交易日

    :param date: 指定日期
    :param n: 第 n 个交易日
    :param market: 市场，cn（默认）或 us

    :example:

    ..  code-block:: python3

        from libfinance import get_next_trading_date

        >>> get_next_trading_date(date='2020-05-13', n=3)
        Timestamp('2020-05-18 00:00:00')
    """
    date = _to_timestamp(date)
    sessions = _sessions(market, date)
    pos = sessions.searchsorted(date, side="right")
    if pos + n > len(sessions):
        # 同上：旧实现返回 sessions[-1]，那是"日历到头了"而不是"往后第 n 个"。
        raise CalendarCoverageError(
            "{} 之后没有第 {} 个交易日；release 确认到 {}".format(
                date.date(), n, _calendar(market)[2].date()
            )
        )
    return sessions[pos + n - 1]


@export_as_api
def is_trading_date(date, market=DEFAULT_MARKET):
    """判断指定日期是否为交易日

    :param date: 指定日期
    :param market: 市场，cn（默认）或 us
    """
    date = _to_timestamp(date)
    sessions = _sessions(market, date)
    pos = sessions.searchsorted(date)
    return pos < len(sessions) and sessions[pos] == date


@export_as_api
def get_n_trading_dates_until(date, n, market=DEFAULT_MARKET):
    """获取截至指定日期（含）的最后 n 个交易日

    :param date: 指定日期
    :param n: 交易日个数
    :param market: 市场，cn（默认）或 us
    """
    date = _to_timestamp(date)
    sessions = _sessions(market, date)
    pos = sessions.searchsorted(date, side="right")
    if pos >= n:
        return sessions[pos - n:pos]
    return sessions[:pos]


@export_as_api
def count_trading_dates(start_date, end_date, market=DEFAULT_MARKET):
    """统计区间内的交易日数量

    :param start_date: 开始日期
    :param end_date: 结束日期
    :param market: 市场，cn（默认）或 us
    """
    start_date, end_date = _to_timestamp(start_date), _to_timestamp(end_date)
    sessions = _sessions(market, start_date, end_date)
    return int(
        sessions.searchsorted(end_date, side="right") - sessions.searchsorted(start_date)
    )
