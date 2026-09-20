==========================
无前视偏差地取财务数据
==========================

**目标**\ ：在回测里取财务数据，保证每个时点用的都是"那天真的能看到"的数字。

一句话做法：\ **每次查询都带上当前回测日期作为** ``as_of``\ 。

看看不带会差多少
================

取三只股票 2023 年年报的净利润，分别站在 2024-06-30 和今天看：

..  code-block:: python

    from libfinance import get_pit_financials_ex

    codes = ["000001.XSHE", "000016.XSHE", "600000.XSHG"]

    # 回测日能看到的
    past = get_pit_financials_ex(codes, ["net_profit"], "2023q4", "2023q4",
                                 as_of="2024-06-30")
    # 今天能看到的（不传 as_of）
    now = get_pit_financials_ex(codes, ["net_profit"], "2023q4", "2023q4")

..  code-block:: text

    >>> past
                           info_date    net_profit  if_adjusted
    order_book_id quarter
    000001.XSHE   2023q4  2024-04-20  4.645500e+10            1
    000016.XSHE   2023q4  2024-04-29 -2.635887e+09            1
    600000.XSHG   2023q4  2024-04-30  3.742900e+10            1

    >>> now
                           info_date    net_profit  if_adjusted
    order_book_id quarter
    000001.XSHE   2023q4  2026-03-21  4.645500e+10            1
    000016.XSHE   2023q4  2026-04-29 -2.730376e+09            1
    600000.XSHG   2023q4  2026-03-31  3.742900e+10            1

    >>> now["net_profit"] - past["net_profit"]
    000001.XSHE  2023q4            0.00
    000016.XSHE  2023q4    -94489273.48        <- 差了 9448 万
    600000.XSHG  2023q4            0.00

三只票里有一只被修订了，亏损多了 9448 万元。注意 ``info_date``\ ：不传 ``as_of``
拿到的那一版是 **2026 年**\ 才发布的。

一个真实的回测里有几百上千只股票、几十个季度，这种修订不会是个例。

正确的取数流程
==============

..  code-block:: python

    from libfinance import (get_trading_dates, get_index_weights,
                            get_pit_financials_ex, get_price)

    for d in get_trading_dates("2024-01-01", "2024-06-30"):
        day = d.strftime("%Y-%m-%d")

        # 1. 那一天的股票池（也要按那一天取）
        pool = get_index_weights(index_code="000300.XSHG", date=day)
        codes = list(pool["order_book_id"])

        # 2. 那一天能看到的财务数据
        fin = get_pit_financials_ex(codes, ["net_profit"], "2023q1", "2023q4",
                                    as_of=day)

        # 3. 行情（行情不会被修订，不需要 as_of）
        px = get_price(codes, day, day)

        ...   # 你的策略逻辑

哪些数据需要 ``as_of``
======================

..  list-table::
    :header-rows: 1
    :widths: 36 16 48

    *   - 数据
        - 需要吗
        - 原因
    *   - :func:`~libfinance.get_pit_financials_ex`
        - **需要**
        - 财报会被追溯修订
    *   - :func:`~libfinance.get_factor`
        - **需要**
        - 基于财报算出来的
    *   - :func:`~libfinance.get_dividends` 等公司行动
        - **需要**
        - 事件会被修订或撤销
    *   - :func:`~libfinance.get_concept_weights`
        - **需要**
        - 成分会调整
    *   - :func:`~libfinance.get_price`
        - 不需要
        - 行情定了就不再变
    *   - :func:`~libfinance.get_trading_dates`
        - 不需要
        - 日历是事实

对 :func:`~libfinance.get_index_weights` 与 :func:`~libfinance.get_instrument_industry`
用的是 ``date``\ ，含义是"那一天的成分/分类"，效果相同。

怎么确认自己做对了
==================

..  list-table::
    :header-rows: 1
    :widths: 40 60

    *   - 检查
        - 预期
    *   - 返回值的 ``info_date`` 列
        - 每一行都 ``<=`` 你传的 ``as_of``
    *   - 换一个更晚的 ``as_of`` 重跑
        - 有些数字会变——**变了才说明 as_of 真的生效了**
    *   - 回测收益率异常地好
        - 先怀疑前视偏差，再怀疑策略

..  tip::

    最省事的自检：把整个回测的 ``as_of`` 去掉再跑一遍。如果结果明显变好，说明原来
    的版本确实挡住了未来信息；如果毫无变化，检查一下 ``as_of`` 是不是根本没传进去。

查看修订历史
============

想知道某个数字被改过几次：

..  code-block:: python

    >>> get_pit_financials_ex("000016.XSHE", ["net_profit"], "2023q4", "2023q4",
    ...                       statements="all")
      order_book_id quarter  info_date    net_profit  if_adjusted
    0   000016.XSHE  2023q4 2024-04-02 -2.635887e+09            0
    1   000016.XSHE  2023q4 2024-04-29 -2.635887e+09            1
    2   000016.XSHE  2023q4 2024-08-31 -2.635887e+09            1
    3   000016.XSHE  2023q4 2024-10-31 -2.635887e+09            1
    4   000016.XSHE  2023q4 2025-04-15 -2.635887e+09            1
    5   000016.XSHE  2023q4 2026-04-29 -2.730376e+09            1

``if_adjusted`` 为 ``0`` 的是原始披露值。更多说明见 :doc:`../data/point_in_time`\ 。
