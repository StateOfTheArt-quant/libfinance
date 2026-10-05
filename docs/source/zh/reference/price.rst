历史行情
========================================

.. currentmodule:: libfinance

按证券代码查询时由服务端推断市场，无需 market 参数。某个市场没有对应数据能力时会报错。

目前使用 ``frequency="1d"`` 查询日频数据。默认 ``adjust_type="pre"``\ ，
原始成交价格需显式传 ``"none"``\ 。详见 :doc:`../data/price`\ 。

.. list-table::
    :header-rows: 1
    :widths: 40 60

    * - 函数 / 类
      - 解决的问题
    * - :func:`~libfinance.get_price`
      - 查询日频价格与成交量，选择字段和复权口径
    * - :func:`~libfinance.get_price_coverage`
      - 确认行情更新上界，构造最近交易日窗口

get_price — 查询日频价格与成交量，选择字段和复权口径
----------------------------------------------------------------

.. autofunction:: get_price

**示例**

.. lf-examples:: get_price

结果解读：前复权默认以查询区间的最后一天为基准（\ ``adjust_orig``\ ），区间之后的除权不影响结果，所以这里前复权价与原始价相同；后复权以上市首日为基准，价格放大、成交量按同一比例缩小。

get_price_coverage — 确认行情更新上界，构造最近交易日窗口
------------------------------------------------------------------------------

.. autofunction:: get_price_coverage

**示例**

.. lf-examples:: get_price_coverage

结果解读：覆盖按证券类型与交易所给出；第二个示例以股票（XSHE）的 ``end`` 为终点回溯 5 个交易日，窗口随数据版本变化。

