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

get_shares — 查询总股本、流通股本与自由流通股本的历史变化
----------------------------------------------------------------------

.. autofunction:: get_shares

**示例**

.. lf-examples:: get_shares

结果解读：所有数值的单位都是股。单日查询仍保留证券与日期两层索引；可流通股本（\ ``tradable_shares``\ ）与自由流通股本（\ ``free_float_shares``\ ）含义不同。

