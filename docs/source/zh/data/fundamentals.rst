=================
财务数据与股本
=================

财务数据按\ **季度\ **\ 取，股本按\ **交易日**\ 取。这一章讲它们的口径与单位。

财务报表：\ :func:`~libfinance.get_pit_financials_ex`
=====================================================

..  code-block:: python

    >>> from libfinance import get_pit_financials_ex
    >>> get_pit_financials_ex("600000.XSHG", ["net_profit"], "2024q1", "2024q4")
                           info_date    net_profit  if_adjusted
    order_book_id quarter
    600000.XSHG   2024q1  2025-04-30  1.766000e+10            1
                  2024q2  2026-08-28  2.732400e+10            1
                  2024q3  2025-10-31  3.568700e+10            1
                  2024q4  2026-08-28  4.583500e+10            1

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

    注意上面 2024q1 那一行的 ``info_date`` 是 **2025-04-30**——它是一年后的修订版，
    不是 2024 年 4 月首次披露的那一版。不传 ``as_of`` 拿到的就是这个。

财务因子：\ :func:`~libfinance.get_factor`
==========================================

在报表科目之上算好的衍生指标，同样按季度：

..  code-block:: python

    >>> from libfinance import get_factor
    >>> get_factor("600000.XSHG", ["net_profit_ttm"], "2024q1", "2025q1")
                           net_profit_ttm
    order_book_id quarter
    600000.XSHG   2024q1     1.072960e+11
                  2024q2     1.110050e+11
                  2024q3     1.181000e+11
                  2024q4     1.265060e+11
                  2025q1     1.266220e+11

``as_of`` 的含义与 :func:`~libfinance.get_pit_financials_ex` 完全一致。

可用的因子名由服务端提供，不同部署可能不同；传一个不存在的因子名会被明确拒绝，
而不是返回空列。

股本：\ :func:`~libfinance.get_shares`
======================================

和财务数据不同，股本给的是\ **逐交易日的面板**——股本变动是稀疏事件，但这里把它展开到
每个交易日，方便直接和行情对齐：

..  code-block:: python

    >>> from libfinance import get_shares
    >>> get_shares("600000.XSHG", start_date="2024-01-01", end_date="2024-01-05")

..  code-block:: text

                              circulation_a free_circulation non_circulation_a  \
    order_book_id date
    600000.XSHG   2024-01-02  29352176396.0    10802151287.0               0.0
                  2024-01-03  29352176396.0    10802151287.0               0.0
                  2024-01-04  29352176848.0    10802151287.0               0.0
                  2024-01-05  29352176848.0    10802151287.0               0.0

                             preferred_shares          total        total_a
    order_book_id date
    600000.XSHG   2024-01-02              0.0  29352176396.0  29352176396.0
    ...

字段与单位
----------

..  list-table::
    :header-rows: 1
    :widths: 26 74

    *   - 字段
        - 含义
    *   - ``total``
        - 总股本
    *   - ``total_a``
        - A 股总股本
    *   - ``circulation_a``
        - A 股流通股本
    *   - ``non_circulation_a``
        - A 股非流通股本
    *   - ``free_circulation``
        - 自由流通股本（剔除限售、控股股东持股等）
    *   - ``preferred_shares``
        - 优先股

..  important::

    **所有股本字段的单位都是"股"**\ ，不是"万股"，也不是"亿股"。

    算市值就是 ``股本 × 股价``\ 。注意股价要用\ **不复权**\ 的价格
    （\ ``adjust_type="none"``\ ）——复权价和当前股本不在同一个尺度上。

省略 ``start_date`` / ``end_date`` 会返回从首个股本事件到最后一个事件的全部历史，
数据量不小，建议按需要指定区间。

只要某几个字段时：

..  code-block:: python

    >>> get_shares(["000001.XSHE", "600000.XSHG"],
    ...            start_date="2024-01-01", end_date="2024-06-30",
    ...            fields=["total", "circulation_a"])
