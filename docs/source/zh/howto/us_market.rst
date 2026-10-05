==============
查美股
==============

**目标**\ ：知道美股能取到什么、和 A 股的写法有什么不同、哪些数据只有一个市场有。

三条差异
========

1. **代码后缀是** ``.US``\ ，如 ``AAPL.US``\ 、\ ``NVDA.US``\ 、指数 ``SPX.US``\ 。
2. **不涉及具体证券的查询要传** ``market="us"``\ ：交易日历、全市场目录、行情覆盖范围。
3. **按证券查询不用传 market**\ ——代码后缀已经说明了市场，一个列表里可以混合 A 股与美股。

..  code-block:: python

    import libfinance as lf

    lf.get_trading_dates("2024-01-01", "2024-01-31", market="us")   # 要 market
    lf.all_instruments(market="us")                                 # 要 market
    lf.get_price(["AAPL.US", "600000.XSHG"], "2026-03-02", "2026-03-06")   # 不用

哪些数据有美股
==============

..  list-table::
    :header-rows: 1
    :widths: 40 12 48

    *   - 接口
        - 美股
        - 说明
    *   - 日历函数（\ :func:`~libfinance.get_trading_dates` 等）
        - ✅
        - 传 ``market="us"``
    *   - :func:`~libfinance.all_instruments` / :func:`~libfinance.instruments`
        - ✅
        - 股票、指数、行业（GICS、ICB、NAICS、SIC）；主题目录只有 A 股
    *   - :func:`~libfinance.get_price` / :func:`~libfinance.get_price_coverage`
        - ✅
        - 股票与指数；\ ``turnover``\ 、\ ``limit_up``\ 、\ ``limit_down`` 为 ``NaN``\ （见下）
    *   - :func:`~libfinance.get_ex_factor`
        - ✅
        -
    *   - :func:`~libfinance.get_dividends` / :func:`~libfinance.get_splits`
        - ✅
        -
    *   - :func:`~libfinance.get_spinoffs`
        - ✅
        - **只有美股**\ ；传 A 股代码会明确报错
    *   - :func:`~libfinance.get_allotments`
        - ❌
        - **只有 A 股**\ （配股）；传美股代码会明确报错
    *   - :func:`~libfinance.get_shares`
        - ✅
        - 与 A 股同一套字段，见 :doc:`../data/fundamentals`
    *   - :func:`~libfinance.get_pit_financials_ex` / :func:`~libfinance.get_financial_metrics`
        - ✅
        - 与 A 股同一套字段、同一套公式
    *   - 行业：\ :func:`~libfinance.get_instrument_industry` 等
        - ✅
        - 分类体系是 GICS、ICB、NAICS、SIC（\ ``source="GICS"``\ ）
    *   - 指数：\ :func:`~libfinance.get_instrument_indices` 等
        - ✅
        - 如 ``SPX.US``
    *   - 主题：\ :func:`~libfinance.get_instrument_themes` 等
        - ❌
        - 主题目录（同花顺 THS）只有 A 股；美股代码返回空表

只有一个市场有的数据，传另一个市场的代码会\ **明确报错**\ ，说明这类数据发布在哪个市场——
不会返回空表冒充"没有事件"：

..  code-block:: text

    RpcError(code=2001): ['AAPL.US'] are ['US'] securities; allotments are published for ['CN'] only

而在支持的市场里查不到事件（比如苹果没有分拆）返回的是空表——\ **这是"没有事件"**\ 。两者含义不同，别混淆。

行情里的三个空列
================

美股的 ``get_price`` 与 A 股返回同样的列，但 ``turnover``\ 、\ ``limit_up``\ 、\ ``limit_down`` 都是 ``NaN``\ ：
美股没有涨跌停限制，成交额也没有提供。需要成交金额时只能用 ``close * volume`` 估算。
带实际输出的例子见 :doc:`../reference/price`\ 。

数据更新到哪一天
================

美股和 A 股的覆盖上界是\ **分开**\ 的。\ ``get_price_coverage(market="us")`` 按证券类型给出：
股票在 ``stock`` 下（键为 ``US``\ ），指数在 ``index`` 下（按交易所）。取最近的交易日窗口时以对应的
``end`` 为终点，不要直接把今天当上界，见 :doc:`../data/freshness`\ 。

名称是英文全称
==============

美股证券的 ``name`` 是带证券类别的英文全称（如 ``Apple Inc. - Common Stock``\ ），不是交易代码——交易代码在
``order_book_id`` 里（去掉 ``.US`` 后缀）。

字段含义见 :doc:`../data/corporate_actions`\ 。
