股本结构
========================================

.. currentmodule:: libfinance

按证券代码查询时由服务端推断市场，无需 market 参数。某个市场没有对应数据能力时会报错。

所有股本字段单位均为股；总股本、流通 A 股与自由流通股本回答不同的问题。
返回表以 ``(order_book_id, date)`` 为索引。

.. list-table::
    :header-rows: 1
    :widths: 40 60

    * - 函数 / 类
      - 解决的问题
    * - :func:`~libfinance.get_shares`
      - 查询总股本、流通股本与自由流通股本的历史变化
    * - :func:`~libfinance.get_turnover_rate`
      - 查询逐交易日的换手率

get_shares — 查询总股本、流通股本与自由流通股本的历史变化
----------------------------------------------------------------------

.. autofunction:: get_shares

**示例**

.. lf-examples:: get_shares

结果解读：所有数值的单位都是股。单日查询仍保留证券与日期两层索引；可流通股本（\ ``tradable_shares``\ ）与自由流通股本（\ ``free_float_shares``\ ）含义不同。

get_turnover_rate — 查询逐交易日的换手率
----------------------------------------------------------------------

.. autofunction:: get_turnover_rate

**示例**

.. code-block:: python

    import libfinance as lf

    lf.get_turnover_rate(["600000.XSHG", "AAPL.US"], "2026-09-01", "2026-09-30")       # 两个市场同一查询
    lf.get_turnover_rate("600000.XSHG", end_date="2026-09-30")                        # 只给一个日期：那一天
    lf.get_turnover_rate(["600000.XSHG", "AAPL.US"])                                   # 都不给：各市场最近一个交易日

结果解读：

- **单位是小数**：0.0123 即 1.23%。
- **分母**：A 股使用当日生效的自由流通股本（\ ``free_float_shares``\ ），没有时用流通股本（\ ``tradable_shares``\ ）；
  美股使用当日已发行股数。这些股本来自 :func:`~libfinance.get_shares` 的底层数据。
- **分子**：未复权成交量，所以送转、拆股前后的换手率可以直接比较。
- **缺失**：停牌日没有行；没有股本数据的证券或日子为 NaN。
- **一致性**：A 股结果与 factors-daybar 中依赖换手率的因子（\ ``system/broker-daybar/TURN20``\ 、\ ``system/barra-cne5-descriptor/STOM`` 等）读取的数值同一口径。
