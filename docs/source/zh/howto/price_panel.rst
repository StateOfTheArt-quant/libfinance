==========================
取最近 N 个交易日的行情
==========================

**目标**\ ：拿到一批股票最近 10 个交易日的行情面板。

听起来是一行代码的事，但直觉写法会失败。这篇把正确写法和它为什么正确讲清楚。

直觉写法为什么不行
==================

..  code-block:: python

    # 不要这样写
    import datetime
    end = datetime.date.today().isoformat()
    start = (datetime.date.today() - datetime.timedelta(days=10)).isoformat()
    df = get_price(["600000.XSHG"], start, end)

两个错误：

1. **``end`` 用了今天。** 行情只到最后一个已收盘交易日，今天的数据还没有。
   服务端会拒绝整个区间——不是返回少几天，是直接报错。
2. **往前减 10 个自然日不等于 10 个交易日。** 中间夹着周末和假期，实际只能拿到
   6 到 7 天。

正确写法
========

..  code-block:: python

    from libfinance import get_price, get_price_coverage, get_n_trading_dates_until

    # 1. 先问行情更新到哪一天（不同交易所可能不同，取最保守的）
    end = min(v["end"] for v in get_price_coverage().values())

    # 2. 从那天往前数 10 个交易日
    sessions = get_n_trading_dates_until(end, 10)

    # 3. 用交易日的两端做区间
    df = get_price(["000001.XSHE", "600000.XSHG"],
                   sessions[0].strftime("%Y-%m-%d"),
                   sessions[-1].strftime("%Y-%m-%d"))

运行结果：

..  code-block:: text

    >>> end
    '2026-09-18'
    >>> sessions[0].date(), sessions[-1].date(), len(sessions)
    (datetime.date(2026, 9, 7), datetime.date(2026, 9, 18), 10)
    >>> df.shape
    (20, 8)

每一步在做什么
==============

..  list-table::
    :header-rows: 1
    :widths: 30 70

    *   - 步骤
        - 为什么需要
    *   - ``get_price_coverage()``
        - 问出行情的真实上界。它返回的 ``end`` 已经把复权因子的 cutoff 考虑进去了，
          直接拿来当 ``end_date`` 是安全的
    *   - ``min(...)``
        - 不同交易所覆盖可能不一致，取最小值保证两边都有数据
    *   - ``get_n_trading_dates_until``
        - 按交易日往前数，自动跳过周末和假期

怎么确认结果对
==============

..  list-table::
    :header-rows: 1
    :widths: 36 64

    *   - 检查
        - 预期
    *   - ``len(sessions)``
        - 正好等于你要的 N
    *   - ``df.index.get_level_values("datetime").nunique()``
        - 等于 N（除非某只票期间停牌且你开了 ``skip_suspended``\ ）
    *   - ``df.index.get_level_values("order_book_id").nunique()``
        - 等于你传入的股票数；少了说明有代码没被解析出来，回头看警告

处理停牌
========

默认保留停牌日（成交量为 0），这样每只票的日期轴一致，适合做面板对齐。
要剔除：

..  code-block:: python

    df = get_price(ids, start, end, skip_suspended=True)

这时不同股票的行数可能不一样，后续做矩阵运算前记得 ``unstack`` 对齐。

要真实成交价
============

上面拿到的是\ **前复权价**\ 。要历史上真实的成交价：

..  code-block:: python

    df = get_price(ids, start, end, adjust_type="none")

区别有多大、什么时候该用哪个，见 :doc:`../data/price`\ 。
