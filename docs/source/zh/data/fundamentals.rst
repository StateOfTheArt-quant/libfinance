=================
财务数据与股本
=================

财务报表按\ **季度**\ 取，财务衍生指标与股本按\ **交易日**\ 取。这一章讲它们的口径与单位；
每个函数的参数与带实际输出的示例见 :doc:`../reference/financials` 与 :doc:`../reference/shares`\ 。

财务报表：\ :func:`~libfinance.get_pit_financials_ex`
=====================================================

..  code-block:: python

    import libfinance as lf

    lf.get_pit_financials_ex("600000.XSHG", ["total_operating_revenue", "net_income_parent"], "2024q1", "2024q3")

返回以 ``(order_book_id, quarter)`` 为索引的表。除了所选字段，还有两列：

- ``info_date``\ ：这一版报表的披露时间；
- ``if_adjusted``\ ：\ ``1`` 表示这一版是后来的修订（追溯调整），\ ``0`` 表示首次披露。

A 股与美股使用同一套字段名（如 ``net_income_parent``\ 、\ ``assets``\ ）。

参数：

..  list-table::
    :header-rows: 1
    :widths: 24 76

    *   - 参数
        - 说明
    *   - ``order_book_ids``
        - 单个代码或代码列表
    *   - ``fields``
        - 要哪些财务字段，必填
    *   - ``start_quarter`` / ``end_quarter``
        - 季度区间，形如 ``"2024q1"``
    *   - ``as_of``
        - 站在哪一天回头看。\ **回测里必须传**\ ，见 :doc:`point_in_time`
    *   - ``statements``
        - ``"latest"``\ （默认，每季一行）或 ``"all"``\ （全部修订版本）

..  important::

    不传 ``as_of`` 时，每个季度取的是\ **最新**\ 的一版：某个季度可能是一年后修订的版本（\ ``info_date``
    在下一年，\ ``if_adjusted`` 为 1），不是当时首次披露的那一版。\ **回测里必须传** ``as_of``\ ，见 :doc:`point_in_time`\ 。

财务衍生指标：\ :func:`~libfinance.get_financial_metrics`
=========================================================

在报表之上算好的衍生指标（如 ``roe_lf``\ 、\ ``revenue_ttm``\ 、\ ``net_profit_growth_lyr``\ 、
``debt_to_assets_lf``\ ），\ **逐交易日**\ 给出，A 股与美股同一套公式：

..  code-block:: python

    lf.get_financial_metrics("600519.XSHG", ["roe_lf", "revenue_ttm"], "2024-10-28", "2024-11-01")

每个交易日的值来自\ **那天收盘后可见的最新报告**\ ：在公告日跳变，其间保持不变。所以它本身就是
point-in-time 的，没有 ``as_of`` 参数。省略日期时取最近一个交易日。传不存在的指标名会被明确拒绝，
而不是返回空列。

股本：\ :func:`~libfinance.get_shares`
======================================

股本给的是\ **逐交易日的面板**\ ——股本变动是稀疏事件，这里展开到每个交易日，方便直接和行情对齐。
A 股与美股使用同一套字段：

..  code-block:: python

    lf.get_shares(["000001.XSHE", "600000.XSHG"], "2024-06-24", "2024-06-28",
                  fields=["issued_shares", "tradable_shares"])

字段与单位
----------

..  list-table::
    :header-rows: 1
    :widths: 26 74

    *   - 字段
        - 含义
    *   - ``issued_shares``
        - 已发行股本（总股本，公司层级）
    *   - ``tradable_shares``
        - 可流通股本（A 股为流通 A 股）
    *   - ``restricted_shares``
        - 限售（非流通）股本
    *   - ``free_float_shares``
        - 自由流通股本：剔除限售、控股股东等持股后的部分（A 股为供应商估算）
    *   - ``preferred_shares``
        - 优先股
    *   - ``shares_outstanding``
        - 流通在外股数（证券层级，美股来自 SEC 与 CRSP）；A 股的总股本\ **不**\ 当作它，所以 A 股为 ``NaN``

..  important::

    **所有股本字段的单位都是"股"**\ ，不是"万股"，也不是"亿股"。

    算市值就是 ``股本 × 股价``\ 。注意股价要用\ **不复权**\ 的价格
    （\ ``adjust_type="none"``\ ）——复权价和当前股本不在同一个尺度上。

省略 ``start_date`` / ``end_date`` 会返回全部历史，数据量不小，建议按需要指定区间与字段。
