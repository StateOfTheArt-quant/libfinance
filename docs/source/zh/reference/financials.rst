财务报表与因子
========================================

.. currentmodule:: libfinance

按证券代码查询时由服务端推断市场，无需 market 参数。某个市场没有对应数据能力时会报错。

季度区间决定查哪几期报告，\ ``as_of`` 决定当时已知哪些版本。
回测应设置 ``as_of``\ ；字段与因子名以所连接服务支持的目录为准。详见 :doc:`../data/fundamentals`\ 。

.. list-table::
    :header-rows: 1
    :widths: 40 60

    * - 函数 / 类
      - 解决的问题
    * - :func:`~libfinance.get_pit_financials_ex`
      - 按季度查询财报，限制披露时点并查看修订版本
    * - :func:`~libfinance.get_financial_metrics`
      - 按交易日查询财务衍生指标

get_pit_financials_ex — 按季度查询财报，限制披露时点并查看修订版本
------------------------------------------------------------------------------------------

.. autofunction:: get_pit_financials_ex

**示例**

.. lf-examples:: get_pit_financials_ex

结果解读：不传 ``as_of`` 时，2024q1 取到的是 2025 年的修订版（\ ``if_adjusted`` 为 1）；\ ``as_of="2024-11-01"`` 时每季只给当时最新的一版；\ ``statements="all"`` 把当时可见的版本都列出——2024q2 有 8 月首次披露与 10 月修订两版。

get_financial_metrics — 按交易日查询财务衍生指标
------------------------------------------------------

.. autofunction:: get_financial_metrics

**示例**

.. lf-examples:: get_financial_metrics

