==============
查美股
==============

**目标**\ ：知道美股能取到什么、和 A 股的写法有什么不同、哪些接口没有美股数据。

三条差异
========

1. **代码后缀是** ``.US``\ ，如 ``AAPL.US``\ 、\ ``NVDA.US``\ 。
2. **交易日历要传** ``market="us"``\ 。
3. **行情不用传 market**——代码后缀已经说明了市场。

..  code-block:: python

    from libfinance import get_trading_dates, all_instruments, get_price

    get_trading_dates("2024-01-01", "2024-01-31", market="us")   # 要 market
    all_instruments(type="CS", market="us")                      # 要 market
    get_price(["AAPL.US"], "2026-03-02", "2026-03-06")           # 不用

哪些数据有美股
==============

下表是在一个实际部署上逐个调用的结果。你的部署可能不同，用报错信息判断——
服务端会明确说"这个命名空间没有 us 的 provider"，不会返回空表冒充"没有数据"。

..  list-table::
    :header-rows: 1
    :widths: 34 12 54

    *   - 接口
        - 美股
        - 说明
    *   - :func:`~libfinance.get_trading_dates` 等日历函数
        - ✅
        - 传 ``market="us"``
    *   - :func:`~libfinance.all_instruments` / :func:`~libfinance.instruments`
        - ✅
        - 股票（\ ``CS``\ ）有；指数返回 0 行
    *   - :func:`~libfinance.get_price`
        - ✅
        - ``turnover`` / ``limit_up`` / ``limit_down`` 为 ``NaN``
    *   - :func:`~libfinance.get_dividends`
        - ✅
        -
    *   - :func:`~libfinance.get_splits`
        - ✅
        -
    *   - :func:`~libfinance.get_spinoffs`
        - ✅
        - **只有美股有**\ ，A 股不产生这类事件
    *   - :func:`~libfinance.get_shares`
        - ❌
        - 报 "命名空间 'shares' 没有 market='us' 的 provider"
    *   - :func:`~libfinance.get_pit_financials_ex` / :func:`~libfinance.get_factor`
        - ❌
        - 见下面的注意事项
    *   - :func:`~libfinance.get_index_weights`
        - ❌
        - 没有美股指数
    *   - :func:`~libfinance.get_instrument_industry` / :func:`~libfinance.get_industry`
        - ❌
        - 报 "unsupported A-share symbol"

..  warning::

    **财务接口对美股代码的报错不直观。** 调用
    :func:`~libfinance.get_factor` 传美股代码，得到的是：

    ..  code-block:: text

        RpcError: Array type doesn't match type of values set: string vs null

    这句话看不出"美股没有财务数据"。碰到它时不用怀疑自己的参数写法——先确认这个
    接口在你的部署上有没有美股。

美股没有涨跌停
==============

..  code-block:: python

    >>> get_price(["AAPL.US"], "2026-03-02", "2026-03-06")

..  code-block:: text

                                     low        open        high        volume  \
    order_book_id datetime
    AAPL.US       2026-03-02  259.960487  262.168453  266.284660  4.186648e+07
                  2026-03-03  259.890551  263.237468  265.315553  3.860446e+07
                  2026-03-04  261.179364  264.406391  265.905010  3.983979e+07

                              turnover  limit_up       close  limit_down
    order_book_id datetime
    AAPL.US       2026-03-02       NaN       NaN  264.476326         NaN
    ...

``turnover``\ 、\ ``limit_up``\ 、\ ``limit_down`` 都是 ``NaN``——美股没有涨跌停限制，
成交额这个部署也没有提供。算成交金额只能自己用 ``close * volume`` 估。

数据更新到哪一天
================

美股和 A 股的覆盖上界是\ **分开**\ 的：

..  code-block:: python

    >>> from libfinance import get_price_coverage
    >>> get_price_coverage(market="us")
    {'US': {'start': None, 'end': '2026-08-21',
            'raw_end': None, 'adjust_cutoff': '2026-08-21'}}

注意 ``start`` 和 ``raw_end`` 是 ``None``\ ：美股的上游数据按月分片，没有日级的上下界，
所以这里不编造一个日期出来。复权价的上界用除权因子的 cutoff，它是准确的。

名称是英文全称
==============

..  code-block:: python

    >>> from libfinance import instruments
    >>> instruments(["AAPL.US", "NVDA.US"])
    [Instrument(order_book_id='AAPL.US', symbol='Apple Inc. - Common Stock',
                type='CS', market='us'),
     Instrument(order_book_id='NVDA.US', symbol='NVIDIA Corporation - Common Stock',
                type='CS', market='us')]

``symbol`` 是带证券类型后缀的英文全称，不是交易代码——交易代码在 ``order_book_id``
里（去掉 ``.US`` 后缀）。

分拆：只有美股有
================

..  code-block:: python

    >>> from libfinance import get_spinoffs
    >>> get_spinoffs("AAPL.US", start_date="2000-01-01", end_date="2026-09-01")
    Empty DataFrame
    Columns: [order_book_id, event_id, ..., valuation_price, valuation_basis,
              valuation_source, d_spin_per_share]

苹果没有分拆事件，所以是空表——**这是"没有事件"**\ 。而对 A 股代码调用同一个函数，得到
的是"该市场未绑定"的错误，那是"这个市场没有这类数据"。两者含义不同，别混淆。

字段含义见 :doc:`../data/corporate_actions`\ 。
