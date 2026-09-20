================
数据更新到哪一天
================

这一章回答一个具体问题：\ **"我想取最近 10 个交易日的行情"，为什么会失败？**

先看现象：

..  code-block:: python

    >>> import datetime
    >>> today = datetime.date.today().isoformat()      # '2026-09-19'
    >>> get_price(["600000.XSHG"], "2026-09-01", today)
    UserWarning: get_price: end_date=2026-09-19 超出行情覆盖（最新已收盘交易日
                 2026-09-18）...
    RpcError: XSHG query 2026-09-01..2026-09-19 is outside coverage
              2000-01-04..2026-09-18; a date this release does not reach is not
              a date with no trading

三个不同的上界
==============

"最近 10 天"之所以出错，是因为它默认了一件不成立的事：\ **今天有数据**\ 。实际上这里至少
有三个互不相同的上界。

..  list-table::
    :header-rows: 1
    :widths: 22 20 58

    *   - 上界
        - 典型位置
        - 它是什么
    *   - 日历确认到
        - **未来**\ （年底）
        - 交易所提前公布的休市安排，所以日历能排到明年
    *   - 行情覆盖到
        - 昨天 / 前天
        - 最后一个\ **已收盘并完成入库**\ 的交易日
    *   - 复权因子到
        - 可能更早
        - 除权因子需要公司行动落地才能算出来

于是就有了那个反直觉的结论：

..  admonition:: 日历上有这一天，不代表行情有这一天
    :class: important

    日历说 2026-12-31 是确认过的，行情却只到 2026-09-18。两者回答的不是同一个问题：
    日历回答"那天开不开市"，行情回答"那天的数据到没到"。

    服务端拒绝越界查询时那句话说的就是这件事——*a date this release does not reach
    is not a date with no trading*。它拒绝把"数据还没到"伪装成"那天没交易"，
    因为后者会让你悄悄少几天数据而毫无察觉。

怎么问出上界
============

..  code-block:: python

    >>> from libfinance import get_price_coverage
    >>> get_price_coverage()
    {'XSHE': {'start': '2000-01-04', 'end': '2026-09-18',
              'raw_end': '2026-09-18', 'adjust_cutoff': '2026-09-18'},
     'XSHG': {'start': '2000-01-04', 'end': '2026-09-18',
              'raw_end': '2026-09-18', 'adjust_cutoff': '2026-09-18'}}

..  list-table::
    :header-rows: 1
    :widths: 22 78

    *   - 键
        - 含义
    *   - ``start``
        - 最早有行情的日期
    *   - ``end``
        - **复权价**\ 能查到的最后一天。默认 ``adjust_type="pre"`` 要用除权因子，
          所以这里已经把 ``raw_end`` 和 ``adjust_cutoff`` 取了较小值——**直接用它
          当 end_date 就是安全的**
    *   - ``raw_end``
        - 未复权价能查到的最后一天
    *   - ``adjust_cutoff``
        - 除权因子算到哪一天

美股传 ``market="us"``\ ：

..  code-block:: python

    >>> get_price_coverage(market="us")
    {'US': {'start': None, 'end': '2026-08-21',
            'raw_end': None, 'adjust_cutoff': '2026-08-21'}}

美股的上游产物按月分片，没有日级的上界，所以 ``raw_end`` 是 ``None``——这里\ **不会**
从月份编一个日期出来充数。复权价的上界用除权因子的 cutoff，它是日级且权威的。

日历的覆盖另外问
================

:func:`~libfinance.get_calendar_coverage` 回答的是日历那一条：

..  code-block:: python

    >>> from libfinance import get_calendar_coverage
    >>> get_calendar_coverage()
    {'history_start': Timestamp('1990-12-19 00:00:00'),
     'confirmed_through': Timestamp('2026-12-31 00:00:00')}

正确的写法
==========

把"最近 N 个交易日"翻译成代码，要先问上界，再往前数交易日——而不是从今天往前数
自然日：

..  code-block:: python

    from libfinance import get_price, get_price_coverage, get_n_trading_dates_until

    end = min(v["end"] for v in get_price_coverage().values())
    sessions = get_n_trading_dates_until(end, 10)

    df = get_price(["600000.XSHG"],
                   sessions[0].strftime("%Y-%m-%d"),
                   sessions[-1].strftime("%Y-%m-%d"))

两个细节：

* 用 ``min(...)`` 是因为不同交易所的覆盖可能不一样，取最保守的那个；
* 用 :func:`~libfinance.get_n_trading_dates_until` 而不是 ``end - 10 天``——
  中间的周末和假期不算交易日。

完整的可运行版本见 :doc:`../howto/price_panel`\ 。

..  tip::

    **可迁移的判断方法**\ ：任何时候你在代码里写下"今天"或 ``datetime.now()`` 作为数据
    查询的右端点，先停一下问自己——这个数据集更新到今天了吗？多数历史数据集的答案是
    否定的。
