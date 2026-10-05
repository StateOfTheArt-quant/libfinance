========
交易日历
========

交易日历是所有日期类查询的参照系：先知道哪些天开市，才能判断"某天没有数据"是因为
停牌、还是因为那天根本不交易。

..  code-block:: python

    >>> from libfinance import get_trading_dates
    >>> get_trading_dates("2024-05-11", "2024-05-20")
    DatetimeIndex(['2024-05-13', '2024-05-14', '2024-05-15', '2024-05-16',
                   '2024-05-17', '2024-05-20'],
                  dtype='datetime64[ns]', freq=None)

区间两端按自然日给，返回的只有交易日；5 月 11、12 日是周末，18、19 日也是。

常用操作
========

..  list-table::
    :header-rows: 1
    :widths: 46 54

    *   - 要做的事
        - 函数
    *   - 取区间内的交易日
        - :func:`~libfinance.get_trading_dates`
    *   - 判断某天是不是交易日
        - :func:`~libfinance.is_trading_date`
    *   - 往前推 N 个交易日
        - :func:`~libfinance.get_previous_trading_date`
    *   - 往后推 N 个交易日
        - :func:`~libfinance.get_next_trading_date`
    *   - 截至某天（含）的最后 N 个交易日
        - :func:`~libfinance.get_n_trading_dates_until`
    *   - 数区间内有几个交易日
        - :func:`~libfinance.count_trading_dates`
    *   - 取全部交易日
        - :func:`~libfinance.get_all_trading_dates`

..  code-block:: python

    >>> from libfinance import (get_previous_trading_date, is_trading_date,
    ...                         count_trading_dates, get_n_trading_dates_until)
    >>> get_previous_trading_date("2020-05-18", n=3)
    Timestamp('2020-05-13 00:00:00')
    >>> is_trading_date("2024-05-01")           # 劳动节
    False
    >>> count_trading_dates("2024-01-01", "2024-12-31")
    242
    >>> get_n_trading_dates_until("2024-03-11", 5)
    DatetimeIndex(['2024-03-05', '2024-03-06', '2024-03-07', '2024-03-08',
                   '2024-03-11'], dtype='datetime64[ns]', freq=None)

美股
====

同一套函数，加 ``market="us"``\ ：

..  code-block:: python

    >>> get_trading_dates("2024-01-01", "2024-01-10", market="us")

不传 ``market`` 就是 A 股。

..  _calendar-coverage:

日历覆盖到哪一天
================

日历不是无限长的。它有一个明确的\ **确认区间**\ ：

..  code-block:: python

    >>> from libfinance import get_calendar_coverage
    >>> get_calendar_coverage()
    {'history_start': Timestamp('1990-12-19 00:00:00'),
     'confirmed_through': Timestamp('2026-12-31 00:00:00')}

``confirmed_through`` 是"已经确认到哪一天"。交易所会提前公布下一年的休市安排，所以
这个日期通常在\ **未来**——上面这个服务已经确认到年底。

问到区间之外会报错：

..  code-block:: python

    >>> get_trading_dates("2027-01-01", "2027-01-10")
    CalendarCoverageError: cn 的查询 2027-01-01 超出 release 确认范围
                           1990-12-19..2026-12-31

..  admonition:: 为什么是报错，不是返回空
    :class: important

    因为\ **"没人公布过那一天"和"那一天不交易"是两回事**\ 。

    如果这里返回一个空结果，你的代码会照常往下跑，只是少了几天——而且没有任何迹象
    告诉你少了。回测里这种静默缺失极难发现。报错则强迫你当场处理。

    同样的道理，往前 / 往后推 N 个交易日时，如果推到了区间外，也会报错而不是返回
    区间端点。返回端点等于给了一个\ **错误答案**\ ：你要的是"往前第 3 个"，拿到的却是
    "最早的那个"，而两者长得一模一样。

..  warning::

    **日历确认到某天 ≠ 那天有行情。** 日历能到 2026-12-31，行情只到最后一个已收盘
    交易日。这是两个不同的上界，混淆它们是最常见的错误来源——见 :doc:`freshness`\ 。
